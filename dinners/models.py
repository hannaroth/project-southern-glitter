from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Dinner(models.Model):
    title = models.CharField(max_length=200)
    theme = models.CharField(max_length=200)
    date = models.DateField()
    starter_time = models.TimeField()
    main_time = models.TimeField()
    dessert_time = models.TimeField()
    after_party_name = models.CharField(max_length=200)
    after_party_address = models.CharField(max_length=255)
    team_cap = models.PositiveIntegerField()
    signup_deadline = models.DateTimeField()

    class Meta:
        ordering = ["date", "title"]

    def __str__(self):
        return f"{self.title} ({self.date:%Y-%m-%d})"

    def clean(self):
        super().clean()
        errors = {}
        times = [self.starter_time, self.main_time, self.dessert_time]
        if None not in times:
            if not self.starter_time < self.main_time:
                errors["main_time"] = "The main course must start after the starter."
            if not self.main_time < self.dessert_time:
                errors["dessert_time"] = "The dessert must start after the main course."
        if self.signup_deadline is not None and self.date is not None:
            deadline_day = timezone.localtime(self.signup_deadline).date()
            if not deadline_day < self.date:
                errors["signup_deadline"] = "The sign-up deadline must be before the dinner date."
        if errors:
            raise ValidationError(errors)
