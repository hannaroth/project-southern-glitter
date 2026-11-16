"""Contract 5.3: the complete Team model, including the fields #27, #28 and #15 use."""

from django.db import IntegrityError
from django.test import TestCase

from teams.models import DIET_CHOICES, Team, new_invite_token

from .helpers import make_dinner, make_user


class TeamModelTests(TestCase):
    def setUp(self):
        self.dinner = make_dinner()
        self.ann = make_user("ann@example.com", first_name="Ann")

    def make_team(self, **kw):
        return Team.objects.create(dinner=self.dinner, creator=kw.pop("creator", self.ann), address="1 Elm St", **kw)

    def test_defaults(self):
        team = self.make_team()
        self.assertIsNone(team.partner)
        self.assertEqual(team.status, Team.Status.REGISTERED)
        self.assertEqual(team.preferred_course, Team.Course.NO_PREFERENCE)
        self.assertEqual(team.dietary_restrictions, [])
        self.assertEqual(team.dietary_notes, "")
        self.assertIsNone(team.cancelled_at)
        self.assertIsNotNone(team.created_at)
        self.assertFalse(team.is_complete)

    def test_choices_match_the_contract(self):
        self.assertEqual(
            [key for key, _ in DIET_CHOICES],
            ["vegetarian", "vegan", "gluten_free", "dairy_free", "nut_allergy"],
        )
        self.assertEqual(Team.Status.values, ["registered", "waitlisted", "cancelled"])
        self.assertEqual(Team.Course.values, ["starter", "main", "dessert", "no_preference"])

    def test_invite_token_is_random_long_and_unique(self):
        first, second = self.make_team(), self.make_team(creator=make_user("bo@example.com"))
        self.assertGreaterEqual(len(first.invite_token), 40)
        self.assertLessEqual(len(first.invite_token), 64)
        self.assertNotEqual(first.invite_token, second.invite_token)
        self.assertNotEqual(new_invite_token(), new_invite_token())
        with self.assertRaises(IntegrityError):
            self.make_team(creator=make_user("cy@example.com"), invite_token=first.invite_token)

    def test_ordered_by_signup_order(self):
        first = self.make_team()
        second = self.make_team(creator=make_user("bo@example.com"))
        self.assertEqual(list(Team.objects.all()), [first, second])

    def test_complete_when_partner_set(self):
        team = self.make_team(partner=make_user("bo@example.com"))
        self.assertTrue(team.is_complete)

    def test_related_names(self):
        bo = make_user("bo@example.com")
        team = self.make_team(partner=bo)
        self.assertEqual(list(self.dinner.teams.all()), [team])
        self.assertEqual(list(self.ann.created_teams.all()), [team])
        self.assertEqual(list(bo.partner_teams.all()), [team])

    def test_deleting_partner_keeps_team(self):
        bo = make_user("bo@example.com")
        team = self.make_team(partner=bo)
        bo.delete()
        team.refresh_from_db()
        self.assertIsNone(team.partner)

    def test_deleting_dinner_deletes_teams(self):
        self.make_team()
        self.dinner.delete()
        self.assertEqual(Team.objects.count(), 0)

    def test_str_and_dietary_labels(self):
        team = self.make_team(dietary_restrictions=["vegan", "nut_allergy"])
        self.assertIn("Ann", str(team))
        self.assertIn("Test Feast", str(team))
        self.assertEqual(team.dietary_labels(), ["Vegan", "Nut allergy"])
