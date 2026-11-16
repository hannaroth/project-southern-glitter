from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from dinners.models import Dinner

from .forms import TeamSignupForm
from .models import Team
from .services import (
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
    return render(
        request,
        "teams/detail.html",
        {"team": team, "dinner": team.dinner, "waitlist_position": waitlist_position(team)},
    )
