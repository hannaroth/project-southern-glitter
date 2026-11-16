from django.test import SimpleTestCase

from recipes.diet import course_for_category, derive_diet_tags


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
        self.assertEqual(tags("Vegetarian", "Tomato"), ["vegetarian"])
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
