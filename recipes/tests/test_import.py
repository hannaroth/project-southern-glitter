import json
import os
import urllib.error
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from recipes.management.commands import import_recipes
from recipes.models import Recipe

CATEGORIES = {"categories": [{"strCategory": "Dessert"}, {"strCategory": "Vegan"}]}
LISTINGS = {
    "Dessert": {"meals": [{"idMeal": "1"}, {"idMeal": "2"}]},
    "Vegan": {"meals": [{"idMeal": "3"}]},
}


def meal(id_, title, category, ingredients, **extra):
    data = {
        "idMeal": id_,
        "strMeal": title,
        "strCategory": category,
        "strArea": "Italian",
        "strInstructions": "Cook it.",
        "strSource": "",
        "strMealThumb": f"https://img.example.com/{id_}.jpg",
    }
    for i in range(1, 21):
        data[f"strIngredient{i}"] = ""
        data[f"strMeasure{i}"] = ""
    for i, (name, measure) in enumerate(ingredients, start=1):
        data[f"strIngredient{i}"] = name
        data[f"strMeasure{i}"] = measure
    data.update(extra)
    return {"meals": [data]}


MEALS = {
    "1": meal("1", "Cake", "Dessert", [("Flour", "200g"), ("Butter", "100g")], strSource="https://src.example.com/cake"),
    "2": meal("2", "Pie", "Dessert", [("Walnuts", "50g"), (" ", " ")]),
    "3": meal("3", "Soup", "Vegan", [("Carrot", "2")]),
}


class FakeHttp:
    """Stands in for urllib.request.urlopen; records URLs and serves canned JSON."""

    def __init__(self, fail=(), categories=CATEGORIES, meals=None):
        self.urls = []
        self.fail = fail
        self.categories = categories
        self.meals = MEALS if meals is None else meals

    def __call__(self, url, timeout=None):
        self.urls.append(url)
        self.timeout = timeout
        for bad in self.fail:
            if bad in url:
                raise urllib.error.URLError("boom")
        if "categories.php" in url:
            payload = self.categories
        elif "filter.php?c=" in url:
            payload = LISTINGS[url.split("c=")[1]]
        else:
            payload = self.meals[url.split("i=")[1]]
        return _Resp(json.dumps(payload))


class _Resp:
    def __init__(self, text):
        self.text = text

    def read(self):
        return self.text.encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def run(fake, *args):
    out, err = StringIO(), StringIO()
    with patch("urllib.request.urlopen", fake), patch.object(import_recipes, "PAUSE_SECONDS", 0):
        call_command("import_recipes", *args, stdout=out, stderr=err)
    return out.getvalue()


class ImportTests(TestCase):
    def test_import_creates_recipes(self):
        fake = FakeHttp()
        out = run(fake)
        self.assertEqual(Recipe.objects.count(), 3)
        self.assertIn("created 3", out)
        self.assertEqual(fake.timeout, 10)
        cake = Recipe.objects.get(external_id="1")
        self.assertEqual(cake.source, "themealdb")
        self.assertEqual(cake.title, "Cake")
        self.assertEqual(cake.cuisine, "Italian")
        self.assertEqual(cake.category, "Dessert")
        self.assertEqual(cake.course, "dessert")
        self.assertEqual(cake.ingredients, [{"name": "Flour", "measure": "200g"}, {"name": "Butter", "measure": "100g"}])
        self.assertEqual(cake.source_url, "https://src.example.com/cake")
        self.assertEqual(cake.image_url, "https://img.example.com/1.jpg")
        self.assertEqual(cake.diet_tags, ["vegetarian", "contains_gluten", "contains_dairy"])
        pie = Recipe.objects.get(external_id="2")
        self.assertEqual(pie.source_url, "https://www.themealdb.com/meal/2")
        self.assertEqual(pie.ingredients, [{"name": "Walnuts", "measure": "50g"}])
        self.assertEqual(pie.diet_tags, ["vegetarian", "vegan", "contains_nuts"])
        soup = Recipe.objects.get(external_id="3")
        self.assertEqual(soup.course, "main")
        self.assertEqual(soup.diet_tags, ["vegetarian", "vegan"])

    def test_second_run_updates_without_duplicates(self):
        run(FakeHttp())
        changed = dict(MEALS)
        changed["1"] = meal("1", "Better Cake", "Dessert", [("Flour", "1")])
        out = run(FakeHttp(meals=changed))
        self.assertEqual(Recipe.objects.count(), 3)
        self.assertIn("updated 3", out)
        self.assertEqual(Recipe.objects.get(external_id="1").title, "Better Cake")

    def test_if_empty_skips_when_recipes_exist(self):
        Recipe.objects.create(external_id="x", title="T", course="main", instructions="i")
        fake = FakeHttp()
        run(fake, "--if-empty")
        self.assertEqual(fake.urls, [])
        self.assertEqual(Recipe.objects.count(), 1)

    def test_if_empty_imports_when_empty(self):
        run(FakeHttp(), "--if-empty")
        self.assertEqual(Recipe.objects.count(), 3)

    def test_failing_meal_is_skipped(self):
        out = run(FakeHttp(fail=("lookup.php?i=2",)))
        self.assertEqual(sorted(Recipe.objects.values_list("external_id", flat=True)), ["1", "3"])
        self.assertIn("skipped 1", out)

    def test_null_meals_and_bad_json_are_skipped(self):
        meals = dict(MEALS)
        meals["2"] = {"meals": None}
        fake = FakeHttp(meals=meals)
        original = fake.__call__

        def call(url, timeout=None):
            if "lookup.php?i=3" in url:
                return _Resp("not json")
            return original(url, timeout)

        out = run(call)
        self.assertEqual(list(Recipe.objects.values_list("external_id", flat=True)), ["1"])
        self.assertIn("skipped 2", out)

    def test_failing_category_is_skipped(self):
        out = run(FakeHttp(fail=("filter.php?c=Dessert",)))
        self.assertEqual(list(Recipe.objects.values_list("external_id", flat=True)), ["3"])
        self.assertIn("skipped 1", out)

    def test_failing_category_list_does_not_raise(self):
        run(FakeHttp(fail=("categories.php",)))
        self.assertEqual(Recipe.objects.count(), 0)

    def test_key_default_and_env(self):
        env = {k: v for k, v in os.environ.items() if k != "THEMEALDB_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            fake = FakeHttp()
            run(fake)
        self.assertEqual(fake.urls[0], "https://www.themealdb.com/api/json/v1/1/categories.php")
        with patch.dict(os.environ, {"THEMEALDB_API_KEY": "secret-test-key"}):
            fake = FakeHttp()
            run(fake)
        self.assertTrue(all("/v1/secret-test-key/" in u for u in fake.urls))
        self.assertIn("https://www.themealdb.com/api/json/v1/secret-test-key/filter.php?c=Dessert", fake.urls)
        self.assertIn("https://www.themealdb.com/api/json/v1/secret-test-key/lookup.php?i=1", fake.urls)


class AdminTests(TestCase):
    def test_admin_list_for_staff(self):
        User = get_user_model()
        staff = User.objects.create_superuser(email="staff@example.com", password="pw-throwaway-1")
        Recipe.objects.create(external_id="1", title="Cake", course="dessert", instructions="i")
        self.client.force_login(staff)
        response = self.client.get("/admin/recipes/recipe/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recipes from TheMealDB")
        self.assertContains(response, "Check the ingredients yourself for allergies.")
        self.assertContains(response, "Cake")


class BuildScriptTests(TestCase):
    def test_import_is_guarded_and_between_migrate_and_seed(self):
        text = (Path(__file__).resolve().parents[2] / "build.sh").read_text()
        line = 'python manage.py import_recipes --if-empty || echo "Recipe import failed; continuing"'
        self.assertIn(line, text)
        self.assertLess(text.index("manage.py migrate"), text.index(line))
        self.assertLess(text.index(line), text.index("manage.py seed"))
