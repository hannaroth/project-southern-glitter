from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dinners.models import Dinner


def make(title, days, **kw):
    return Dinner.objects.create(
        title=title,
        theme=kw.get("theme", "Any theme"),
        date=timezone.localdate() + timedelta(days=days),
        after_party_place=kw.get("after_party_place", "Some Bar"),
        team_cap=kw.get("team_cap", 10),
    )


class HomeDinnerListTests(TestCase):
    def test_past_dinner_hidden(self):
        make("Yesterday Feast", -1)
        make("Tomorrow Feast", 1)
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "Yesterday Feast")
        self.assertContains(response, "Tomorrow Feast")

    def test_todays_dinner_shown(self):
        make("Tonight Feast", 0)
        self.assertContains(self.client.get("/"), "Tonight Feast")

    def test_ordered_soonest_first(self):
        make("C Next Week", 7)
        make("A Tomorrow", 1)
        make("B Today", 0)
        response = self.client.get("/")
        self.assertEqual(
            [d.title for d in response.context["dinners"]],
            ["B Today", "A Tomorrow", "C Next Week"],
        )
        content = response.content.decode()
        self.assertLess(content.index("B Today"), content.index("A Tomorrow"))
        self.assertLess(content.index("A Tomorrow"), content.index("C Next Week"))

    def test_shows_title_date_theme_after_party(self):
        d = make("Around the World", 3, theme="Cuisines", after_party_place="Toad's Place")
        response = self.client.get("/")
        self.assertContains(response, "Around the World")
        self.assertContains(response, "Cuisines")
        self.assertContains(response, "Toad&#x27;s Place")
        self.assertContains(response, f"{d.date:%a}, {d.date:%b} {d.date.day}, {d.date.year}")

    def test_visible_when_logged_out(self):
        make("Public Feast", 2)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Feast")

    def test_empty_state(self):
        make("Old Feast", -5)
        response = self.client.get("/")
        self.assertContains(response, "No upcoming dinners yet. Check back soon.")


class DinnerModelAndAdminTests(TestCase):
    def test_str(self):
        d = make("Str Feast", 0)
        self.assertEqual(str(d), f"Str Feast ({d.date:%Y-%m-%d})")

    def test_update_or_create_by_title(self):
        make("Seedable", 1)
        Dinner.objects.update_or_create(title="Seedable", defaults={"theme": "New"})
        self.assertEqual(Dinner.objects.filter(title="Seedable").count(), 1)

    def test_admin_list_opens_for_staff(self):
        make("Admin Feast", 1)
        staff = get_user_model().objects.create_superuser("staff@example.com", "pw-12345-xyz")
        self.client.force_login(staff)
        response = self.client.get("/admin/dinners/dinner/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Feast")
