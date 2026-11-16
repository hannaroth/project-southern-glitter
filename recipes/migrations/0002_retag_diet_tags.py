from django.db import migrations

from recipes.diet import derive_diet_tags


# Deliberately uses the current derive_diet_tags, so a deploy re-tags with the latest rules.
def recompute_diet_tags(apps, schema_editor):
    """Re-derive diet_tags for every recipe from its stored category and ingredients."""
    Recipe = apps.get_model("recipes", "Recipe")
    for recipe in Recipe.objects.all().iterator():
        tags = derive_diet_tags(recipe.category, recipe.ingredients)
        if tags != recipe.diet_tags:
            Recipe.objects.filter(pk=recipe.pk).update(diet_tags=tags)


class Migration(migrations.Migration):

    dependencies = [("recipes", "0001_initial")]

    operations = [migrations.RunPython(recompute_diet_tags, migrations.RunPython.noop)]
