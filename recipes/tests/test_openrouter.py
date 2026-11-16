import json
import os
import urllib.error
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from recipes import openrouter
from recipes.openrouter import InvalidJSONReply, OpenRouterError, chat_json


def fake_response(content):
    body = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
    response = MagicMock()
    response.read.return_value = body
    response.__enter__.return_value = response
    return response


def env(**values):
    base = {k: v for k, v in os.environ.items() if not k.startswith("OPENROUTER_")}
    base.update(values)
    return patch.dict(os.environ, base, clear=True)


class ChatJsonTests(SimpleTestCase):
    def test_missing_key_raises_without_http_call(self):
        with env(), patch("urllib.request.urlopen") as urlopen:
            with self.assertRaises(OpenRouterError):
                chat_json([{"role": "user", "content": "hi"}])
        urlopen.assert_not_called()

    def test_custom_timeout_is_passed_on(self):
        with env(OPENROUTER_API_KEY="test-key"), patch(
            "urllib.request.urlopen", return_value=fake_response("{}")
        ) as urlopen:
            chat_json([{"role": "user", "content": "hi"}], timeout=7.5)
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 7.5)

    def test_request_shape_and_parsing(self):
        with env(OPENROUTER_API_KEY="test-key"), patch(
            "urllib.request.urlopen", return_value=fake_response('{"a": 1}')
        ) as urlopen:
            result = chat_json([{"role": "user", "content": "hi"}])
        self.assertEqual(result, {"a": 1})
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 20)
        body = json.loads(request.data)
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertEqual(body["messages"], [{"role": "user", "content": "hi"}])
        self.assertEqual(body["model"], openrouter.DEFAULT_MODEL)

    def _model_used(self, **kwargs):
        with patch("urllib.request.urlopen", return_value=fake_response("{}")) as urlopen:
            chat_json([], **kwargs)
        return json.loads(urlopen.call_args.args[0].data)["model"]

    def test_model_env_override_and_argument_override(self):
        with env(OPENROUTER_API_KEY="k", OPENROUTER_MODEL="vendor/from-env"):
            self.assertEqual(self._model_used(), "vendor/from-env")
            self.assertEqual(self._model_used(model="vendor/arg"), "vendor/arg")

    def test_bad_json_content(self):
        with env(OPENROUTER_API_KEY="k"), patch(
            "urllib.request.urlopen", return_value=fake_response("not json")
        ):
            with self.assertRaises(InvalidJSONReply):
                chat_json([])

    def test_json_but_not_an_object(self):
        with env(OPENROUTER_API_KEY="k"), patch(
            "urllib.request.urlopen", return_value=fake_response("[1, 2]")
        ):
            with self.assertRaises(InvalidJSONReply):
                chat_json([])

    def test_unexpected_payload_shape(self):
        response = MagicMock()
        response.read.return_value = b'{"error": "nope"}'
        response.__enter__.return_value = response
        with env(OPENROUTER_API_KEY="k"), patch("urllib.request.urlopen", return_value=response):
            with self.assertRaises(OpenRouterError) as ctx:
                chat_json([])
        self.assertNotIsInstance(ctx.exception, InvalidJSONReply)

    def test_http_error(self):
        error = urllib.error.HTTPError("u", 500, "boom", {}, None)
        with env(OPENROUTER_API_KEY="k"), patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(OpenRouterError):
                chat_json([])

    def test_timeout_and_url_error(self):
        for exc in (TimeoutError(), urllib.error.URLError("down")):
            with env(OPENROUTER_API_KEY="k"), patch("urllib.request.urlopen", side_effect=exc):
                with self.assertRaises(OpenRouterError):
                    chat_json([])

    def test_error_message_does_not_contain_key(self):
        error = urllib.error.HTTPError("u", 401, "bad", {}, None)
        with env(OPENROUTER_API_KEY="secret-key-123"), patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(OpenRouterError) as ctx:
                chat_json([])
        self.assertNotIn("secret-key-123", str(ctx.exception))
