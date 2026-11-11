from django.db import models


class Dinner(models.Model):
    title = models.CharField(max_length=200)
    theme = models.CharField(max_length=200)
    date = models.DateField()
    after_party_place = models.CharField(max_length=200)
    team_cap = models.PositiveIntegerField()

    class Meta:
        ordering = ["date", "title"]

    def __str__(self):
        return f"{self.title} ({self.date:%Y-%m-%d})"
