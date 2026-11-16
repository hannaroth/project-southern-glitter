"""Import recipes from TheMealDB into our own table. Safe to run twice; never fails a deploy."""

import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand

from recipes.diet import course_for_category, derive_diet_tags
from recipes.models import Recipe

logger = logging.getLogger(__name__)

BASE_URL = "https://www.themealdb.com/api/json/v1"
TIMEOUT_SECONDS = 10
PAUSE_SECONDS = 0.3  # patched to 0 in tests
MAX_INGREDIENTS = 20


def _pause():
    if PAUSE_SECONDS:
        time.sleep(PAUSE_SECONDS)


def _get_json(url):
    with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_ingredients(meal):
    items = []
    for i in range(1, MAX_INGREDIENTS + 1):
        name = (meal.get(f"strIngredient{i}") or "").strip()
        if not name:
            continue
        items.append({"name": name, "measure": (meal.get(f"strMeasure{i}") or "").strip()})
    return items


def meal_to_fields(meal):
    category = (meal.get("strCategory") or "").strip()
    ingredients = parse_ingredients(meal)
    external_id = str(meal["idMeal"])
    return {
        "title": (meal.get("strMeal") or "").strip()[:200],
        "cuisine": (meal.get("strArea") or "").strip()[:100],
        "category": category[:100],
        "course": course_for_category(category),
        "ingredients": ingredients,
        "instructions": (meal.get("strInstructions") or "").strip(),
        "source_url": (meal.get("strSource") or "").strip() or f"https://www.themealdb.com/meal/{external_id}",
        "image_url": (meal.get("strMealThumb") or "").strip(),
        "diet_tags": derive_diet_tags(category, ingredients),
    }


class Command(BaseCommand):
    help = "Import recipes from TheMealDB (upsert by external_id)."

    def add_arguments(self, parser):
        parser.add_argument("--if-empty", action="store_true", help="Do nothing if any recipe already exists.")

    def handle(self, *args, **options):
        if options["if_empty"] and Recipe.objects.exists():
            self.stdout.write("Recipes already exist; skipping import.")
            return

        key = os.environ.get("THEMEALDB_API_KEY") or "1"
        base = f"{BASE_URL}/{key}"
        created = updated = skipped = 0

        try:
            categories = _get_json(f"{base}/categories.php").get("categories") or []
            names = [c["strCategory"] for c in categories]
        except Exception as exc:  # never fail the deploy
            logger.error("Could not list TheMealDB categories: %s", exc)
            self.stderr.write(f"Could not list categories: {exc}")
            self.stdout.write("Imported 0 recipes (created 0, updated 0, skipped 0).")
            return

        for name in names:
            _pause()
            try:
                listing = _get_json(f"{base}/filter.php?c={urllib.parse.quote(name)}").get("meals") or []
                ids = [m["idMeal"] for m in listing]
            except Exception as exc:
                logger.warning("Skipping category %s: %s", name, exc)
                skipped += 1
                continue
            for meal_id in ids:
                _pause()
                try:
                    meals = _get_json(f"{base}/lookup.php?i={urllib.parse.quote(str(meal_id))}").get("meals") or []
                    if not meals:
                        raise ValueError("no meal returned")
                    fields = meal_to_fields(meals[0])
                    _, was_created = Recipe.objects.update_or_create(
                        external_id=str(meals[0]["idMeal"]), defaults=fields
                    )
                except Exception as exc:
                    logger.warning("Skipping meal %s: %s", meal_id, exc)
                    skipped += 1
                    continue
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            f"Imported {created + updated} recipes (created {created}, updated {updated}, skipped {skipped})."
        )
