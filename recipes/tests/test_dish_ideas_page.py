from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from recipes.diet import ALLERGY_NOTE
from recipes.models import Recipe
from recipes.openrouter import InvalidJSONReply, MissingAPIKey
from teams.models import Team
from teams.tests.helpers import make_dinner, make_user

NOTICE = "AI unavailable, here are matching recipes"


def make_recipe(n, course="main", tags=()):
    return Recipe.objects.create(
        external_id=f"ext-{course}-{n}",
        title=f"Dish {course} {n}",
        cuisine="Italian",
        category="Pasta",
        course=course,
        ingredients=[{"name": f"ingredient{n}", "measure": "1"}],
        instructions="Cook.",
        source_url=f"https://example.com/r/{n}",
        diet_tags=list(tags),
    )


def reply_for(recipes, why="Tasty."):
    return {
        "suggestions": [{"recipe_id": r.pk, "why": why} for r in recipes[:3]],
        "shopping_list": ["rice", "salt"],
    }


def make_team(dinner, creator, partner=None, **kw):
    return Team.objects.create(
        dinner=dinner,
        creator=creator,
        partner=partner,
        address=kw.pop("address", "12 Secret Lane"),
        **kw,
    )


class PageTestBase(TestCase):
    def setUp(self):
        self.dinner = make_dinner(theme="Mediterranean")
        self.creator = make_user("creator@example.com")
        self.partner = make_user("partner@example.com")
        self.team = make_team(
            self.dinner, self.creator, self.partner, preferred_course="main",
            dietary_restrictions=["vegetarian"],
        )
        self.url = reverse("recipes:dish_ideas", kwargs={"pk": self.dinner.pk})
        self.recipes = [make_recipe(i, tags=["vegetarian"]) for i in range(5)]

    def login(self, user=None):
        self.client.force_login(user or self.creator)


class PermissionTests(PageTestBase):
    def test_url(self):
        self.assertEqual(self.url, f"/dinners/{self.dinner.pk}/dish-ideas/")

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_non_member_forbidden(self):
        self.login(make_user("other@example.com"))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_admin_non_member_forbidden(self):
        self.login(make_user("boss@example.com", is_staff=True))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_cancelled_team_member_forbidden(self):
        self.team.status = Team.Status.CANCELLED
        self.team.save()
        self.login()
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_creator_and_partner_allowed(self):
        for user in (self.creator, self.partner):
            self.login(user)
            self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_unknown_dinner_404(self):
        self.login()
        response = self.client.get(reverse("recipes:dish_ideas", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)

    def test_post_by_non_member_forbidden_and_no_llm_call(self):
        self.login(make_user("other@example.com"))
        with patch("recipes.ai.chat_json") as chat:
            response = self.client.post(self.url, {"suggest": "1"})
        self.assertEqual(response.status_code, 403)
        chat.assert_not_called()


class ResultsTests(PageTestBase):
    def test_get_shows_context_and_restrictions(self):
        self.login()
        response = self.client.get(self.url)
        self.assertContains(response, "Test Feast")
        self.assertContains(response, "Mediterranean")
        self.assertContains(response, "Vegetarian")
        self.assertContains(response, "Suggest dishes")
        self.assertNotContains(response, "Suggest others")

    def test_post_shows_three_recipes_and_shopping_list(self):
        self.login()
        with patch("recipes.ai.chat_json", return_value=reply_for(self.recipes, "Great pick.")) as chat:
            response = self.client.post(self.url, {"suggest": "1", "wish": "no oven"})
        chat.assert_called_once()
        self.assertEqual(response.status_code, 200)
        for recipe in self.recipes[:3]:
            self.assertContains(response, recipe.title)
            self.assertContains(response, recipe.source_url)
        self.assertContains(response, "Great pick.")
        self.assertContains(response, "Italian")
        self.assertContains(response, "rice")
        self.assertContains(response, "Recipes from TheMealDB")
        self.assertContains(response, ALLERGY_NOTE)
        self.assertContains(response, "Vegetarian")
        self.assertContains(response, "Suggest others")
        self.assertNotContains(response, NOTICE)

    def test_llm_html_is_escaped_and_why_truncated(self):
        self.login()
        why = "<script>alert(1)</script>" + "x" * 500
        with patch("recipes.ai.chat_json", return_value=reply_for(self.recipes, why)):
            response = self.client.post(self.url, {"suggest": "1"})
        self.assertNotContains(response, "<script>alert(1)")
        self.assertContains(response, "&lt;script&gt;alert(1)")
        self.assertNotContains(response, "x" * 301)

    def test_shopping_list_capped_and_escaped(self):
        self.login()
        reply = reply_for(self.recipes)
        reply["shopping_list"] = ["<b>item</b>"] + [f"item{i}" for i in range(100)]
        with patch("recipes.ai.chat_json", return_value=reply):
            response = self.client.post(self.url, {"suggest": "1"})
        self.assertContains(response, "&lt;b&gt;item&lt;/b&gt;")
        self.assertContains(response, "item38")
        self.assertNotContains(response, "item39")

    def test_non_http_source_url_not_linked(self):
        Recipe.objects.update(source_url="javascript:alert(1)")
        self.login()
        with patch("recipes.ai.chat_json", return_value=reply_for(self.recipes)):
            response = self.client.post(self.url, {"suggest": "1"})
        self.assertNotContains(response, "javascript:")


class RestrictionTests(PageTestBase):
    def test_union_over_active_teams_only(self):
        make_team(self.dinner, make_user("a@example.com"), dietary_restrictions=["nut_allergy", "bogus"])
        make_team(
            self.dinner, make_user("b@example.com"), dietary_restrictions=["vegan"],
            status=Team.Status.CANCELLED,
        )
        other = make_dinner(title="Other")
        make_team(other, make_user("c@example.com"), dietary_restrictions=["dairy_free"])
        self.login()
        import recipes.views as views

        with patch.object(views, "suggest_dishes", wraps=views.suggest_dishes) as spy:
            with patch("recipes.ai.chat_json", return_value=reply_for(self.recipes)):
                response = self.client.post(self.url, {"suggest": "1"})
        self.assertEqual(spy.call_args.kwargs["restrictions"], ["vegetarian", "nut_allergy"])
        self.assertContains(response, "Nut allergy")
        self.assertNotContains(response, "Vegan")
        self.assertNotContains(response, "Dairy-free")

    def test_none_when_empty(self):
        self.team.dietary_restrictions = []
        self.team.save()
        self.login()
        self.assertContains(self.client.get(self.url), "None")


class CourseTests(PageTestBase):
    def test_fixed_course_used_without_picker(self):
        self.team.preferred_course = "dessert"
        self.team.save()
        desserts = [make_recipe(i, course="dessert", tags=["vegetarian"]) for i in range(4)]
        self.login()
        self.assertNotContains(self.client.get(self.url), 'name="course"')
        with patch("recipes.ai.chat_json", return_value=reply_for(desserts)) as chat:
            response = self.client.post(self.url, {"suggest": "1", "course": "starter"})
        chat.assert_called_once()
        self.assertContains(response, desserts[0].title)

    def test_no_preference_requires_valid_course(self):
        self.team.preferred_course = "no_preference"
        self.team.save()
        self.login()
        self.assertContains(self.client.get(self.url), 'name="course"')
        for bad in ({}, {"course": "no_preference"}, {"course": "brunch"}):
            with patch("recipes.ai.chat_json") as chat:
                response = self.client.post(self.url, {"suggest": "1", **bad})
            chat.assert_not_called()
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, "Three ideas")
            self.assertContains(response, "alert")

    def test_no_preference_with_valid_course(self):
        self.team.preferred_course = "no_preference"
        self.team.save()
        self.login()
        with patch("recipes.ai.chat_json", return_value=reply_for(self.recipes)):
            response = self.client.post(self.url, {"suggest": "1", "course": "main"})
        self.assertContains(response, self.recipes[0].title)


class SuggestOthersTests(PageTestBase):
    def test_shown_ids_are_excluded_and_accumulate(self):
        self.recipes += [make_recipe(i, tags=["vegetarian"]) for i in range(5, 10)]
        self.login()
        import recipes.views as views

        with patch.object(views, "suggest_dishes", wraps=views.suggest_dishes) as spy:
            with patch("recipes.ai.chat_json", side_effect=lambda m: reply_for(
                [r for r in self.recipes if r.pk not in spy.call_args.kwargs["exclude_ids"]]
            )):
                first = self.client.post(self.url, {"suggest": "1"})
                shown = first.context["form"]["shown_ids"].value()
                self.assertEqual(spy.call_args.kwargs["exclude_ids"], [])
                second = self.client.post(self.url, {"others": "1", "shown_ids": shown})
        ids = [int(i) for i in shown.split(",")]
        self.assertEqual(len(ids), 3)
        self.assertEqual(spy.call_args.kwargs["exclude_ids"], ids)
        shown2 = second.context["form"]["shown_ids"].value()
        self.assertEqual(len(shown2.split(",")), 6)

    def test_garbage_ids_ignored_and_capped(self):
        self.login()
        import recipes.views as views

        junk = "abc,,-5,1.5,7;8, 12 ,99999999999999999999,<b>," + ",".join(str(i) for i in range(1000, 1100))
        with patch.object(views, "suggest_dishes", wraps=views.suggest_dishes) as spy:
            with patch("recipes.ai.chat_json", return_value=reply_for(self.recipes)):
                response = self.client.post(self.url, {"others": "1", "shown_ids": junk})
        self.assertEqual(response.status_code, 200)
        excluded = spy.call_args.kwargs["exclude_ids"]
        self.assertEqual(excluded[0], 12)
        self.assertEqual(len(excluded), 60)
        self.assertTrue(all(isinstance(i, int) and i > 0 for i in excluded))


class FallbackTests(PageTestBase):
    def test_missing_api_key(self):
        self.login()
        with patch.dict("os.environ", {}, clear=False) as env:
            env.pop("OPENROUTER_API_KEY", None)
            response = self.client.post(self.url, {"suggest": "1"})
        self.assertContains(response, NOTICE)
        self.assertContains(response, "Three ideas")

    def test_chat_json_raises(self):
        self.login()
        with patch("recipes.ai.chat_json", side_effect=MissingAPIKey("no key")):
            response = self.client.post(self.url, {"suggest": "1"})
        self.assertContains(response, NOTICE)

    def test_invalid_json_retried_then_fallback(self):
        self.login()
        with patch("recipes.ai.chat_json", side_effect=InvalidJSONReply("bad")) as chat:
            response = self.client.post(self.url, {"suggest": "1"})
        self.assertEqual(chat.call_count, 2)
        self.assertContains(response, NOTICE)

    def test_unexpected_error_no_500(self):
        self.login()
        with patch("recipes.ai.chat_json", side_effect=ValueError("boom")):
            response = self.client.post(self.url, {"suggest": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, NOTICE)

    def test_no_matching_recipes_message(self):
        Recipe.objects.all().delete()
        self.login()
        response = self.client.post(self.url, {"suggest": "1"})
        self.assertContains(response, "No matching recipes")


class NoPersonalDataTests(PageTestBase):
    def test_prompt_has_no_personal_data(self):
        other_user = make_user("someone-else@example.com")
        make_team(self.dinner, other_user, address="99 Hidden Road", dietary_notes="allergic to kiwi")
        self.team.dietary_notes = "my private note about shellfish"
        self.team.address = "12 Secret Lane"
        self.team.save()
        self.login()
        with patch("recipes.ai.chat_json", return_value=reply_for(self.recipes)) as chat:
            self.client.post(self.url, {"suggest": "1", "wish": "something spicy"})
        chat.assert_called_once()
        sent = str(chat.call_args)
        for secret in (
            "12 Secret Lane", "99 Hidden Road", "kiwi", "shellfish",
            "creator@example.com", "partner@example.com", "someone-else@example.com",
            "example.com", self.creator.display_name, self.partner.display_name,
        ):
            self.assertNotIn(secret, sent)
        self.assertIn("Mediterranean", sent)
        self.assertIn("something spicy", sent)


class TeamPageLinkTests(PageTestBase):
    def test_link_for_active_team(self):
        self.login()
        response = self.client.get(reverse("teams:detail", kwargs={"pk": self.team.pk}))
        self.assertContains(response, "Get dish ideas")
        self.assertContains(response, self.url)

    def test_no_link_for_cancelled_team(self):
        self.team.status = Team.Status.CANCELLED
        self.team.save()
        self.login()
        response = self.client.get(reverse("teams:detail", kwargs={"pk": self.team.pk}))
        self.assertNotContains(response, "Get dish ideas")

    def test_no_link_for_admin_who_is_not_a_member(self):
        admin = make_user("boss2@example.com", is_staff=True)
        self.login(admin)
        response = self.client.get(reverse("teams:detail", kwargs={"pk": self.team.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Get dish ideas")

    def test_link_for_partner(self):
        self.login(self.partner)
        response = self.client.get(reverse("teams:detail", kwargs={"pk": self.team.pk}))
        self.assertContains(response, "Get dish ideas")


class FewCandidatesNoticeTests(PageTestBase):
    def test_few_candidates_show_own_notice_and_skip_ai(self):
        Recipe.objects.exclude(pk__in=[r.pk for r in self.recipes[:2]]).delete()
        self.login()
        with patch("recipes.ai.chat_json") as chat:
            response = self.client.post(self.url, {"suggest": "1"})
        chat.assert_not_called()
        self.assertContains(response, "Only a few recipes match")
        self.assertNotContains(response, NOTICE)

    def test_zero_candidates_no_ai_unavailable(self):
        Recipe.objects.all().delete()
        self.login()
        with patch("recipes.ai.chat_json") as chat:
            response = self.client.post(self.url, {"suggest": "1"})
        chat.assert_not_called()
        self.assertContains(response, "No matching recipes found")
        self.assertNotContains(response, NOTICE)


class VeganNoticeTests(PageTestBase):
    def setUp(self):
        super().setUp()
        self.team.dietary_restrictions = ["vegan"]
        self.team.preferred_course = "starter"
        self.team.save()
        for i in range(5):
            make_recipe(i + 20, course="starter", tags=["vegetarian"])

    def test_vegan_starter_host_sees_explanation(self):
        self.login()
        with patch("recipes.ai.chat_json") as chat:
            response = self.client.post(self.url, {"suggest": "1"})
        chat.assert_not_called()
        self.assertContains(response, "No matching recipes found for these restrictions.")
        self.assertContains(response, "marks vegan dishes only among main courses")

    def test_vegan_main_host_gets_no_extra_line(self):
        self.team.preferred_course = "main"
        self.team.save()
        Recipe.objects.all().delete()
        self.login()
        response = self.client.post(self.url, {"suggest": "1"})
        self.assertContains(response, "No matching recipes found")
        self.assertNotContains(response, "marks vegan dishes only")
