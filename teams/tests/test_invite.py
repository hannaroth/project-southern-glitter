"""Issue #27: the partner invite link on the team page, and accepting it."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from teams.models import Team
from teams.services import accept_refusal

from .helpers import make_dinner, make_user


class InviteLinkOnTeamPageTests(TestCase):
    def setUp(self):
        self.dinner = make_dinner()
        self.ann = make_user("ann@example.com", first_name="Ann")
        self.team = Team.objects.create(dinner=self.dinner, creator=self.ann, address="x")
        self.url = reverse("teams:detail", args=[self.team.pk])
        self.accept_path = reverse("teams:accept", args=[self.team.invite_token])

    def test_creator_sees_full_invite_link_and_copy_button(self):
        self.client.force_login(self.ann)
        response = self.client.get(self.url)
        self.assertContains(response, f"http://testserver{self.accept_path}")
        self.assertContains(response, "Copy link")
        self.assertContains(response, "navigator.clipboard")

    def test_link_hidden_once_the_partner_joined(self):
        self.team.partner = make_user("bo@example.com")
        self.team.save()
        self.client.force_login(self.ann)
        response = self.client.get(self.url)
        self.assertNotContains(response, self.team.invite_token)
        self.assertNotContains(response, "Copy link")

    def test_partner_never_sees_the_link(self):
        bo = make_user("bo@example.com")
        self.team.partner = bo
        self.team.save()
        self.client.force_login(bo)
        self.assertNotContains(self.client.get(self.url), self.team.invite_token)

    def test_admin_does_not_see_the_link(self):
        self.client.force_login(make_user("admin@example.com", is_staff=True))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.team.invite_token)

    def test_link_hidden_for_a_cancelled_team(self):
        self.team.status = Team.Status.CANCELLED
        self.team.cancelled_at = timezone.now()
        self.team.save()
        self.client.force_login(self.ann)
        self.assertNotContains(self.client.get(self.url), self.team.invite_token)

    def test_after_the_deadline_the_page_says_the_invite_no_longer_works(self):
        team = Team.objects.create(
            dinner=make_dinner("Past Feast", deadline_in=-timedelta(hours=1)), creator=self.ann, address="x"
        )
        self.client.force_login(self.ann)
        response = self.client.get(reverse("teams:detail", args=[team.pk]))
        self.assertContains(response, "can no longer accept the invite")
        self.assertNotContains(response, team.invite_token)

    def test_each_team_has_its_own_token(self):
        other = Team.objects.create(dinner=make_dinner("Other"), creator=self.ann, address="x")
        self.assertNotEqual(self.team.invite_token, other.invite_token)
        self.assertGreaterEqual(len(self.team.invite_token), 40)


class AcceptInviteTests(TestCase):
    def setUp(self):
        self.dinner = make_dinner()
        self.ann = make_user("ann@example.com", first_name="Ann")
        self.bo = make_user("bo@example.com", first_name="Bo")
        self.team = Team.objects.create(dinner=self.dinner, creator=self.ann, address="12 Secret Lane")
        self.url = reverse("teams:accept", args=[self.team.invite_token])

    def test_url(self):
        self.assertEqual(self.url, f"/teams/join/{self.team.invite_token}/")

    def test_logged_out_visitor_goes_to_login_and_comes_back(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/login/?next={self.url}", fetch_redirect_response=False)
        response = self.client.post(
            "/login/", {"username": "bo@example.com", "password": "pw-12345-xyz", "next": self.url}
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)

    def test_logged_out_post_does_not_accept(self):
        self.client.post(self.url)
        self.team.refresh_from_db()
        self.assertIsNone(self.team.partner)

    def test_unknown_token_is_404(self):
        self.client.force_login(self.bo)
        self.assertEqual(self.client.get(reverse("teams:accept", args=["nope"])).status_code, 404)
        self.assertEqual(self.client.post(reverse("teams:accept", args=["nope"])).status_code, 404)

    def test_get_shows_the_invite_without_accepting_or_revealing_the_address(self):
        self.client.force_login(self.bo)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Feast")
        self.assertContains(response, "Join Ann's team")
        self.assertNotContains(response, "12 Secret Lane")
        self.team.refresh_from_db()
        self.assertIsNone(self.team.partner)

    def test_accepting_sets_the_partner(self):
        self.client.force_login(self.bo)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("teams:detail", args=[self.team.pk]))
        self.team.refresh_from_db()
        self.assertEqual(self.team.partner, self.bo)
        self.assertTrue(self.team.is_complete)
        self.assertEqual(self.team.status, Team.Status.REGISTERED)
        page = self.client.get(reverse("teams:detail", args=[self.team.pk]))
        self.assertContains(page, "12 Secret Lane")

    def test_accepting_keeps_a_waitlisted_team_waitlisted(self):
        self.team.status = Team.Status.WAITLISTED
        self.team.save()
        self.client.force_login(self.bo)
        self.client.post(self.url)
        self.team.refresh_from_db()
        self.assertEqual(self.team.partner, self.bo)
        self.assertEqual(self.team.status, Team.Status.WAITLISTED)

    def test_partner_opening_the_link_again_goes_to_the_team(self):
        self.team.partner = self.bo
        self.team.save()
        self.client.force_login(self.bo)
        self.assertRedirects(self.client.get(self.url), reverse("teams:detail", args=[self.team.pk]))


class AcceptRefusalTests(TestCase):
    """Each refusal shows a clear message on GET and changes nothing on POST."""

    def setUp(self):
        self.dinner = make_dinner()
        self.ann = make_user("ann@example.com", first_name="Ann")
        self.bo = make_user("bo@example.com", first_name="Bo")
        self.team = Team.objects.create(dinner=self.dinner, creator=self.ann, address="x")
        self.url = reverse("teams:accept", args=[self.team.invite_token])

    def assertRefused(self, user, message, team=None):
        team = team or self.team
        url = reverse("teams:accept", args=[team.invite_token])
        partner_before = team.partner_id
        self.client.force_login(user)
        for response in (self.client.get(url), self.client.post(url)):
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, message)
            self.assertNotContains(response, '<button type="submit">Join')
        team.refresh_from_db()
        self.assertEqual(team.partner_id, partner_before)

    def test_after_the_deadline(self):
        team = Team.objects.create(
            dinner=make_dinner("Past Feast", deadline_in=-timedelta(minutes=1)), creator=self.ann, address="x"
        )
        self.assertRefused(self.bo, "Sign-ups for this dinner are closed.", team)

    def test_deadline_passing_between_get_and_post(self):
        self.client.force_login(self.bo)
        self.assertContains(self.client.get(self.url), "Join Ann's team")
        with patch("teams.services.timezone.now", return_value=self.dinner.signup_deadline):
            response = self.client.post(self.url)
        self.assertContains(response, "Sign-ups for this dinner are closed.")
        self.team.refresh_from_db()
        self.assertIsNone(self.team.partner)

    def test_your_own_invite(self):
        self.assertRefused(self.ann, "This is your own team&#x27;s invite link.")

    def test_team_already_has_a_partner(self):
        self.team.partner = self.bo
        self.team.save()
        self.assertRefused(make_user("cy@example.com"), "This team already has a partner.")

    def test_already_creator_of_another_team_for_the_dinner(self):
        own = Team.objects.create(dinner=self.dinner, creator=self.bo, address="y")
        self.assertRefused(self.bo, "You already have a team for this dinner")
        self.assertContains(self.client.get(self.url), reverse("teams:detail", args=[own.pk]))

    def test_already_partner_of_another_team_for_the_dinner(self):
        Team.objects.create(dinner=self.dinner, creator=make_user("cy@example.com"), partner=self.bo, address="y")
        self.assertRefused(self.bo, "You already have a team for this dinner")

    def test_waitlisted_team_also_counts(self):
        Team.objects.create(dinner=self.dinner, creator=self.bo, address="y", status=Team.Status.WAITLISTED)
        self.assertRefused(self.bo, "You already have a team for this dinner")

    def test_cancelled_team_for_the_dinner_does_not_block(self):
        Team.objects.create(
            dinner=self.dinner, creator=self.bo, address="y",
            status=Team.Status.CANCELLED, cancelled_at=timezone.now(),
        )
        self.client.force_login(self.bo)
        self.client.post(self.url)
        self.team.refresh_from_db()
        self.assertEqual(self.team.partner, self.bo)

    def test_team_for_another_dinner_does_not_block(self):
        Team.objects.create(dinner=make_dinner("Other Feast"), creator=self.bo, address="y")
        self.client.force_login(self.bo)
        self.client.post(self.url)
        self.team.refresh_from_db()
        self.assertEqual(self.team.partner, self.bo)

    def test_cancelled_team_cannot_be_joined(self):
        self.team.status = Team.Status.CANCELLED
        self.team.cancelled_at = timezone.now()
        self.team.save()
        self.assertRefused(self.bo, "This team has cancelled its sign-up.")

    def test_accept_refusal(self):
        self.assertIsNone(accept_refusal(self.bo, self.team))
        self.assertIn("own", accept_refusal(self.ann, self.team))
        self.team.partner = self.bo
        self.assertIn("already has a partner", accept_refusal(make_user("cy@example.com"), self.team))
