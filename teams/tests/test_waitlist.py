"""Issue #28: once the team cap is reached, new teams join a waitlist in sign-up order."""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from teams.models import Team
from teams.services import assign_status, is_full, registered_count, waitlist_position

from .helpers import make_dinner, make_user

FORM = {"address": "1 Elm St, New Haven, CT", "preferred_course": "no_preference"}


def sign_up(client, user, dinner):
    client.force_login(user)
    return client.post(reverse("teams:signup", args=[dinner.pk]), FORM)


def new_team(dinner, email, **kw):
    """A team row created the way the sign-up view does it, with assign_status()."""
    team = Team(dinner=dinner, creator=make_user(email), address="x", **kw)
    assign_status(team)
    team.save()
    return team


class AssignStatusTests(TestCase):
    def test_registered_until_cap_then_waitlisted(self):
        dinner = make_dinner(team_cap=2)
        statuses = [new_team(dinner, f"u{i}@example.com").status for i in range(4)]
        self.assertEqual(statuses, ["registered", "registered", "waitlisted", "waitlisted"])

    def test_incomplete_team_holds_its_spot(self):
        # Decided Nov 15: a team holds its spot from sign-up, before the partner accepts.
        dinner = make_dinner(team_cap=1)
        first = new_team(dinner, "a@example.com")
        self.assertIsNone(first.partner)
        self.assertEqual(new_team(dinner, "b@example.com").status, Team.Status.WAITLISTED)

    def test_cancelled_teams_do_not_take_a_spot(self):
        dinner = make_dinner(team_cap=1)
        Team.objects.create(dinner=dinner, creator=make_user("gone@example.com"), address="x",
                            status=Team.Status.CANCELLED)
        self.assertEqual(new_team(dinner, "a@example.com").status, Team.Status.REGISTERED)

    def test_waitlisted_teams_do_not_take_a_spot(self):
        dinner = make_dinner(team_cap=1)
        Team.objects.create(dinner=dinner, creator=make_user("w@example.com"), address="x",
                            status=Team.Status.WAITLISTED)
        self.assertEqual(new_team(dinner, "a@example.com").status, Team.Status.REGISTERED)

    def test_other_dinners_do_not_count(self):
        full = make_dinner("Full", team_cap=1)
        new_team(full, "a@example.com")
        other = make_dinner("Other", team_cap=1)
        self.assertEqual(new_team(other, "b@example.com").status, Team.Status.REGISTERED)

    def test_cap_zero_waitlists_everyone(self):
        self.assertEqual(new_team(make_dinner(team_cap=0), "a@example.com").status,
                         Team.Status.WAITLISTED)

    def test_rechecking_a_saved_team_does_not_count_itself(self):
        dinner = make_dinner(team_cap=1)
        team = new_team(dinner, "a@example.com")
        self.assertEqual(assign_status(team), Team.Status.REGISTERED)

    def test_is_full_and_count(self):
        dinner = make_dinner(team_cap=2)
        self.assertFalse(is_full(dinner))
        new_team(dinner, "a@example.com")
        new_team(dinner, "b@example.com")
        self.assertTrue(is_full(dinner))
        self.assertEqual(registered_count(dinner), 2)


class WaitlistPositionTests(TestCase):
    def test_positions_follow_sign_up_order(self):
        dinner = make_dinner(team_cap=1)
        teams = [new_team(dinner, f"u{i}@example.com") for i in range(4)]
        self.assertEqual([waitlist_position(t) for t in teams], [None, 1, 2, 3])

    def test_ties_on_created_at_are_broken_by_id(self):
        dinner = make_dinner(team_cap=0)
        a, b = new_team(dinner, "a@example.com"), new_team(dinner, "b@example.com")
        Team.objects.filter(pk__in=[a.pk, b.pk]).update(created_at=timezone.now())
        a.refresh_from_db()
        b.refresh_from_db()
        self.assertEqual((waitlist_position(a), waitlist_position(b)), (1, 2))

    def test_position_moves_up_when_someone_ahead_leaves_the_waitlist(self):
        dinner = make_dinner(team_cap=0)
        a, b = new_team(dinner, "a@example.com"), new_team(dinner, "b@example.com")
        a.status = Team.Status.CANCELLED
        a.save()
        self.assertEqual(waitlist_position(b), 1)


class SignupViewWaitlistTests(TestCase):
    def setUp(self):
        self.dinner = make_dinner(team_cap=1)
        self.first = make_user("first@example.com", first_name="First")
        self.second = make_user("second@example.com", first_name="Second")
        self.third = make_user("third@example.com", first_name="Third")

    def test_first_team_registered_with_normal_message(self):
        response = sign_up(self.client, self.first, self.dinner)
        team = Team.objects.get(creator=self.first)
        self.assertEqual(team.status, Team.Status.REGISTERED)
        page = self.client.get(response["Location"])
        self.assertContains(page, "Your team is signed up.")
        self.assertNotContains(page, 'id="waitlist"')

    def test_team_over_the_cap_is_waitlisted_and_told_its_place(self):
        sign_up(self.client, self.first, self.dinner)
        response = sign_up(self.client, self.second, self.dinner)
        team = Team.objects.get(creator=self.second)
        self.assertEqual(team.status, Team.Status.WAITLISTED)
        page = self.client.get(response["Location"])
        self.assertContains(page, "your team is on the waitlist (number 1)")
        self.assertContains(page, "Waitlisted")
        self.assertContains(page, "<strong>Waitlist position:</strong> 1.")

    def test_second_waitlisted_team_is_number_two(self):
        sign_up(self.client, self.first, self.dinner)
        sign_up(self.client, self.second, self.dinner)
        response = sign_up(self.client, self.third, self.dinner)
        page = self.client.get(response["Location"])
        self.assertContains(page, "<strong>Waitlist position:</strong> 2.")

    def test_form_warns_when_the_dinner_is_full(self):
        url = reverse("teams:signup", args=[self.dinner.pk])
        self.client.force_login(self.second)
        self.assertNotContains(self.client.get(url), 'id="full-notice"')
        sign_up(self.client, self.first, self.dinner)
        self.client.force_login(self.second)
        self.assertContains(self.client.get(url), "This dinner is full.")

    def test_waitlisted_person_still_has_one_team_per_dinner(self):
        sign_up(self.client, self.first, self.dinner)
        sign_up(self.client, self.second, self.dinner)
        team = Team.objects.get(creator=self.second)
        response = sign_up(self.client, self.second, self.dinner)
        self.assertRedirects(response, reverse("teams:detail", args=[team.pk]))
        self.assertEqual(Team.objects.filter(creator=self.second).count(), 1)

    def test_admin_sees_waitlist_position_too(self):
        sign_up(self.client, self.first, self.dinner)
        sign_up(self.client, self.second, self.dinner)
        team = Team.objects.get(creator=self.second)
        self.client.force_login(make_user("boss@example.com", is_staff=True))
        page = self.client.get(reverse("teams:detail", args=[team.pk]))
        self.assertContains(page, "<strong>Waitlist position:</strong> 1.")

    def test_closed_dinner_waitlists_nobody(self):
        closed = make_dinner("Closed", deadline_in=-timedelta(minutes=1), team_cap=0)
        sign_up(self.client, self.first, closed)
        self.assertFalse(Team.objects.filter(dinner=closed).exists())
