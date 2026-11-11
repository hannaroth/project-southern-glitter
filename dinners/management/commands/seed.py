"""Create the demo data and grader accounts. Safe to run any number of times.

Passwords come from SEED_ADMIN_PASSWORD and SEED_MEMBER_PASSWORD, never from the repo.
On a re-run, accounts (found by email) get the env password and the seeded role flags
again; dinners (found by title) keep a date that is still today or later and are moved
to a new upcoming date once theirs has passed. Nothing is duplicated.
"""

import os
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from dinners.models import Dinner

ACCOUNTS = [
    {
        "email": "admin@example.com",
        "env": "SEED_ADMIN_PASSWORD",
        "first_name": "Ada",
        "last_name": "Admin",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "member@example.com",
        "env": "SEED_MEMBER_PASSWORD",
        "first_name": "Max",
        "last_name": "Member",
        "is_staff": False,
        "is_superuser": False,
    },
]

# (title, theme, after-party place, team cap, days after the first dinner date)
DINNERS = [
    ("Around the World", "Each course from a different country", "After-party: to be announced downtown", 12, 0),
    ("Through the Eras", "Each course from a different decade", "Student lounge (demo)", 12, 14),
    ("No Theme, Just Dinner", "Cook whatever you love", "After-party: place to be announced", 9, 28),
]


def first_dinner_date(today):
    """The next Saturday that is at least 7 days away."""
    earliest = today + timedelta(days=7)
    return earliest + timedelta(days=(5 - earliest.weekday()) % 7)


class Command(BaseCommand):
    help = "Create the grader accounts and three upcoming demo dinners (safe to run twice)."

    def handle(self, *args, **options):
        passwords = {a["env"]: os.environ.get(a["env"], "") for a in ACCOUNTS}
        missing = [name for name, value in passwords.items() if not value]
        if missing:
            raise CommandError(
                "Missing environment variable(s): " + ", ".join(missing) + ". Nothing was created."
            )

        with transaction.atomic():
            for account in ACCOUNTS:
                self.seed_user(account, passwords[account["env"]])
            base = first_dinner_date(timezone.localdate())
            for title, theme, place, cap, offset in DINNERS:
                self.seed_dinner(title, theme, place, cap, base + timedelta(days=offset))

    def seed_user(self, account, password):
        User = get_user_model()
        fields = {k: account[k] for k in ("first_name", "last_name", "is_staff", "is_superuser")}
        user = User.objects.filter(email=account["email"]).first()
        if user is None:
            User.objects.create_user(account["email"], password, **fields)
            self.stdout.write(f"{account['email']}: created")
            return
        changed = False
        for name, value in fields.items():
            if getattr(user, name) != value:
                setattr(user, name, value)
                changed = True
        if not user.check_password(password):
            user.set_password(password)
            changed = True
        if changed:
            user.save()
        self.stdout.write(f"{account['email']}: {'updated' if changed else 'unchanged'}")

    def seed_dinner(self, title, theme, place, cap, new_date):
        dinner = Dinner.objects.filter(title=title).order_by("pk").first()
        if dinner is None:
            Dinner.objects.create(
                title=title, theme=theme, after_party_place=place, team_cap=cap, date=new_date
            )
            self.stdout.write(f"{title}: created")
            return
        values = {"theme": theme, "after_party_place": place, "team_cap": cap}
        if dinner.date < timezone.localdate():
            values["date"] = new_date
        changed = False
        for name, value in values.items():
            if getattr(dinner, name) != value:
                setattr(dinner, name, value)
                changed = True
        if changed:
            dinner.save()
        self.stdout.write(f"{title}: {'updated' if changed else 'unchanged'}")
