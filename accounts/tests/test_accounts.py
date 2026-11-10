import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()

PASSWORD = "throwaway-test-pass-123"

# The admin pages use {% static %}; the manifest only exists after collectstatic.
PLAIN_STATIC = override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)


class UserModelTests(TestCase):
    def test_create_user_is_participant(self):
        user = User.objects.create_user("a@example.com", PASSWORD)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(PASSWORD))

    def test_create_superuser_is_admin(self):
        user = User.objects.create_superuser("root@example.com", PASSWORD)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_email_is_required_and_unique(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("", PASSWORD)
        User.objects.create_user("a@example.com", PASSWORD)
        with self.assertRaises(Exception):
            User.objects.create_user("a@example.com", PASSWORD)

    def test_email_is_the_login_name(self):
        self.assertEqual(User.USERNAME_FIELD, "email")


class SignUpTests(TestCase):
    data = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "password1": PASSWORD,
        "password2": PASSWORD,
    }

    def test_page_renders(self):
        self.assertEqual(self.client.get("/signup/").status_code, 200)

    def test_signup_creates_participant_and_logs_in(self):
        response = self.client.post("/signup/", self.data)
        self.assertRedirects(response, "/")
        user = User.objects.get(email="ada@example.com")
        self.assertEqual(user.first_name, "Ada")
        self.assertEqual(user.last_name, "Lovelace")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_duplicate_email_rejected(self):
        User.objects.create_user("ada@example.com", PASSWORD)
        response = self.client.post("/signup/", {**self.data, "email": "ADA@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertEqual(User.objects.count(), 1)

    def test_password_mismatch_rejected(self):
        response = self.client.post("/signup/", {**self.data, "password2": "different-pass-456"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_name_is_required(self):
        response = self.client.post("/signup/", {**self.data, "first_name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())


class LoginLogoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "grace@example.com", PASSWORD, first_name="Grace", last_name="Hopper"
        )

    def test_login_page_renders(self):
        self.assertEqual(self.client.get("/login/").status_code, 200)

    def test_login_with_right_password(self):
        response = self.client.post("/login/", {"username": "grace@example.com", "password": PASSWORD})
        self.assertRedirects(response, "/")
        self.assertEqual(self.client.session["_auth_user_id"], str(self.user.pk))

    def test_login_with_wrong_password(self):
        response = self.client.post("/login/", {"username": "grace@example.com", "password": "wrong-pass"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_with_unknown_email(self):
        response = self.client.post("/login/", {"username": "nobody@example.com", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_by_post(self):
        self.client.force_login(self.user)
        response = self.client.post("/logout/")
        self.assertRedirects(response, "/")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_by_get_is_not_allowed(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/logout/").status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)


class HomePageTests(TestCase):
    def test_logged_out_shows_login_and_signup_links(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/login/"')
        self.assertContains(response, 'href="/signup/"')
        self.assertNotContains(response, "Log out")

    def test_logged_in_shows_first_name_and_logout_form(self):
        user = User.objects.create_user("grace@example.com", PASSWORD, first_name="Grace")
        self.client.force_login(user)
        response = self.client.get("/")
        self.assertContains(response, "Grace")
        self.assertContains(response, 'action="/logout/"')
        self.assertContains(response, "Log out")
        self.assertNotContains(response, 'href="/signup/"')

    def test_falls_back_to_email_without_a_first_name(self):
        user = User.objects.create_user("anon@example.com", PASSWORD)
        self.client.force_login(user)
        self.assertContains(self.client.get("/"), "anon@example.com")

    def test_page_is_mobile_friendly_and_uses_pico(self):
        response = self.client.get("/")
        self.assertContains(response, 'name="viewport"')
        self.assertContains(response, "pico")


@PLAIN_STATIC
class AdminAccessTests(TestCase):
    def test_anonymous_redirected_to_admin_login(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/admin/login/"))

    def test_regular_user_refused(self):
        user = User.objects.create_user("member@example.com", PASSWORD)
        self.client.force_login(user)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/admin/login/"))

    def test_regular_user_cannot_log_in_through_admin_form(self):
        User.objects.create_user("member@example.com", PASSWORD)
        response = self.client.post(
            "/admin/login/", {"username": "member@example.com", "password": PASSWORD, "next": "/admin/"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_user_can_open_admin(self):
        staff = User.objects.create_user("staff@example.com", PASSWORD, is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_staff_can_open_user_list_and_add_form(self):
        root = User.objects.create_superuser("root@example.com", PASSWORD)
        self.client.force_login(root)
        self.assertEqual(self.client.get("/admin/accounts/user/").status_code, 200)
        self.assertEqual(self.client.get("/admin/accounts/user/add/").status_code, 200)


class RoutingTests(TestCase):
    def test_urls(self):
        self.assertEqual(reverse("home"), "/")
        self.assertEqual(reverse("signup"), "/signup/")
        self.assertEqual(reverse("login"), "/login/")
        self.assertEqual(reverse("logout"), "/logout/")

    def test_root_urlconf_does_not_redirect_slashless_paths(self):
        # The A/B page lives at /c6a680e with no trailing slash and must never be redirected.
        # With nothing mounted there yet it is a plain 404, not a 301 to /c6a680e/.
        self.assertEqual(self.client.get("/c6a680e").status_code, 404)


class SettingsTests(TestCase):
    def reload_settings(self, **env):
        """Execute config.settings in a fresh namespace with the given environment."""
        import importlib

        import config.settings as module

        with mock.patch.dict(os.environ, env, clear=True):
            return importlib.reload(module)

    def tearDown(self):
        import importlib

        import config.settings as module

        importlib.reload(module)

    def test_secret_key_required_when_debug_off(self):
        with self.assertRaises(ImproperlyConfigured):
            self.reload_settings(DATABASE_URL="postgres://u:p@h/d")

    def test_debug_defaults_to_off(self):
        s = self.reload_settings(SECRET_KEY="x", DATABASE_URL="postgres://u:p@h/d")
        self.assertFalse(s.DEBUG)

    def test_insecure_default_key_only_in_debug(self):
        s = self.reload_settings(DEBUG="true", DATABASE_URL="postgres://u:p@h/d")
        self.assertTrue(s.DEBUG)
        self.assertTrue(s.SECRET_KEY)

    def test_hosts_and_origins_from_env(self):
        s = self.reload_settings(
            SECRET_KEY="x",
            DATABASE_URL="postgres://u:p@h/d",
            ALLOWED_HOSTS="a.example.com, b.example.com",
            CSRF_TRUSTED_ORIGINS="https://a.example.com",
        )
        self.assertEqual(s.ALLOWED_HOSTS, ["a.example.com", "b.example.com"])
        self.assertEqual(s.CSRF_TRUSTED_ORIGINS, ["https://a.example.com"])

    def test_render_hostname_added_automatically(self):
        s = self.reload_settings(
            SECRET_KEY="x",
            DATABASE_URL="postgres://u:p@h/d",
            RENDER_EXTERNAL_HOSTNAME="app.onrender.com",
        )
        self.assertIn("app.onrender.com", s.ALLOWED_HOSTS)
        self.assertIn("https://app.onrender.com", s.CSRF_TRUSTED_ORIGINS)

    def test_database_url_is_parsed(self):
        s = self.reload_settings(SECRET_KEY="x", DATABASE_URL="postgres://u:p@dbhost:5432/dbname")
        self.assertEqual(s.DATABASES["default"]["HOST"], "dbhost")
        self.assertEqual(s.DATABASES["default"]["NAME"], "dbname")

    def test_proxy_ssl_header_set(self):
        s = self.reload_settings(SECRET_KEY="x", DATABASE_URL="postgres://u:p@h/d")
        self.assertEqual(s.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))

    def test_cookies_are_secure_outside_debug(self):
        s = self.reload_settings(SECRET_KEY="x", DATABASE_URL="postgres://u:p@h/d")
        self.assertTrue(s.SESSION_COOKIE_SECURE)
        self.assertTrue(s.CSRF_COOKIE_SECURE)
        s = self.reload_settings(DEBUG="1", DATABASE_URL="postgres://u:p@h/d")
        self.assertFalse(s.SESSION_COOKIE_SECURE)
