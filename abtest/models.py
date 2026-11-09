"""Impressions and clicks for the course A/B test at /c6a680e.

Each visitor gets a random id (stored in a signed cookie). The unique
constraint on visitor_id is what guarantees "one impression per visitor"
and "at most one click per visitor", even if two requests race.
"""

from django.db import models


class Variant(models.TextChoices):
    KUDOS = "kudos", "kudos"
    THANKS = "thanks", "thanks"


class Impression(models.Model):
    visitor_id = models.CharField(max_length=64, unique=True)
    variant = models.CharField(max_length=6, choices=Variant.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"impression {self.variant} {self.visitor_id}"


class Click(models.Model):
    visitor_id = models.CharField(max_length=64, unique=True)
    variant = models.CharField(max_length=6, choices=Variant.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"click {self.variant} {self.visitor_id}"
