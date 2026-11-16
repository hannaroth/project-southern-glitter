from django.test import SimpleTestCase, TestCase

from recipes.diet import course_for_category, derive_diet_tags
from recipes.models import Recipe


def tags(category, *names):
    return derive_diet_tags(category, [{"name": n, "measure": ""} for n in names])


class CourseTests(SimpleTestCase):
    def test_mapping(self):
        self.assertEqual(course_for_category("Starter"), "starter")
        self.assertEqual(course_for_category("Side"), "starter")
        self.assertEqual(course_for_category("Dessert"), "dessert")
        for c in ("Beef", "Vegan", "Seafood", "", None):
            self.assertEqual(course_for_category(c), "main")


class DietTests(SimpleTestCase):
    def test_vegetarian_and_vegan_from_category(self):
        self.assertEqual(tags("Vegetarian", "Eggs"), ["vegetarian"])
        self.assertEqual(tags("Vegan", "Tomato"), ["vegetarian", "vegan"])
        self.assertEqual(tags("Beef", "Beef"), [])

    def test_gluten(self):
        self.assertIn("contains_gluten", tags("Pasta", "Plain Flour"))
        self.assertIn("contains_gluten", tags("Pasta", "Spaghetti"))
        self.assertIn("contains_gluten", tags("Beef", "Soy Sauce"))
        self.assertNotIn("contains_gluten", tags("Beef", "Gluten-Free Flour"))
        self.assertNotIn("contains_gluten", tags("Beef", "Potatoes", "Rice"))

    def test_dairy(self):
        for n in ("Butter", "Whole MILK", "Cheddar Cheese", "Double Cream", "Greek Yogurt"):
            self.assertIn("contains_dairy", tags("Beef", n), n)
        for n in ("Coconut Milk", "Coconut cream", "Almond Milk", "Dairy-Free Butter", "Cocoa Butter"):
            self.assertNotIn("contains_dairy", tags("Beef", n), n)
        self.assertNotIn("contains_dairy", tags("Beef", "Butternut Squash"))

    def test_nuts(self):
        for n in ("Almonds", "Chopped Walnuts", "Pine Nuts", "Peanut Butter", "Hazelnut"):
            self.assertIn("contains_nuts", tags("Beef", n), n)
        for n in ("Nutmeg", "Butternut Squash", "Coconut", "Water Chestnut", "Nut-free Mix"):
            self.assertNotIn("contains_nuts", tags("Beef", n), n)

    def test_peanut_butter_is_not_dairy(self):
        self.assertNotIn("contains_dairy", tags("Beef", "Peanut Butter"))

    def test_empty_ingredients(self):
        self.assertEqual(derive_diet_tags("Beef", []), [])
        self.assertEqual(derive_diet_tags(None, None), [])


class DerivedVegetarianTests(SimpleTestCase):
    def test_starter_and_dessert_from_ingredients(self):
        self.assertIn("vegetarian", tags("Starter", "Tomato", "Basil", "Olive Oil"))
        self.assertIn("vegetarian", tags("Dessert", "Plain Flour", "Sugar", "Butter"))
        self.assertIn("vegetarian", tags("Side", "Potatoes"))
        self.assertIn("vegetarian", tags("Pasta", "Spaghetti", "Tomato"))

    def test_meat_and_fish_block(self):
        for n in (
            "Chicken Breast", "Minced Beef", "Bacon", "Ham", "Pork Sausages", "Prawns", "Salmon",
            "Anchovies", "Gelatine Leafs", "Fish Sauce", "Oyster Sauce", "Worcestershire Sauce",
            "Beef Stock", "Chicken Stock", "Stock Cube", "Lard", "Suet", "Chorizo", "Mussels",
            "Calamari", "Kidney", "Duck Legs",
        ):
            self.assertNotIn("vegetarian", tags("Starter", "Tomato", n), n)
            self.assertNotIn("vegan", tags("Starter", "Tomato", n), n)

    def test_false_hits_do_not_block(self):
        for n in (
            "Vegetable Stock", "Hamburger Buns", "Eggplant", "Butternut Squash", "Coconut Milk",
            "Kidney Beans", "Veggie Sausages", "Peanut Butter", "Shamrock",
        ):
            self.assertIn("vegetarian", tags("Starter", "Tomato", n), n)

    def test_mixed_marker_names_are_meat(self):
        for n in (
            "Chicken and vegetable stock", "Beef and Vegetable Broth", "Vegetable and Chicken Stock",
            "Chicken Stock (vegetable)", "Veggie Sausages with Pork", "Vegan Gelatine and Gelatine",
        ):
            self.assertEqual(tags("Starter", n), [], n)
            self.assertNotIn("vegetarian", tags("Starter", "Tomato", n), n)

    def test_new_meat_fish_keywords_block(self):
        for n in (
            "Black Pudding", "Blood Pudding", "Dashi", "Bonito Flakes", "Katsuobushi", "Caviar",
            "Roe", "Trout", "Sea Bass", "Bass", "Halibut", "Herring", "Eel", "Tilapia",
            "Snapper", "Swordfish", "Monkfish", "Mahi Mahi", "Kippers", "Cockles", "Whelks",
            "Langoustines", "Crevettes", "Surimi", "Fishcakes", "Cuttlefish", "Escargot",
            "Snails", "Steak", "Ribeye", "Sirloin", "Tenderloin", "Ribs", "Short Ribs",
            "Brisket", "Rabbit", "Pheasant", "Quail", "Pigeon", "Bresaola", "Mortadella",
            "Hot Dogs", "Frankfurters", "Lardons", "Guanciale", "Nduja", "Pastrami", "Spam",
            "Meatballs", "Jerky", "Wings", "Drumsticks", "Poultry", "Bone Marrow",
            "Marrow Bones", "Foie Gras", "Tripe", "Tongue", "Offal", "Sweetbreads", "Haggis",
            "Pate", "Pâté", "Tallow", "Schmaltz", "Crackling", "Oxo Cube", "Bovril", "Gravy",
            "Nam Pla", "Shrimp Paste", "Red Curry Paste", "Thai Green Curry Paste",
            "Caesar Dressing", "XO Sauce",
        ):
            self.assertNotIn("vegetarian", tags("Starter", "Tomato", n), n)
            self.assertNotIn("vegan", tags("Starter", "Tomato", n), n)

    def test_meat_free_phrases_alone_stay_vegan(self):
        for n in (
            "Vegetable Stock", "Vegetable Stock Cube", "Vegetable Broth", "Vegetable Bouillon",
            "Veggie Stock", "Vegan Stock", "Veggie Sausages", "Vegetarian Sausage",
            "Vegan Sausages", "Vegetarian Mince", "Vegan Mince", "Meat-free Mince",
            "Plant-based Mince", "Vegetable Suet", "Vegetarian Suet", "Vegetarian Gelatine",
            "Vegan Gelatine", "Vegetarian Worcestershire Sauce", "Vegan Fish Sauce",
            "Vegan Curry Paste", "Vegetarian Curry Paste",
        ):
            self.assertEqual(tags("Starter", n), ["vegetarian", "vegan"], n)

    def test_false_positive_guards(self):
        for n in (
            "Rice Pudding", "Christmas Pudding", "Pudding Rice", "Marrow", "Kidney Beans",
            "Vegetable Stock", "Veggie Sausages", "Hamburger Buns", "Eggplant",
            "Butternut Squash", "Sea Salt", "Coconut", "Chocolate", "Ribbons of Courgette",
        ):
            self.assertIn("vegetarian", tags("Starter", "Tomato", n), n)

    def test_meat_category_never_vegetarian(self):
        for c in ("Beef", "Chicken", "Lamb", "Pork", "Seafood", "Goat"):
            self.assertNotIn("vegetarian", tags(c, "Tomato", "Basil"), c)

    def test_no_ingredients_is_not_vegetarian(self):
        self.assertEqual(tags("Starter"), [])

    def test_vegan_rules(self):
        self.assertEqual(tags("Starter", "Tomato", "Olive Oil"), ["vegetarian", "vegan"])
        self.assertEqual(tags("Starter", "Tomato", "Eggs"), ["vegetarian"])
        self.assertEqual(tags("Starter", "Tomato", "Egg Yolks"), ["vegetarian"])
        self.assertEqual(tags("Dessert", "Oats", "Honey"), ["vegetarian", "contains_gluten"])
        self.assertEqual(tags("Starter", "Tomato", "Mayonnaise"), ["vegetarian"])
        self.assertEqual(tags("Starter", "Tomato", "Feta"), ["vegetarian", "contains_dairy"])
        self.assertEqual(tags("Starter", "Tomato", "Ghee"), ["vegetarian", "contains_dairy"])

    def test_category_vegan_still_vegan(self):
        self.assertEqual(tags("Vegan", "Eggs"), ["vegetarian", "vegan"])
        self.assertEqual(tags("Vegetarian", "Eggs"), ["vegetarian"])

    def test_vegan_implies_vegetarian(self):
        for cat, names in (("Vegan", ["x"]), ("Starter", ["Tomato"]), ("Dessert", ["Sugar"])):
            t = tags(cat, *names)
            if "vegan" in t:
                self.assertIn("vegetarian", t)


class RetagMigrationTests(TestCase):
    def test_recompute_updates_stored_tags(self):
        from importlib import import_module

        from django.apps import apps

        migration = import_module("recipes.migrations.0002_retag_diet_tags")
        starter = Recipe.objects.create(
            external_id="s", title="S", category="Starter", course="starter",
            ingredients=[{"name": "Tomato", "measure": "1"}], instructions="x", diet_tags=[],
        )
        meaty = Recipe.objects.create(
            external_id="m", title="M", category="Starter", course="starter",
            ingredients=[{"name": "Bacon", "measure": "1"}], instructions="x",
            diet_tags=["vegetarian"],
        )
        migration.recompute_diet_tags(apps, None)
        starter.refresh_from_db()
        meaty.refresh_from_db()
        self.assertEqual(starter.diet_tags, ["vegetarian", "vegan"])
        self.assertEqual(meaty.diet_tags, [])
