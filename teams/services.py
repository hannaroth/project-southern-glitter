"""Business rules for teams (docs/sprint-2-plan.md, section 5.3)."""

from django.db.models import Q
from django.utils import timezone

from .models import Team


def signups_open(dinner):
    """Sign-ups, invite accepts and cancels are allowed until the dinner's deadline."""
    return timezone.now() < dinner.signup_deadline


def active_team_for(user, dinner):
    """The user's non-cancelled team for this dinner (as creator or partner), or None."""
    if not user.is_authenticated:
        return None
    return (
        Team.objects.filter(dinner=dinner)
        .exclude(status=Team.Status.CANCELLED)
        .filter(Q(creator=user) | Q(partner=user))
        .first()
    )


def can_see_address(user, team):
    """A team's address is visible only to its two members and admins."""
    return user.is_authenticated and (user.is_staff or team.is_member(user))


def accept_refusal(user, team):
    """Why `user` may not accept `team`'s partner invite, or None if they may."""
    if user.pk == team.creator_id:
        return "This is your own team's invite link. Send it to your partner instead."
    if team.partner_id is not None:
        return "This team already has a partner."
    if team.status == Team.Status.CANCELLED:
        return "This team has cancelled its sign-up."
    if not signups_open(team.dinner):
        return "Sign-ups for this dinner are closed."
    if active_team_for(user, team.dinner):
        return "You already have a team for this dinner, so you can't join another one."
    return None
