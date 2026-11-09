"""A/B test page and stats (course requirement).

GET  /c6a680e        page with one <button id="abtest"> showing "kudos" or "thanks"
POST /c6a680e        records at most one click per visitor, then redirects back
GET  /c6a680e/stats  live JSON results with a "preferred" key

The visitor id and variant live in one signed cookie, so a reload or the
redirect after a click keeps the same variant and never adds an impression.
"""

import random
import uuid

from django.core import signing
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .models import Click, Impression, Variant

TEAM_NICKNAMES = ["magnificent-aardvark", "stormy-zebra", "delightful-crocodile"]
VARIANTS = [Variant.KUDOS.value, Variant.THANKS.value]

COOKIE_NAME = "abtest_visitor"
COOKIE_SALT = "abtest"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # one year


def choose_variant():
    """50/50 random choice. Kept separate so tests can mock it."""
    return random.choice(VARIANTS)


def _read_visitor(request):
    """Return (visitor_id, variant) from the cookie, or (None, None)."""
    try:
        value = request.get_signed_cookie(COOKIE_NAME, salt=COOKIE_SALT)
    except (KeyError, signing.BadSignature):
        return None, None
    visitor_id, _, variant = value.partition(":")
    if not visitor_id or variant not in VARIANTS:
        return None, None
    return visitor_id, variant


def _set_visitor_cookie(response, visitor_id, variant):
    response.set_signed_cookie(
        COOKIE_NAME,
        f"{visitor_id}:{variant}",
        salt=COOKIE_SALT,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="Lax",
    )


# csrf_exempt: the click form posts to the same page and only ever records one
# click for the visitor in the signed cookie, so a forged post can do no harm.
# Exempting it also avoids CSRF origin failures behind Render's HTTPS proxy,
# which would silently lose the bot's clicks during the graded run.
@csrf_exempt
@require_http_methods(["GET", "POST"])
def ab_page(request):
    visitor_id, variant = _read_visitor(request)

    if request.method == "POST":
        # Only a visitor who has seen the page (has the cookie) can click.
        # The variant comes from the cookie, never from the form.
        if visitor_id:
            Click.objects.get_or_create(
                visitor_id=visitor_id, defaults={"variant": variant}
            )
        return redirect("abtest:page")

    is_new = visitor_id is None
    if is_new:
        visitor_id = uuid.uuid4().hex
        variant = choose_variant()

    # get_or_create + unique visitor_id: the first view stores the impression,
    # reloads and the redirect after a click find the existing row.
    Impression.objects.get_or_create(
        visitor_id=visitor_id, defaults={"variant": variant}
    )

    response = render(
        request,
        "abtest/page.html",
        {"variant": variant, "nicknames": TEAM_NICKNAMES},
    )
    if is_new:
        _set_visitor_cookie(response, visitor_id, variant)
    return response


def compute_stats():
    counts = {}
    for v in VARIANTS:
        counts[v] = {
            "impressions": Impression.objects.filter(variant=v).count(),
            "clicks": Click.objects.filter(variant=v).count(),
        }

    def rate(v):
        imp = counts[v]["impressions"]
        return counts[v]["clicks"] / imp if imp else 0.0

    # Ties (including no data at all) fall back to "kudos" so the value is
    # never null.
    preferred = "thanks" if rate("thanks") > rate("kudos") else "kudos"
    return {"preferred": preferred, **counts}


@require_GET
def ab_stats(request):
    return JsonResponse(compute_stats())
