from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from dinners.models import Dinner

from .forms import TeamSignupForm
from .models import Team
from .services import (
    accept_refusal,
    active_team_for,
    assign_status,
    can_see_address,
    is_full,
    signups_open,
    waitlist_position,
)

CLOSED_MESSAGE = "Sign-ups for this dinner are closed."


@login_required
def signup(request, pk):
    dinner = get_object_or_404(Dinner, pk=pk)

    existing = active_team_for(request.user, dinner)
    if existing:
        messages.info(request, "You already have a team for this dinner.")
        return redirect("teams:detail", pk=existing.pk)

    if not signups_open(dinner):
        if request.method == "POST":
            messages.error(request, CLOSED_MESSAGE)
        return render(request, "teams/signup.html", {"dinner": dinner, "closed": True})

    if request.method == "POST":
        form = TeamSignupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Lock the dinner so two requests by the same person can't both create a team.
                Dinner.objects.select_for_update().get(pk=dinner.pk)
                existing = active_team_for(request.user, dinner)
                if existing:
                    messages.info(request, "You already have a team for this dinner.")
                    return redirect("teams:detail", pk=existing.pk)
                team = form.save(commit=False)
                team.dinner = dinner
                team.creator = request.user
                # Inside the dinner lock, so two sign-ups can't both take the last spot.
                assign_status(team)
                team.save()
            if team.status == Team.Status.WAITLISTED:
                messages.success(
                    request,
                    f"The dinner is full, so your team is on the waitlist "
                    f"(number {waitlist_position(team)}). You'll keep your place in line.",
                )
            else:
                messages.success(request, "Your team is signed up.")
            return redirect("teams:detail", pk=team.pk)
    else:
        form = TeamSignupForm()
    return render(
        request, "teams/signup.html", {"dinner": dinner, "form": form, "full": is_full(dinner)}
    )


@login_required
def detail(request, pk):
    team = get_object_or_404(Team.objects.select_related("dinner", "creator", "partner"), pk=pk)
    # The "our team" page is for the team's members and admins only.
    if not can_see_address(request.user, team):
        raise Http404
    invite_url = None
    show_invite = (
        request.user.pk == team.creator_id
        and not team.is_complete
        and team.status != Team.Status.CANCELLED
    )
    if show_invite:
        invite_url = request.build_absolute_uri(reverse("teams:accept", args=[team.invite_token]))
    return render(
        request,
        "teams/detail.html",
        {
            "team": team,
            "dinner": team.dinner,
            "invite_url": invite_url,
            "signups_open": signups_open(team.dinner),
            "waitlist_position": waitlist_position(team),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def accept(request, token):
    team = get_object_or_404(Team.objects.select_related("dinner", "creator"), invite_token=token)

    if team.partner_id == request.user.pk:
        messages.info(request, "You're already on this team.")
        return redirect("teams:detail", pk=team.pk)

    if request.method == "POST":
        with transaction.atomic():
            # Same lock as sign-up, so a person can't join two teams for one dinner at once.
            Dinner.objects.select_for_update().get(pk=team.dinner_id)
            team = Team.objects.select_related("dinner", "creator").get(pk=team.pk)
            refusal = accept_refusal(request.user, team)
            if refusal is None:
                team.partner = request.user
                team.save(update_fields=["partner"])
        if refusal is None:
            messages.success(request, f"You joined {team.creator.display_name}'s team.")
            return redirect("teams:detail", pk=team.pk)
    else:
        refusal = accept_refusal(request.user, team)

    context = {"team": team, "dinner": team.dinner, "refusal": refusal}
    if refusal:
        context["own_team"] = active_team_for(request.user, team.dinner)
    return render(request, "teams/accept.html", context)
