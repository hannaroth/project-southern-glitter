import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from recipes import ai
from recipes.models import Recipe
from recipes.openrouter import MissingAPIKey, OpenRouterError

NOTICE = "AI unavailable, here are matching recipes"


def make(n, course="main", tags=(), title=None, ingredients=("salt", "rice")):
    return Recipe.objects.create(
        external_id=f"ext-{course}-{n}-{'-'.join(tags)}",
        title=title or f"Dish {n}",
        cuisine="Italian",
        category="Pasta",
        course=course,
        ingredients=[{"name": i, "measure": "1"} for i in ingredients],
        instructions="Cook.",
        diet_tags=list(tags),
    )


def good_reply(recipes, shopping=("rice", "salt")):
    return {
        "suggestions": [{"recipe_id": r.pk, "why": f"Because {r.pk}."} for r in recipes[:3]],
        "shopping_list": list(shopping),
    }


def call(**kwargs):
    args = {"course": "main", "theme": "Italian night", "restrictions": []}
    args.update(kwargs)
    return ai.suggest_dishes(**args)


class SuggestDishesTests(TestCase):
    def setUp(self):
        self.recipes = [make(i) for i in range(5)]

    def test_valid_reply_gives_three_ideas(self):
        picked = self.recipes[:3]
        with patch("recipes.ai.chat_json", return_value=good_reply(picked)) as chat:
            result = call()
        self.assertTrue(result.ai_used)
        self.assertEqual(result.notice, "")
        self.assertEqual([i.recipe.pk for i in result.ideas], [r.pk for r in picked])
        self.assertTrue(all(i.why for i in result.ideas))
        self.assertEqual(result.shopping_list, ["rice", "salt"])
        self.assertEqual(chat.call_count, 1)

    def test_invalid_json_shape_retried_once_then_fallback(self):
        with patch("recipes.ai.chat_json", return_value={"oops": 1}) as chat:
            result = call()
        self.assertEqual(chat.call_count, 2)
        self._assert_fallback(result)

    def test_retry_can_succeed(self):
        replies = [{"oops": 1}, good_reply(self.recipes)]
        with patch("recipes.ai.chat_json", side_effect=replies) as chat:
            result = call()
        self.assertEqual(chat.call_count, 2)
        self.assertTrue(result.ai_used)

    def test_id_outside_candidates_rejected(self):
        outsider = make(99, course="dessert")
        reply = good_reply(self.recipes)
        reply["suggestions"][0]["recipe_id"] = outsider.pk
        with patch("recipes.ai.chat_json", return_value=reply) as chat:
            result = call()
        self.assertEqual(chat.call_count, 2)
        self._assert_fallback(result)
        self.assertNotIn(outsider.pk, [i.recipe.pk for i in result.ideas])

    def test_duplicate_ids_rejected(self):
        reply = good_reply(self.recipes)
        reply["suggestions"][1]["recipe_id"] = reply["suggestions"][0]["recipe_id"]
        with patch("recipes.ai.chat_json", return_value=reply):
            self._assert_fallback(call())

    def test_wrong_count_and_bad_fields_rejected(self):
        bad = [
            {**good_reply(self.recipes), "suggestions": good_reply(self.recipes)["suggestions"][:2]},
            {**good_reply(self.recipes), "shopping_list": "rice"},
            {**good_reply(self.recipes), "shopping_list": [1, 2]},
        ]
        empty_why = good_reply(self.recipes)
        empty_why["suggestions"][0]["why"] = "  "
        bad.append(empty_why)
        for reply in bad:
            with patch("recipes.ai.chat_json", return_value=reply):
                self._assert_fallback(call())

    def test_missing_key_falls_back_without_retry(self):
        with patch("recipes.ai.chat_json", side_effect=MissingAPIKey("no key")) as chat:
            result = call()
        self.assertEqual(chat.call_count, 1)
        self._assert_fallback(result)

    def test_openrouter_error_falls_back(self):
        with patch("recipes.ai.chat_json", side_effect=OpenRouterError("timeout")):
            self._assert_fallback(call())

    def test_fewer_than_three_candidates_skips_llm(self):
        Recipe.objects.filter(pk__in=[r.pk for r in self.recipes[2:]]).delete()
        with patch("recipes.ai.chat_json") as chat:
            result = call()
        chat.assert_not_called()
        self.assertEqual(len(result.ideas), 2)
        self.assertFalse(result.ai_used)
        self.assertEqual(result.notice, NOTICE)

    def _assert_fallback(self, result):
        self.assertFalse(result.ai_used)
        self.assertEqual(result.notice, NOTICE)
        self.assertEqual(len(result.ideas), 3)
        self.assertEqual(len({i.recipe.pk for i in result.ideas}), 3)
        self.assertEqual(sorted(result.shopping_list), ["rice", "salt"])


class CandidateTests(TestCase):
    def ids(self, **kwargs):
        args = {"course": "main", "restrictions": []}
        args.update(kwargs)
        return {r.pk for r in ai.get_candidates(**args)}

    def test_respects_course(self):
        main, starter = make(1), make(1, course="starter")
        self.assertEqual(self.ids(), {main.pk})
        self.assertEqual(self.ids(course="starter"), {starter.pk})

    def test_each_restriction(self):
        plain = make(1)
        veg = make(2, tags=["vegetarian"])
        vegan = make(3, tags=["vegetarian", "vegan"])
        gluten = make(4, tags=["contains_gluten"])
        dairy = make(5, tags=["contains_dairy"])
        nuts = make(6, tags=["contains_nuts"])
        everything = {plain.pk, veg.pk, vegan.pk, gluten.pk, dairy.pk, nuts.pk}
        self.assertEqual(self.ids(), everything)
        self.assertEqual(self.ids(restrictions=["vegetarian"]), {veg.pk, vegan.pk})
        self.assertEqual(self.ids(restrictions=["vegan"]), {vegan.pk})
        self.assertEqual(self.ids(restrictions=["gluten_free"]), everything - {gluten.pk})
        self.assertEqual(self.ids(restrictions=["dairy_free"]), everything - {dairy.pk})
        self.assertEqual(self.ids(restrictions=["nut_allergy"]), everything - {nuts.pk})
        self.assertEqual(
            self.ids(restrictions=["vegetarian", "gluten_free", "dairy_free", "nut_allergy"]),
            {veg.pk, vegan.pk},
        )

    def test_unknown_keys_ignored(self):
        recipe = make(1)
        self.assertEqual(self.ids(restrictions=["kosher", "paleo"]), {recipe.pk})

    def test_exclude_ids(self):
        a, b = make(1), make(2)
        self.assertEqual(self.ids(exclude_ids=[a.pk]), {b.pk})

    def test_limit_is_twenty(self):
        for i in range(25):
            make(i)
        self.assertEqual(len(ai.get_candidates("main", [])), 20)


class PromptTests(TestCase):
    def setUp(self):
        self.recipes = [make(i, title=f"Dish {i}", ingredients=("pasta", "basil")) for i in range(4)]

    def messages_sent(self, **kwargs):
        with patch("recipes.ai.chat_json", return_value=good_reply(self.recipes)) as chat:
            call(**kwargs)
        return chat.call_args.args[0]

    def user_data(self, **kwargs):
        return json.loads(self.messages_sent(**kwargs)[1]["content"])

    def test_wish_trimmed_to_200_characters(self):
        data = self.user_data(wish="x" * 500)
        self.assertEqual(data["wish"], "x" * 200)

    def test_prompt_content(self):
        data = self.user_data(restrictions=["dairy_free"], wish="  no oven ")
        self.assertEqual(data["course"], "main")
        self.assertEqual(data["theme"], "Italian night")
        self.assertEqual(data["restrictions"], ["dairy_free"])
        self.assertEqual(data["wish"], "no oven")
        self.assertEqual(
            set(data["candidates"][0]), {"id", "title", "cuisine", "category", "ingredients"}
        )
        self.assertEqual(data["candidates"][0]["ingredients"], ["pasta", "basil"])

    def test_no_personal_data_in_prompt(self):
        User = get_user_model()
        user = User.objects.create_user(
            email="ada@example.com", password="x"
        )
        other = User.objects.create_user(
            email="bob@example.com", password="x"
        )
        address = "12 Fake Street, New Haven"
        messages = self.messages_sent(restrictions=["gluten_free", "nut_allergy"], wish="something spicy")
        text = json.dumps(messages)
        for secret in (user.email, other.email, address, "Fake Street"):
            self.assertNotIn(secret, text)
        self.assertNotIn("@", text)


class UnexpectedErrorTests(TestCase):
    def test_unexpected_exception_falls_back_and_logs_without_message(self):
        recipes = [make(i) for i in range(4)]
        with patch("recipes.ai.chat_json", side_effect=RuntimeError("secret-token-123")):
            with self.assertLogs("recipes.ai", level="ERROR") as logs:
                result = call()
        self.assertFalse(result.ai_used)
        self.assertEqual(result.notice, NOTICE)
        self.assertEqual(len(result.ideas), 3)
        self.assertIn("RuntimeError", logs.output[0])
        self.assertNotIn("secret-token-123", "".join(logs.output))
        self.assertTrue(recipes)
