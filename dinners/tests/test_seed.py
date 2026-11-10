import os
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from dinners.models import Dinner

ADMIN_PW = "throwaway-admin-pw-1"
MEMBER_PW = "throwaway-member-pw-2"
ENV = {"SEED_ADMIN_PASSWORD": ADMIN_PW, "SEED_MEMBER_PASSWORD": MEMBER_PW}
TITLES = ["Around the World", "Through the Eras", "No Theme, Just Dinner"]
User = get_user_model()


def run_seed(env=ENV):
    out = StringIO()
    with patch.dict(os.environ, env):
        call_command("seed", stdout=out)
    return out.getvalue()


def snapshot():
    return (
        list(User.objects.order_by("pk").values_list("pk", "email", "password", "is_staff", "is_superuser")),
        list(Dinner.objects.order_by("pk").values_list("pk", "title", "theme", "date", "after_party_place", "team_cap")),
    )


class SeedTests(TestCase):
    def test_creates_accounts(self):
        run_seed()
        admin = User.objects.get(email="admin@example.com")
        member = User.objects.get(email="member@example.com")
        self.assertTrue(admin.is_staff and admin.is_superuser)
        self.assertFalse(member.is_staff or member.is_superuser)
        self.assertEqual(User.objects.count(), 2)

    def test_logins_and_admin_access(self):
        run_seed()
        self.assertTrue(self.client.login(username="admin@example.com", password=ADMIN_PW))
        self.assertEqual(self.client.get("/admin/").status_code, 200)
        self.client.logout()
        response = self.client.post("/login/", {"username": "member@example.com", "password": MEMBER_PW})
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.client.get("/admin/").status_code, 200)

    def test_both_log_in_through_login_page(self):
        run_seed()
        for email, pw in [("admin@example.com", ADMIN_PW), ("member@example.com", MEMBER_PW)]:
            response = self.client.post("/login/", {"username": email, "password": pw})
            self.assertEqual(response.status_code, 302)
            self.client.logout()

    def test_three_upcoming_dinners_on_home_page(self):
        run_seed()
        self.assertEqual(sorted(Dinner.objects.values_list("title", flat=True)), sorted(TITLES))
        today = timezone.localdate()
        for dinner in Dinner.objects.all():
            self.assertGreaterEqual(dinner.date, today)
            self.assertEqual(dinner.team_cap % 3, 0)
        home = self.client.get("/")
        for title in TITLES:
            self.assertContains(home, title)

    def test_second_run_changes_nothing(self):
        run_seed()
        before = snapshot()
        output = run_seed()
        self.assertEqual(snapshot(), before)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Dinner.objects.count(), 3)
        self.assertNotIn("created", output)
        self.assertNotIn("updated", output)

    def test_changed_password_and_flags_are_reset(self):
        run_seed()
        admin = User.objects.get(email="admin@example.com")
        admin.set_password("someone-changed-it")
        admin.is_superuser = False
        admin.save()
        run_seed()
        admin.refresh_from_db()
        self.assertTrue(admin.check_password(ADMIN_PW))
        self.assertTrue(admin.is_superuser)
        self.assertEqual(User.objects.count(), 2)

    def test_past_dinner_is_moved_to_the_future(self):
        run_seed()
        old = timezone.localdate() - timedelta(days=30)
        Dinner.objects.filter(title="Through the Eras").update(date=old)
        pk = Dinner.objects.get(title="Through the Eras").pk
        run_seed()
        dinner = Dinner.objects.get(title="Through the Eras")
        self.assertEqual(dinner.pk, pk)
        self.assertGreaterEqual(dinner.date, timezone.localdate())
        self.assertEqual(Dinner.objects.count(), 3)

    def test_future_dinner_keeps_its_date(self):
        run_seed()
        later = timezone.localdate() + timedelta(days=100)
        Dinner.objects.filter(title="Around the World").update(date=later)
        run_seed()
        self.assertEqual(Dinner.objects.get(title="Around the World").date, later)

    def test_missing_env_var_creates_nothing(self):
        for missing in ENV:
            for value in (None, ""):
                env = dict(ENV)
                with patch.dict(os.environ, env):
                    if value is None:
                        os.environ.pop(missing)
                    else:
                        os.environ[missing] = value
                    with self.assertRaises(CommandError) as ctx:
                        call_command("seed", stdout=StringIO())
                self.assertIn(missing, str(ctx.exception))
                self.assertEqual(User.objects.count(), 0)
                self.assertEqual(Dinner.objects.count(), 0)

    def test_both_missing_are_named(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SEED_ADMIN_PASSWORD", None)
            os.environ.pop("SEED_MEMBER_PASSWORD", None)
            with self.assertRaises(CommandError) as ctx:
                call_command("seed", stdout=StringIO())
        self.assertIn("SEED_ADMIN_PASSWORD", str(ctx.exception))
        self.assertIn("SEED_MEMBER_PASSWORD", str(ctx.exception))

    def test_output_never_contains_passwords(self):
        output = run_seed() + run_seed()
        self.assertNotIn(ADMIN_PW, output)
        self.assertNotIn(MEMBER_PW, output)
