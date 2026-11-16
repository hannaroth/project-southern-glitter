from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from dinners.models import Dinner

User = get_user_model()


def make_dinner(title="Test Feast", deadline_in=timedelta(days=3), **kw):
    """A dinner whose sign-up deadline is `deadline_in` from now (negative = already passed)."""
    deadline = timezone.now() + deadline_in
    date = timezone.localtime(deadline).date() + timedelta(days=2)
    return Dinner.objects.create(
        title=title,
        theme=kw.get("theme", "Any theme"),
        date=date,
        starter_time=time(18, 0),
        main_time=time(19, 30),
        dessert_time=time(21, 0),
        after_party_name="Some Bar",
        after_party_address="1 Test Street",
        team_cap=kw.get("team_cap", 10),
        signup_deadline=deadline,
    )


def make_user(email, **kw):
    return User.objects.create_user(email, "pw-12345-xyz", **kw)
