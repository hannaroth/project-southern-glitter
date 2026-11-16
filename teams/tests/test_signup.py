"""Issue #26: the sign-up form, one team per person per dinner, the deadline, and the team page."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from teams.models import Team
from teams.services import active_team_for, can_see_address, signups_open

from .helpers import make_dinner, make_user

VALID = {
    "address": "12 Elm St, New Haven, CT",
    "dietary_restrictions": ["vegetarian", "nut_allergy"],
    "dietary_notes": "No cilantro",
    "preferred_course": "main",
}


class SignupsOpenTests(TestCase):
    def test_open_before_the_deadline(self):
        self.assertTrue(signups_open(make_dinner(deadline_in=timedelta(minutes=1))))

    def test_closed_after_the_deadline(self):
        self.assertFalse(signups_open(make_dinner(deadline_in=-timedelta(minutes=1))))

    def test_closed_exactly_at_the_deadline(self):
        dinner = make_dinner()
        with patch("teams.services.timezone.now", return_value=dinner.signup_deadline):
            self.assertFalse(signups_open(dinner))


class SignupFormTests(TestCase):
    def setUp(self):
        self.dinner = make_dinner()
        self.url = reverse("teams:signup", args=[self.dinner.pk])
        self.ann = make_user("ann@example.com", first_name="Ann")
        self.client.force_login(self.ann)

    def test_url(self):
        self.assertEqual(self.url, f"/dinners/{self.dinner.pk}/signup/")

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/login/?next={self.url}", fetch_redirect_response=False)
        self.client.post(self.url, VALID)
        self.assertEqual(Team.objects.count(), 0)

    def test_unknown_dinner_is_404(self):
        self.assertEqual(self.client.get(reverse("teams:signup", args=[9999])).status_code, 404)

    def test_form_shows_all_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for text in [
            "Test Feast", 'name="address"', "Vegetarian", "Vegan", "Gluten-free", "Dairy-free",
            "Nut allergy", 'name="dietary_notes"', "Starter", "Main", "Dessert", "No preference",
        ]:
            self.assertContains(response, text)

    def test_valid_signup_creates_a_registered_team(self):
        response = self.client.post(self.url, VALID)
        team = Team.objects.get()
        self.assertRedirects(response, reverse("teams:detail", args=[team.pk]))
        self.assertEqual(team.dinner, self.dinner)
        self.assertEqual(team.creator, self.ann)
        self.assertIsNone(team.partner)
        self.assertEqual(team.status, Team.Status.REGISTERED)
        self.assertEqual(team.address, "12 Elm St, New Haven, CT")
        self.assertEqual(team.dietary_restrictions, ["vegetarian", "nut_allergy"])
        self.assertEqual(team.dietary_notes, "No cilantro")
        self.assertEqual(team.preferred_course, Team.Course.MAIN)

    def test_new_teams_are_registered_even_past_the_team_cap(self):
        # Until the waitlist (#28) lands, every new team is REGISTERED.
        dinner = make_dinner("Small Feast", team_cap=1)
        Team.objects.create(dinner=dinner, creator=make_user("bo@example.com"), address="x")
        self.client.post(reverse("teams:signup", args=[dinner.pk]), VALID)
        self.assertEqual(Team.objects.get(creator=self.ann).status, Team.Status.REGISTERED)

    def test_dietary_fields_optional_and_course_defaults(self):
        self.client.post(self.url, {"address": "1 Elm St", "preferred_course": "no_preference"})
        team = Team.objects.get()
        self.assertEqual(team.dietary_restrictions, [])
        self.assertEqual(team.preferred_course, Team.Course.NO_PREFERENCE)

    def test_address_required(self):
        for address in ["", "   "]:
            response = self.client.post(self.url, {**VALID, "address": address})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors["address"])
        self.assertEqual(Team.objects.count(), 0)

    def test_unknown_diet_or_course_rejected(self):
        response = self.client.post(self.url, {**VALID, "dietary_restrictions": ["paleo"]})
        self.assertTrue(response.context["form"].errors["dietary_restrictions"])
        response = self.client.post(self.url, {**VALID, "preferred_course": "brunch"})
        self.assertTrue(response.context["form"].errors["preferred_course"])
        self.assertEqual(Team.objects.count(), 0)

    def test_client_cannot_set_status_partner_or_token(self):
        bo = make_user("bo@example.com")
        self.client.post(
            self.url,
            {**VALID, "status": "waitlisted", "partner": bo.pk, "invite_token": "chosen", "creator": bo.pk},
        )
        team = Team.objects.get()
        self.assertEqual(team.status, Team.Status.REGISTERED)
        self.assertIsNone(team.partner)
        self.assertEqual(team.creator, self.ann)
        self.assertNotEqual(team.invite_token, "chosen")


class DeadlineTests(TestCase):
    def setUp(self):
        self.dinner = make_dinner(deadline_in=-timedelta(hours=1))
        self.url = reverse("teams:signup", args=[self.dinner.pk])
        self.client.force_login(make_user("ann@example.com"))

    def test_form_hidden_after_the_deadline(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign-ups for this dinner are closed.")
        self.assertNotContains(response, 'name="address"')

    def test_post_refused_after_the_deadline(self):
        response = self.client.post(self.url, VALID)
        self.assertContains(response, "Sign-ups for this dinner are closed.")
        self.assertEqual(Team.objects.count(), 0)

    def test_deadline_passing_between_get_and_post(self):
        dinner = make_dinner("Edge Feast")
        with patch("teams.services.timezone.now", return_value=dinner.signup_deadline + timedelta(seconds=1)):
            self.client.post(reverse("teams:signup", args=[dinner.pk]), VALID)
        self.assertEqual(Team.objects.count(), 0)


class OneTeamPerPersonTests(TestCase):
    def setUp(self):
        self.dinner = make_dinner()
        self.url = reverse("teams:signup", args=[self.dinner.pk])
        self.ann = make_user("ann@example.com")
        self.bo = make_user("bo@example.com")

    def test_creator_cannot_sign_up_twice(self):
        self.client.force_login(self.ann)
        self.client.post(self.url, VALID)
        first = Team.objects.get()
        response = self.client.post(self.url, {**VALID, "address": "Elsewhere"})
        self.assertRedirects(response, reverse("teams:detail", args=[first.pk]))
        self.assertEqual(Team.objects.count(), 1)
        # The form itself sends them to their team.
        self.assertRedirects(self.client.get(self.url), reverse("teams:detail", args=[first.pk]))

    def test_partner_cannot_sign_up_another_team(self):
        team = Team.objects.create(dinner=self.dinner, creator=self.ann, partner=self.bo, address="x")
        self.client.force_login(self.bo)
        response = self.client.post(self.url, VALID)
        self.assertRedirects(response, reverse("teams:detail", args=[team.pk]))
        self.assertEqual(Team.objects.count(), 1)

    def test_waitlisted_team_also_counts(self):
        Team.objects.create(dinner=self.dinner, creator=self.ann, address="x", status=Team.Status.WAITLISTED)
        self.client.force_login(self.ann)
        self.client.post(self.url, VALID)
        self.assertEqual(Team.objects.count(), 1)

    def test_cancelled_team_does_not_block(self):
        Team.objects.create(
            dinner=self.dinner, creator=self.ann, address="x",
            status=Team.Status.CANCELLED, cancelled_at=timezone.now(),
        )
        self.client.force_login(self.ann)
        self.client.post(self.url, VALID)
        self.assertEqual(Team.objects.exclude(status=Team.Status.CANCELLED).count(), 1)

    def test_a_team_for_another_dinner_does_not_block(self):
        Team.objects.create(dinner=make_dinner("Other Feast"), creator=self.ann, address="x")
        self.client.force_login(self.ann)
        self.client.post(self.url, VALID)
        self.assertEqual(Team.objects.filter(dinner=self.dinner, creator=self.ann).count(), 1)

    def test_active_team_for(self):
        team = Team.objects.create(dinner=self.dinner, creator=self.ann, partner=self.bo, address="x")
        self.assertEqual(active_team_for(self.ann, self.dinner), team)
        self.assertEqual(active_team_for(self.bo, self.dinner), team)
        self.assertIsNone(active_team_for(make_user("cy@example.com"), self.dinner))
        self.assertIsNone(active_team_for(self.ann, make_dinner("Other Feast")))
        team.status = Team.Status.CANCELLED
        team.save()
        self.assertIsNone(active_team_for(self.ann, self.dinner))


class TeamPageTests(TestCase):
    def setUp(self):
        self.dinner = make_dinner()
        self.ann = make_user("ann@example.com", first_name="Ann")
        self.bo = make_user("bo@example.com", first_name="Bo")
        self.team = Team.objects.create(
            dinner=self.dinner, creator=self.ann, partner=self.bo, address="12 Secret Lane",
            dietary_restrictions=["vegan"], dietary_notes="No cilantro", preferred_course="dessert",
        )
        self.url = reverse("teams:detail", args=[self.team.pk])

    def test_url(self):
        self.assertEqual(self.url, f"/teams/{self.team.pk}/")

    def test_members_see_the_team_and_address(self):
        for user in (self.ann, self.bo):
            self.client.force_login(user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            for text in ["Test Feast", "Registered", "Ann", "Bo", "12 Secret Lane", "Vegan", "No cilantro", "Dessert"]:
                self.assertContains(response, text)

    def test_admin_sees_the_address(self):
        self.client.force_login(make_user("admin@example.com", is_staff=True))
        self.assertContains(self.client.get(self.url), "12 Secret Lane")

    def test_other_participant_cannot_see_it(self):
        self.client.force_login(make_user("cy@example.com"))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, "12 Secret Lane", status_code=404)

    def test_logged_out_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/login/?next={self.url}", fetch_redirect_response=False)

    def test_incomplete_team_says_partner_not_joined(self):
        team = Team.objects.create(dinner=make_dinner("Other"), creator=self.ann, address="x")
        self.client.force_login(self.ann)
        self.assertContains(self.client.get(reverse("teams:detail", args=[team.pk])), "Not joined yet")

    def test_can_see_address(self):
        cy = make_user("cy@example.com")
        admin = make_user("admin@example.com", is_staff=True)
        self.assertTrue(can_see_address(self.ann, self.team))
        self.assertTrue(can_see_address(self.bo, self.team))
        self.assertTrue(can_see_address(admin, self.team))
        self.assertFalse(can_see_address(cy, self.team))

    def test_address_not_on_public_pages(self):
        self.assertNotContains(self.client.get("/"), "12 Secret Lane")


class TeamAdminTests(TestCase):
    def test_team_listed_in_admin(self):
        Team.objects.create(dinner=make_dinner(), creator=make_user("ann@example.com"), address="x")
        self.client.force_login(make_user("admin@example.com", is_staff=True, is_superuser=True))
        response = self.client.get("/admin/teams/team/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ann@example.com")
        self.assertContains(response, "Registered")

    def test_participant_cannot_open_team_admin(self):
        self.client.force_login(make_user("ann@example.com"))
        response = self.client.get("/admin/teams/team/")
        self.assertEqual(response.status_code, 302)
