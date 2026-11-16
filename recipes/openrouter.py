"""Minimal OpenRouter client (standard library only). Call it from server code only."""

import json
import os
import urllib.error
import urllib.request

API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.5-flash-lite"
TIMEOUT_SECONDS = 20


class OpenRouterError(Exception):
    """OpenRouter could not give us a usable JSON object."""


class MissingAPIKey(OpenRouterError):
    """OPENROUTER_API_KEY is not set."""


def chat_json(messages, *, model=None):
    """Send chat messages and return the reply content parsed as a JSON object (dict)."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise MissingAPIKey("OPENROUTER_API_KEY is not set")
    model = model or os.environ.get("OPENROUTER_MODEL", "").strip() or DEFAULT_MODEL
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        result = json.loads(content)
    except urllib.error.HTTPError as exc:
        raise OpenRouterError(f"OpenRouter returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OpenRouterError(f"OpenRouter request failed: {type(exc).__name__}") from exc
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("OpenRouter reply was not a JSON object") from exc
    if not isinstance(result, dict):
        raise OpenRouterError("OpenRouter reply was not a JSON object")
    return result
