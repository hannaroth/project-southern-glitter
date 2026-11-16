from django.contrib import admin

from .models import Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("dinner", "creator", "partner", "status", "created_at")
    list_filter = ("dinner", "status")
    search_fields = ("creator__email", "partner__email", "address")
    readonly_fields = ("invite_token", "created_at")
