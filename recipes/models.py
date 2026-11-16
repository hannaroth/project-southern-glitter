from django.db import models


class Recipe(models.Model):
    source = models.CharField(max_length=30, default="themealdb")
    external_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    cuisine = models.CharField(max_length=100, blank=True)  # TheMealDB "strArea", e.g. "Italian"
    category = models.CharField(max_length=100, blank=True)  # TheMealDB "strCategory", e.g. "Dessert"
    course = models.CharField(max_length=20)  # "starter" | "main" | "dessert" (derived)
    ingredients = models.JSONField(default=list)  # [{"name": "...", "measure": "..."}]
    instructions = models.TextField()
    source_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    diet_tags = models.JSONField(default=list)  # derived, see recipes/diet.py
    imported_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
