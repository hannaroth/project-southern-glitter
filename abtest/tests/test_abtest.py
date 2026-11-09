"""Tests for the A/B test page and stats (backlog: Sprint 1, both A/B stories)."""

import re
from unittest import mock

from django.test import Client, TestCase

from abtest import views
from abtest.models import Click, Impression

PAGE = "/c6a680e"
STATS = "/c6a680e/stats"


def button_text(response):
    html = response.content.decode()
    buttons = re.findall(r'<button[^>]*id="abtest"[^>]*>(.*?)</button>', html, re.S)
    assert len(buttons) == 1, f"expected exactly one #abtest button, found {len(buttons)}"
    return buttons[0].strip()


class PageTests(TestCase):
    def test_page_is_public_200_with_no_redirect(self):
        response = self.client.get(PAGE)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Location", response.headers)

    def test_page_lists_team_nicknames(self):
        response = self.client.get(PAGE)
        for nickname in ["magnificent-aardvark", "stormy-zebra", "delightful-crocodile"]:
            self.assertContains(response, nickname)

    def test_exactly_one_button_with_valid_text_set_by_server(self):
        response = self.client.get(PAGE)
        self.assertIn(button_text(response), ["kudos", "thanks"])
        self.assertNotIn("<script", response.content.decode().lower())

    def test_new_visitor_variant_comes_from_random_choice(self):
        with mock.patch.object(views.random, "choice", return_value="kudos"):
            self.assertEqual(button_text(Client().get(PAGE)), "kudos")
        with mock.patch.object(views.random, "choice", return_value="thanks"):
            self.assertEqual(button_text(Client().get(PAGE)), "thanks")

    def test_random_choice_is_between_both_variants_equally(self):
        with mock.patch.object(views.random, "choice", return_value="kudos") as choice:
            self.client.get(PAGE)
        choice.assert_called_once_with(["kudos", "thanks"])

    def test_both_variants_show_up_over_many_visitors(self):
        seen = {button_text(Client().get(PAGE)) for _ in range(40)}
        self.assertEqual(seen, {"kudos", "thanks"})

    def test_same_visitor_keeps_same_variant(self):
        first = button_text(self.client.get(PAGE))
        with mock.patch.object(views, "choose_variant", side_effect=AssertionError("re-randomized")):
            for _ in range(5):
                self.assertEqual(button_text(self.client.get(PAGE)), first)

    def test_tampered_cookie_is_treated_as_new_visitor(self):
        self.client.cookies[views.COOKIE_NAME] = "fake:thanks"
        response = self.client.get(PAGE)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Impression.objects.count(), 1)
        self.assertNotEqual(Impression.objects.get().visitor_id, "fake")


class ImpressionTests(TestCase):
    def test_first_view_stores_one_impression_with_variant_and_timestamp(self):
        variant = button_text(self.client.get(PAGE))
        impression = Impression.objects.get()
        self.assertEqual(impression.variant, variant)
        self.assertIsNotNone(impression.created_at)
        self.assertTrue(impression.visitor_id)

    def test_reloads_do_not_add_impressions(self):
        for _ in range(5):
            self.client.get(PAGE)
        self.assertEqual(Impression.objects.count(), 1)

    def test_each_new_visitor_adds_one_impression(self):
        for _ in range(3):
            Client().get(PAGE)
        self.assertEqual(Impression.objects.count(), 3)


class ClickTests(TestCase):
    def test_click_stores_one_click_and_redirects_back(self):
        variant = button_text(self.client.get(PAGE))
        response = self.client.post(PAGE)
        self.assertRedirects(response, PAGE, fetch_redirect_response=False)
        click = Click.objects.get()
        self.assertEqual(click.variant, variant)
        self.assertIsNotNone(click.created_at)

    def test_repeated_clicks_count_once(self):
        self.client.get(PAGE)
        for _ in range(4):
            self.client.post(PAGE)
        self.assertEqual(Click.objects.count(), 1)

    def test_redirect_after_click_adds_no_impression_and_keeps_variant(self):
        variant = button_text(self.client.get(PAGE))
        response = self.client.post(PAGE, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(button_text(response), variant)
        self.assertEqual(Impression.objects.count(), 1)

    def test_click_without_csrf_token_still_counts(self):
        # A real browser posts the plain form; make sure CSRF never drops it.
        client = Client(enforce_csrf_checks=True)
        client.get(PAGE)
        client.post(PAGE)
        self.assertEqual(Click.objects.count(), 1)

    def test_click_from_visitor_who_never_saw_page_is_ignored(self):
        response = Client().post(PAGE)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Click.objects.count(), 0)


class StatsTests(TestCase):
    def make(self, variant, impressions, clicks):
        for i in range(impressions):
            Impression.objects.create(visitor_id=f"{variant}-{i}", variant=variant)
        for i in range(clicks):
            Click.objects.create(visitor_id=f"{variant}-{i}", variant=variant)

    def test_stats_public_json_with_counts(self):
        self.make("kudos", 10, 3)
        self.make("thanks", 8, 1)
        response = self.client.get(STATS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            {
                "preferred": "kudos",
                "kudos": {"impressions": 10, "clicks": 3},
                "thanks": {"impressions": 8, "clicks": 1},
            },
        )

    def test_clear_winner_uses_click_rate_not_raw_clicks(self):
        # thanks has fewer clicks but a higher rate: 4/5 vs 5/50.
        self.make("kudos", 50, 5)
        self.make("thanks", 5, 4)
        self.assertEqual(self.client.get(STATS).json()["preferred"], "thanks")

    def test_tie_returns_a_valid_value(self):
        self.make("kudos", 10, 2)
        self.make("thanks", 10, 2)
        self.assertIn(self.client.get(STATS).json()["preferred"], ["kudos", "thanks"])

    def test_zero_impressions_returns_a_valid_value(self):
        response = self.client.get(STATS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["preferred"], ["kudos", "thanks"])
        self.assertEqual(data["kudos"], {"impressions": 0, "clicks": 0})

    def test_stats_are_live_after_real_visits(self):
        visitor = Client()
        with mock.patch.object(views.random, "choice", return_value="thanks"):
            visitor.get(PAGE)
        visitor.post(PAGE)
        with mock.patch.object(views.random, "choice", return_value="kudos"):
            Client().get(PAGE)
        data = self.client.get(STATS).json()
        self.assertEqual(data["preferred"], "thanks")
        self.assertEqual(data["thanks"], {"impressions": 1, "clicks": 1})
        self.assertEqual(data["kudos"], {"impressions": 1, "clicks": 0})
