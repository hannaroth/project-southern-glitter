from django.contrib import admin

from .models import Dinner


@admin.register(Dinner)
class DinnerAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "theme", "team_cap", "signup_deadline")
    ordering = ("date",)
    fieldsets = (
        ("Basics", {"fields": ("title", "theme", "date")}),
        ("Course times", {"fields": ("starter_time", "main_time", "dessert_time")}),
        ("After-party", {"fields": ("after_party_name", "after_party_address")}),
        ("Sign-ups", {"fields": ("team_cap", "signup_deadline")}),
    )
