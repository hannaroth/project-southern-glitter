import secrets

from django.conf import settings
from django.db import models

DIET_CHOICES = [
    ("vegetarian", "Vegetarian"),
    ("vegan", "Vegan"),
    ("gluten_free", "Gluten-free"),
    ("dairy_free", "Dairy-free"),
    ("nut_allergy", "Nut allergy"),
]


def new_invite_token():
    return secrets.token_urlsafe(32)


class Team(models.Model):
    """Two people signed up for one dinner. Contract: docs/sprint-2-plan.md, section 5.3."""

    class Status(models.TextChoices):
        REGISTERED = "registered"  # holds one of the dinner's team_cap spots
        WAITLISTED = "waitlisted"
        CANCELLED = "cancelled"

    class Course(models.TextChoices):
        STARTER = "starter"
        MAIN = "main"
        DESSERT = "dessert"
        NO_PREFERENCE = "no_preference", "No preference"

    dinner = models.ForeignKey("dinners.Dinner", on_delete=models.CASCADE, related_name="teams")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_teams"
    )
    partner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="partner_teams",
    )
    address = models.CharField(max_length=255)
    dietary_restrictions = models.JSONField(default=list, blank=True)  # keys from DIET_CHOICES
    dietary_notes = models.CharField(max_length=255, blank=True)  # free text
    preferred_course = models.CharField(
        max_length=20, choices=Course.choices, default=Course.NO_PREFERENCE
    )
    invite_token = models.CharField(max_length=64, unique=True, default=new_invite_token)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REGISTERED)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]  # sign-up order

    def __str__(self):
        return f"{self.creator.display_name} – {self.dinner.title}"

    @property
    def is_complete(self):
        return self.partner_id is not None

    def is_member(self, user):
        return user.is_authenticated and user.pk in (self.creator_id, self.partner_id)

    def dietary_labels(self):
        labels = dict(DIET_CHOICES)
        return [labels.get(key, key) for key in self.dietary_restrictions]
