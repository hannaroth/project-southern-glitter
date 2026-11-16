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


NOT_VEGETARIAN_NAMES = (
    # Verifier rounds 1 and 2
    "Chicken and vegetable stock", "Beef and Vegetable Broth", "Vegetable and Chicken Stock",
    "Chicken Stock (vegetable)", "Veggie Sausages with Pork", "Vegetable Stock with Chicken",
    "Chicken & Vegetable Stock Cube", "Rendang Paste", "Red Curry Paste", "Black Pudding", "Dashi",
    "Bonito Flakes", "Caviar", "Pollock", "Plaice", "Scampi", "Crayfish", "Sushi", "Bratwurst",
    "Kielbasa", "Schnitzel", "Wild Boar", "Frog Legs", "Speck", "Confit", "Terrine", "Burger",
    "Nuggets", "Consomme", "Bisque", "Isinglass", "Rennet", "Collagen", "Cochineal",
    "Marrowbone", "Gravy", "Stock", "Stock Cube", "Gelatine Leafs", "Marshmallows", "Jelly",
    "Worcestershire Sauce", "Fish Sauce", "Caesar Dressing", "XO Sauce", "Zorbo Paste", "Zorbo",
    # Earlier cases
    "Chicken Breast", "Minced Beef", "Bacon", "Ham", "Pork Sausages", "Prawns", "Salmon",
    "Anchovies", "Oyster Sauce", "Beef Stock", "Chicken Stock", "Lard", "Suet", "Chorizo",
    "Mussels", "Calamari", "Kidney", "Duck Legs", "Blood Pudding", "Katsuobushi", "Roe", "Trout",
    "Sea Bass", "Halibut", "Herring", "Eel", "Surimi", "Steak", "Brisket", "Rabbit", "Pate",
    "Foie Gras", "Tripe", "Haggis", "Tallow", "Schmaltz", "Oxo Cube", "Bovril", "Nam Pla",
    "Shrimp Paste", "Thai Green Curry Paste", "Vegan Gelatine and Gelatine", "Rice Pudding",
    "Marrow", "Vegetarian Worcestershire Sauce", "Vegan Curry Paste", "Vegan Fish Sauce",
)


class DerivedVegetarianTests(SimpleTestCase):
    def test_every_risky_name_blocks_alone_and_with_others(self):
        for category in ("Miscellaneous", "Dessert", "Starter"):
            for n in NOT_VEGETARIAN_NAMES:
                self.assertEqual(tags(category, n), [], (category, n))
                for other in (["Tomato"], ["Plain Flour", "Caster Sugar"]):
                    t = tags(category, *other, n)
                    self.assertNotIn("vegetarian", t, (category, n))
                    self.assertNotIn("vegan", t, (category, n))

    def test_known_vegetarian_single_ingredients(self):
        for n in (
            "Vegetable Stock", "Veggie Sausages", "Kidney Beans", "Butternut Squash", "Eggplant",
            "Mushrooms", "Tofu", "Coconut Milk", "Nutmeg", "Sea Salt",
            "Peanut Butter", "Vegetable Stock Cube", "Vegetarian Mince", "Soy Sauce",
            "Tomato Puree", "Golden Syrup", "Double Cream", "Free-range Eggs", "Cherry Tomatoes",
            "Extra Virgin Olive Oil", "Basmati Rice", "Chickpeas", "Spinach", "Feta",
            "Red Onions", "Garlic Clove", "Lemon Juice", "Coriander Leaves", "Ground Cumin",
            "Strawberry Jam", "Blackberries", "Plain Flour", "Unsalted Butter", "Dark Chocolate",
        ):
            self.assertIn("vegetarian", tags("Miscellaneous", n), n)

    def test_unknown_word_blocks(self):
        self.assertNotIn("vegetarian", tags("Starter", "Tomato", "Zorbo"))
        self.assertNotIn("vegetarian", tags("Starter", "Tomato", "Tomato Zorbo"))

    def test_normalisation(self):
        self.assertIn("vegetarian", tags("Starter", "Free-Range EGGS", "Salt/Pepper", "Oil, Olive"))
        self.assertIn("vegetarian", tags("Starter", "Vegetable-Stock"))
        self.assertIn("vegetarian", tags("Starter", "Tomatoes (tinned)", "Berries"))
        self.assertNotIn("vegetarian", tags("Starter", "Chicken/Vegetable Stock"))

    def test_realistic_vegetarian_recipes(self):
        sponge = ("Plain Flour", "Caster Sugar", "Unsalted Butter", "Free-range Eggs",
                  "Baking Powder", "Vanilla Extract", "Strawberry Jam", "Double Cream")
        bruschetta = ("Ciabatta", "Cherry Tomatoes", "Garlic Clove", "Basil Leaves",
                      "Extra Virgin Olive Oil", "Balsamic Vinegar", "Sea Salt", "Black Pepper")
        hummus = ("Chickpeas", "Tahini", "Lemon Juice", "Garlic Clove", "Olive Oil", "Ground Cumin",
                  "Salt", "Water", "Paprika")
        mousse = ("Dark Chocolate", "Eggs", "Caster Sugar", "Double Cream")
        veg_side = ("Carrots", "Parsnips", "Red Onions", "Courgettes", "Olive Oil", "Thyme",
                    "Rosemary", "Sea Salt", "Black Pepper")
        self.assertEqual(tags("Dessert", *sponge), ["vegetarian", "contains_gluten", "contains_dairy"])
        self.assertEqual(tags("Dessert", *mousse), ["vegetarian", "contains_dairy"])
        self.assertEqual(tags("Starter", *bruschetta), ["vegetarian", "vegan"])
        self.assertEqual(tags("Starter", *hummus), ["vegetarian", "vegan"])
        self.assertEqual(tags("Side", *veg_side), ["vegetarian", "vegan"])

    def test_veto_still_applies_with_known_words(self):
        # "Rendang" is on the meat list; every word of "Rendang Spice" would otherwise be unknown anyway.
        self.assertNotIn("vegetarian", tags("Starter", "Tomato", "Rendang"))
        self.assertNotIn("vegetarian", tags("Starter", "Tomato", "Chicken"))

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
        self.assertEqual(tags("Starter", "Tomato", "Coconut Milk"), ["vegetarian", "vegan"])
        self.assertEqual(tags("Starter", "Tomato", "Puff Pastry"), ["vegetarian", "contains_gluten"])
        self.assertEqual(tags("Starter", "Tomato", "Milk Chocolate"), ["vegetarian", "contains_dairy"])
        self.assertEqual(tags("Starter", "Tomato", "White Chocolate"), ["vegetarian"])

    def test_category_rules_unchanged(self):
        self.assertEqual(tags("Vegan", "Eggs"), ["vegetarian", "vegan"])
        self.assertEqual(tags("Vegetarian", "Eggs"), ["vegetarian"])
        self.assertEqual(tags("Vegetarian", "Zorbo Paste"), ["vegetarian"])
        self.assertEqual(tags("Vegan", "Zorbo Paste"), ["vegetarian", "vegan"])

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
