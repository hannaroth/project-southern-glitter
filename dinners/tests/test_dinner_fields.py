"""Tests for issue #12 / contract 5.1: the Dinner fields, admin, validation, migration and seed."""

import os
from datetime import date, datetime, time, timedelta
from io import StringIO
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from dinners.models import Dinner

NEW_YORK = ZoneInfo("America/New_York")
User = get_user_model()
ADD_URL = "/admin/dinners/dinner/add/"


def deadline(day, hour=23, minute=59):
    return datetime.combine(day, time(hour, minute), tzinfo=NEW_YORK)


def dinner_kwargs(**overrides):
    day = date(2027, 3, 20)
    kwargs = dict(
        title="Spring Feast",
        theme="Spring",
        date=day,
        starter_time=time(18, 0),
        main_time=time(19, 30),
        dessert_time=time(21, 0),
        after_party_name="The Lounge",
        after_party_address="1 Test Street, New Haven, CT",
        team_cap=12,
        signup_deadline=deadline(day - timedelta(days=2)),
    )
    kwargs.update(overrides)
    return kwargs


def form_data(**overrides):
    """POST data for the admin add/change form."""
    data = {
        "title": "Spring Feast",
        "theme": "Spring",
        "date": "2027-03-20",
        "starter_time": "18:00:00",
        "main_time": "19:30:00",
        "dessert_time": "21:00:00",
        "after_party_name": "The Lounge",
        "after_party_address": "1 Test Street, New Haven, CT",
        "team_cap": "12",
        "signup_deadline_0": "2027-03-18",
        "signup_deadline_1": "23:59:00",
    }
    data.update(overrides)
    return data


class ModelFieldTests(TestCase):
    def test_contract_fields_and_types(self):
        expected = {
            "title": ("CharField", 200),
            "theme": ("CharField", 200),
            "date": ("DateField", None),
            "starter_time": ("TimeField", None),
            "main_time": ("TimeField", None),
            "dessert_time": ("TimeField", None),
            "after_party_name": ("CharField", 200),
            "after_party_address": ("CharField", 255),
            "team_cap": ("PositiveIntegerField", None),
            "signup_deadline": ("DateTimeField", None),
        }
        fields = {f.name: f for f in Dinner._meta.get_fields() if f.concrete and not f.primary_key}
        self.assertEqual(set(fields), set(expected))
        for name, (kind, length) in expected.items():
            self.assertEqual(type(fields[name]).__name__, kind, name)
            self.assertEqual(fields[name].max_length, length, name)
        self.assertFalse(hasattr(Dinner, "after_party_place"))

    def test_saves_and_reloads_all_fields(self):
        saved = Dinner.objects.create(**dinner_kwargs())
        loaded = Dinner.objects.get(pk=saved.pk)
        for name, value in dinner_kwargs().items():
            self.assertEqual(getattr(loaded, name), value, name)


class ValidationTests(TestCase):
    def check(self, **overrides):
        Dinner(**dinner_kwargs(**overrides)).full_clean()

    def test_valid_dinner_passes(self):
        self.check()

    def test_starter_must_be_before_main(self):
        for starter in (time(19, 30), time(20, 0)):
            with self.assertRaises(ValidationError) as ctx:
                self.check(starter_time=starter)
            self.assertIn("main_time", ctx.exception.message_dict)

    def test_main_must_be_before_dessert(self):
        for main in (time(21, 0), time(22, 0)):
            with self.assertRaises(ValidationError) as ctx:
                self.check(main_time=main)
            self.assertIn("dessert_time", ctx.exception.message_dict)

    def test_deadline_must_be_before_the_dinner_date(self):
        day = date(2027, 3, 20)
        self.check(signup_deadline=deadline(day - timedelta(days=1)))  # the evening before is fine
        for bad in (deadline(day, 9, 0), deadline(day, 0, 0), deadline(day + timedelta(days=1), 8, 0)):
            with self.assertRaises(ValidationError) as ctx:
                self.check(signup_deadline=bad)
            self.assertIn("signup_deadline", ctx.exception.message_dict)

    def test_deadline_is_judged_in_new_york_time(self):
        # 02:00 UTC on Mar 20 is still 22:00 on Mar 19 in New York, so it is before the dinner date.
        self.check(signup_deadline=datetime(2027, 3, 20, 2, 0, tzinfo=ZoneInfo("UTC")))

    def test_address_is_required(self):
        with self.assertRaises(ValidationError) as ctx:
            self.check(after_party_address="")
        self.assertIn("after_party_address", ctx.exception.message_dict)


class AdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser("staff@example.com", "pw-12345-xyz")
        cls.participant = User.objects.create_user("member@example.com", "pw-12345-xyz")

    def login(self, user):
        self.client.force_login(user)

    def test_admin_can_create_a_dinner(self):
        self.login(self.staff)
        self.assertEqual(self.client.get(ADD_URL).status_code, 200)
        response = self.client.post(ADD_URL, form_data())
        self.assertRedirects(response, "/admin/dinners/dinner/", fetch_redirect_response=False)
        dinner = Dinner.objects.get()
        self.assertEqual(dinner.after_party_name, "The Lounge")
        self.assertEqual(dinner.after_party_address, "1 Test Street, New Haven, CT")
        self.assertEqual(dinner.starter_time, time(18, 0))
        self.assertEqual(dinner.dessert_time, time(21, 0))
        self.assertEqual(dinner.signup_deadline, deadline(date(2027, 3, 18)))

    def test_admin_can_edit_a_dinner(self):
        dinner = Dinner.objects.create(**dinner_kwargs())
        self.login(self.staff)
        url = f"/admin/dinners/dinner/{dinner.pk}/change/"
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, form_data(theme="Winter", main_time="20:00:00", team_cap="15"))
        self.assertEqual(response.status_code, 302)
        dinner.refresh_from_db()
        self.assertEqual((dinner.theme, dinner.main_time, dinner.team_cap), ("Winter", time(20, 0), 15))

    def test_form_is_grouped_into_the_four_sections(self):
        fieldsets = self.admin_class().fieldsets
        self.assertEqual(
            [(name, opts["fields"]) for name, opts in fieldsets],
            [
                ("Basics", ("title", "theme", "date")),
                ("Course times", ("starter_time", "main_time", "dessert_time")),
                ("After-party", ("after_party_name", "after_party_address")),
                ("Sign-ups", ("team_cap", "signup_deadline")),
            ],
        )
        self.login(self.staff)
        page = self.client.get(ADD_URL)
        for heading in ("Basics", "Course times", "After-party", "Sign-ups"):
            self.assertContains(page, heading)

    def admin_class(self):
        from django.contrib import admin

        return admin.site._registry[Dinner]

    def test_every_field_is_editable_in_the_admin(self):
        listed = [f for _, opts in self.admin_class().fieldsets for f in opts["fields"]]
        editable = [f.name for f in Dinner._meta.get_fields() if f.concrete and not f.primary_key]
        self.assertCountEqual(listed, editable)

    def test_admin_form_rejects_times_out_of_order(self):
        self.login(self.staff)
        response = self.client.post(ADD_URL, form_data(starter_time="20:00:00"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The main course must start after the starter.")
        response = self.client.post(ADD_URL, form_data(dessert_time="19:00:00"))
        self.assertContains(response, "The dessert must start after the main course.")
        self.assertEqual(Dinner.objects.count(), 0)

    def test_admin_form_rejects_a_deadline_on_or_after_the_dinner_date(self):
        self.login(self.staff)
        response = self.client.post(ADD_URL, form_data(signup_deadline_0="2027-03-20", signup_deadline_1="09:00:00"))
        self.assertContains(response, "The sign-up deadline must be before the dinner date.")
        self.assertEqual(Dinner.objects.count(), 0)

    def test_admin_form_requires_the_address(self):
        self.login(self.staff)
        response = self.client.post(ADD_URL, form_data(after_party_address=""))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertEqual(Dinner.objects.count(), 0)

    def test_participant_is_refused(self):
        dinner = Dinner.objects.create(**dinner_kwargs())
        self.login(self.participant)
        change_url = f"/admin/dinners/dinner/{dinner.pk}/change/"
        for url in ("/admin/dinners/dinner/", ADD_URL, change_url):
            self.assertNotEqual(self.client.get(url).status_code, 200, url)
        self.client.post(ADD_URL, form_data(title="Sneaky"))
        self.client.post(change_url, form_data(title="Hacked"))
        self.assertEqual(list(Dinner.objects.values_list("title", flat=True)), ["Spring Feast"])

    def test_anonymous_is_sent_to_the_login(self):
        response = self.client.get(ADD_URL)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])


class HomePageTests(TestCase):
    def test_home_shows_the_after_party_name(self):
        day = timezone.localdate() + timedelta(days=5)
        Dinner.objects.create(
            **dinner_kwargs(date=day, signup_deadline=deadline(day - timedelta(days=2)), after_party_name="Toad's Place")
        )
        response = self.client.get("/")
        self.assertContains(response, "After-party: Toad&#x27;s Place")


class MigrationTests(TransactionTestCase):
    """Run 0002 against rows created under 0001 (the data that exists on staging today)."""

    before = [("dinners", "0001_initial")]
    after = [("dinners", "0002_dinner_fields")]

    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_existing_dinners_keep_their_data_and_get_defaults(self):
        old = self.migrate(self.before).get_model("dinners", "Dinner")
        # Two days before Nov 2 2026 is Oct 31 (EDT); two days before Nov 4 is Nov 2 (EST, DST ended Nov 1).
        old.objects.create(title="A", theme="T1", date=date(2026, 11, 2), after_party_place="Bar A", team_cap=9)
        old.objects.create(title="B", theme="T2", date=date(2026, 11, 4), after_party_place="Bar B", team_cap=12)

        new = self.migrate(self.after).get_model("dinners", "Dinner")
        a, b = new.objects.get(title="A"), new.objects.get(title="B")

        self.assertEqual((a.after_party_name, a.theme, a.team_cap, a.date), ("Bar A", "T1", 9, date(2026, 11, 2)))
        self.assertEqual((b.after_party_name, b.theme, b.team_cap), ("Bar B", "T2", 12))
        for dinner in (a, b):
            self.assertEqual(dinner.starter_time, time(18, 0))
            self.assertEqual(dinner.main_time, time(19, 30))
            self.assertEqual(dinner.dessert_time, time(21, 0))
            self.assertEqual(dinner.after_party_address, "")
        self.assertEqual(a.signup_deadline, deadline(date(2026, 10, 31)))
        self.assertEqual(b.signup_deadline, deadline(date(2026, 11, 2)))
        self.assertEqual(a.signup_deadline.astimezone(NEW_YORK).utcoffset(), timedelta(hours=-4))
        self.assertEqual(b.signup_deadline.astimezone(NEW_YORK).utcoffset(), timedelta(hours=-5))

    def test_signup_deadline_is_not_nullable_afterwards(self):
        self.migrate(self.after)
        with connection.cursor() as cursor:
            columns = {c.name: c for c in connection.introspection.get_table_description(cursor, "dinners_dinner")}
        self.assertFalse(columns["signup_deadline"].null_ok)
        self.assertNotIn("after_party_place", columns)


class SeedFieldTests(TestCase):
    ENV = {"SEED_ADMIN_PASSWORD": "throwaway-admin-pw-1", "SEED_MEMBER_PASSWORD": "throwaway-member-pw-2"}

    def seed(self):
        with patch.dict(os.environ, self.ENV):
            call_command("seed", stdout=StringIO())

    def test_seeded_dinners_have_every_new_field_and_are_valid(self):
        self.seed()
        self.assertEqual(Dinner.objects.count(), 3)
        for dinner in Dinner.objects.all():
            dinner.full_clean()
            self.assertEqual((dinner.starter_time, dinner.main_time, dinner.dessert_time), (time(18), time(19, 30), time(21)))
            self.assertTrue(dinner.after_party_name)
            self.assertTrue(dinner.after_party_address)
            self.assertEqual(dinner.signup_deadline, deadline(dinner.date - timedelta(days=2)))
            self.assertTrue(dinner.signup_deadline < timezone.now() + timedelta(days=60))

    def test_running_twice_is_idempotent(self):
        self.seed()
        first = list(Dinner.objects.order_by("pk").values())
        self.seed()
        self.assertEqual(list(Dinner.objects.order_by("pk").values()), first)

    def test_rerun_fills_the_new_fields_on_a_dinner_that_lacks_them(self):
        self.seed()
        Dinner.objects.filter(title="Through the Eras").update(after_party_address="", main_time=time(23, 0))
        self.seed()
        dinner = Dinner.objects.get(title="Through the Eras")
        self.assertTrue(dinner.after_party_address)
        self.assertEqual(dinner.main_time, time(19, 30))
        self.assertEqual(Dinner.objects.count(), 3)

    def test_moved_dinner_gets_a_matching_deadline(self):
        self.seed()
        Dinner.objects.filter(title="Through the Eras").update(
            date=timezone.localdate() - timedelta(days=30), signup_deadline=deadline(date(2020, 1, 1))
        )
        self.seed()
        dinner = Dinner.objects.get(title="Through the Eras")
        self.assertGreaterEqual(dinner.date, timezone.localdate())
        self.assertEqual(dinner.signup_deadline, deadline(dinner.date - timedelta(days=2)))
        dinner.full_clean()
