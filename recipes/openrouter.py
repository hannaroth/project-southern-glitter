"""Minimal OpenRouter client (standard library only). Call it from server code only."""

import json
import os
import threading
import urllib.error
import urllib.request

API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.5-flash-lite"
TIMEOUT_SECONDS = 20


class OpenRouterError(Exception):
    """OpenRouter could not give us a usable JSON object."""


class InvalidJSONReply(OpenRouterError):
    """The model's reply content was not a JSON object."""


class MissingAPIKey(OpenRouterError):
    """OPENROUTER_API_KEY is not set."""


def _fetch(request, timeout, out):
    """Run the HTTP call in a worker thread and hand the result back through `out`.

    `out` is a fresh dict per call, so a thread that outlives its deadline can only write
    into a dict nobody reads any more. We catch Exception, not BaseException: KeyboardInterrupt
    and SystemExit are not network errors and must not be swallowed. (Signals reach the main
    thread anyway; in a daemon thread they would only be lost.) urlopen is looked up through
    the module on every call so tests can patch it.
    """
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            out["body"] = response.read()
    except Exception as exc:
        out["error"] = exc


def chat_json(messages, *, model=None, timeout=None):
    """Send chat messages and return the reply content parsed as a JSON object (dict).

    `timeout` is in seconds; None means TIMEOUT_SECONDS. It is a hard wall-clock deadline for
    the whole request (DNS, connect, TLS, body), enforced by joining a worker thread.
    """
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
    deadline = TIMEOUT_SECONDS if timeout is None else timeout
    out = {}
    worker = threading.Thread(target=_fetch, args=(request, deadline, out), daemon=True)
    worker.start()
    worker.join(deadline)
    if worker.is_alive():
        # Plain OpenRouterError (not InvalidJSONReply): the caller falls back without a retry.
        raise OpenRouterError("OpenRouter request timed out")
    try:
        if "error" in out:
            raise out["error"]
        payload = json.loads(out["body"].decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        raise OpenRouterError(f"OpenRouter returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OpenRouterError(f"OpenRouter request failed: {type(exc).__name__}") from exc
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("OpenRouter reply had an unexpected format") from exc
    try:
        result = json.loads(content)
    except (ValueError, TypeError) as exc:
        raise InvalidJSONReply("OpenRouter reply was not a JSON object") from exc
    if not isinstance(result, dict):
        raise InvalidJSONReply("OpenRouter reply was not a JSON object")
    return result
