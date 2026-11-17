from django.contrib import admin

from .models import Recipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "cuisine", "category")
    list_filter = ("course", "category", "cuisine")
    search_fields = ("title",)
    ordering = ("title",)
