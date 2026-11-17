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


def registered_count(dinner, *, exclude=None):
    """Non-cancelled teams holding one of the dinner's `team_cap` spots."""
    teams = Team.objects.filter(dinner=dinner, status=Team.Status.REGISTERED)
    if exclude is not None and exclude.pk is not None:
        teams = teams.exclude(pk=exclude.pk)
    return teams.count()


def is_full(dinner):
    """True once every spot is taken, so the next team goes on the waitlist."""
    return registered_count(dinner) >= dinner.team_cap


def assign_status(team):
    """Waitlist (#28): set and return the status of a team being created.

    REGISTERED while fewer than `team_cap` teams hold a spot, otherwise WAITLISTED.
    A team holds its spot from sign-up, before its partner accepts (decided Nov 15).
    Call it inside the sign-up transaction that locks the dinner row, so two
    sign-ups can't both take the last spot.
    """
    if registered_count(team.dinner, exclude=team) < team.dinner.team_cap:
        team.status = Team.Status.REGISTERED
    else:
        team.status = Team.Status.WAITLISTED
    return team.status


def waitlist_position(team):
    """1-based place on the dinner's waitlist in sign-up order, or None if not waitlisted."""
    if team.status != Team.Status.WAITLISTED:
        return None
    ahead = Team.objects.filter(dinner_id=team.dinner_id, status=Team.Status.WAITLISTED).filter(
        Q(created_at__lt=team.created_at) | Q(created_at=team.created_at, id__lt=team.id)
    )
    return ahead.count() + 1


def accept_refusal(user, team):
    """Why `user` may not accept `team`'s partner invite, or None if they may."""
    if team.status == Team.Status.CANCELLED:
        return "This team has cancelled its sign-up."
    if user.pk == team.creator_id:
        return "This is your own team's invite link. Send it to your partner instead."
    if team.partner_id is not None:
        return "This team already has a partner."
    if not signups_open(team.dinner):
        return "Sign-ups for this dinner are closed."
    if active_team_for(user, team.dinner):
        return "You already have a team for this dinner, so you can't join another one."
    return None
