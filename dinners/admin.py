from django.contrib import admin

from .models import Dinner


@admin.register(Dinner)
class DinnerAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "theme", "team_cap")
    ordering = ("date",)
