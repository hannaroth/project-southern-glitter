"""Share a dinner (#14): the public detail page with a copy-link button (contract 5.2)."""

import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dinners.tests.test_home import make
from teams.models import Team


class DetailPageTests(TestCase):
    def setUp(self):
        self.dinner = make(
            "Around the World",
            10,
            theme="Each course from a different country",
            after_party_name="Rooftop Bar",
            after_party_address="99 Secret Lane",
        )
        self.url = f"/dinners/{self.dinner.pk}/"

    def test_url_name_and_path(self):
        self.assertEqual(reverse("dinners:detail", args=[self.dinner.pk]), self.url)

    def test_public_without_login_and_no_redirect(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dinners/detail.html")

    def test_shows_public_details(self):
        response = self.client.get(self.url)
        for text in ["Around the World", "Each course from a different country", "Rooftop Bar",
                     "6:00 PM", "7:30 PM", "9:00 PM", "Up to 10 teams"]:
            self.assertContains(response, text)

    def test_hides_after_party_address(self):
        # The page is public; addresses come with the My Dinner page (#18).
        self.assertNotContains(self.client.get(self.url), "99 Secret Lane")

    def test_unknown_dinner_is_404(self):
        self.assertEqual(self.client.get("/dinners/999999/").status_code, 404)


class ShareLinkTests(TestCase):
    def setUp(self):
        self.dinner = make("Share Me", 10)
        self.url = f"/dinners/{self.dinner.pk}/"

    def test_full_link_shown_as_text_and_in_copy_field(self):
        html = self.client.get(self.url).content.decode()
        full = f"http://testserver{self.url}"
        field = re.search(r'<input[^>]*id="share-url"[^>]*>', html).group(0)
        self.assertIn(f'value="{full}"', field)
        self.assertIn("readonly", field)
        self.assertIn(f"<small>{full}</small>", html)

    def test_copy_button_uses_clipboard_with_fallback(self):
        html = self.client.get(self.url).content.decode()
        self.assertIn('id="copy-share"', html)
        self.assertIn("navigator.clipboard.writeText", html)
        self.assertIn("field.select()", html)

    def test_link_uses_https_behind_render_proxy(self):
        # Render terminates HTTPS and forwards the request with these headers.
        response = self.client.get(self.url, headers={"x-forwarded-proto": "https", "host": "testserver"})
        self.assertContains(response, f'value="https://testserver{self.url}"')

    def test_link_preview_tags(self):
        response = self.client.get(self.url)
        self.assertContains(response, '<meta property="og:title" content="Share Me · Running Dinner New Haven">')
        self.assertContains(response, f'<meta property="og:url" content="http://testserver{self.url}">')

    def test_share_box_shown_to_logged_in_users_too(self):
        user = get_user_model().objects.create_user(email="ann@example.com", password="pw-12345-long")
        self.client.force_login(user)
        self.assertContains(self.client.get(self.url), 'id="copy-share"')


class JoinSectionTests(TestCase):
    def setUp(self):
        self.dinner = make("Joinable", 10)
        self.url = f"/dinners/{self.dinner.pk}/"
        self.user = get_user_model().objects.create_user(email="ann@example.com", password="pw-12345-long")

    def test_logged_out_visitor_asked_to_log_in_and_comes_back(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Log in to join")
        self.assertContains(response, f'href="/login/?next={self.url}"')

    def test_login_next_returns_to_the_dinner(self):
        response = self.client.post(
            f"/login/?next={self.url}",
            {"username": "ann@example.com", "password": "pw-12345-long", "next": self.url},
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)

    def test_logged_in_user_not_asked_to_log_in(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertNotContains(response, "Log in to join")
        self.assertContains(response, "Sign-ups close")

    def test_user_without_team_gets_sign_up_button(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, f'href="/dinners/{self.dinner.pk}/signup/" role="button">Sign up as a team</a>')
        self.assertNotContains(response, ">Your team</a>")

    def test_user_with_active_team_gets_your_team_button(self):
        team = Team.objects.create(dinner=self.dinner, creator=self.user, address="1 Elm St")
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context["my_team"], team)
        self.assertContains(response, f'href="/teams/{team.pk}/" role="button">Your team</a>')
        self.assertNotContains(response, ">Sign up as a team</a>")

    def test_partner_also_gets_your_team_button(self):
        creator = get_user_model().objects.create_user(email="bob@example.com", password="pw-12345-long")
        team = Team.objects.create(dinner=self.dinner, creator=creator, partner=self.user, address="1 Elm St")
        self.client.force_login(self.user)
        self.assertContains(self.client.get(self.url), f'href="/teams/{team.pk}/" role="button">Your team</a>')

    def test_cancelled_team_does_not_count(self):
        Team.objects.create(dinner=self.dinner, creator=self.user, address="1 Elm St", status=Team.Status.CANCELLED)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, ">Sign up as a team</a>")
        self.assertNotContains(response, ">Your team</a>")

    def test_team_for_another_dinner_does_not_count(self):
        other = make("Other Dinner", 12)
        Team.objects.create(dinner=other, creator=self.user, address="1 Elm St")
        self.client.force_login(self.user)
        self.assertContains(self.client.get(self.url), ">Sign up as a team</a>")

    def test_logged_out_visitor_gets_no_join_buttons(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, ">Sign up as a team</a>")
        self.assertNotContains(response, ">Your team</a>")

    def test_closed_signups_show_closed_and_no_login_button(self):
        self.dinner.signup_deadline = timezone.now() - timedelta(minutes=1)
        self.dinner.save()
        response = self.client.get(self.url)
        self.assertContains(response, "Sign-ups for this dinner are closed.")
        self.assertNotContains(response, "Log in to join")

    def test_past_dinner_still_opens_but_cannot_be_joined(self):
        past = make("Last Month", -30)
        response = self.client.get(f"/dinners/{past.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This dinner has already happened.")
        self.assertNotContains(response, "Log in to join")


class HomeLinksTests(TestCase):
    def test_home_links_each_dinner_title_to_its_page(self):
        first = make("First Dinner", 3)
        second = make("Second Dinner", 5)
        response = self.client.get("/")
        self.assertContains(response, f'<a href="/dinners/{first.pk}/">First Dinner</a>')
        self.assertContains(response, f'<a href="/dinners/{second.pk}/">Second Dinner</a>')
