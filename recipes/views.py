from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from dinners.models import Dinner
from teams.models import DIET_CHOICES, Team
from teams.services import active_team_for

from .ai import WISH_MAX_LENGTH, suggest_dishes
from .diet import ALLERGY_NOTE

COURSE_CHOICES = [("starter", "Starter"), ("main", "Main course"), ("dessert", "Dessert")]
MAX_EXCLUDED_IDS = 60
MAX_WHY_LENGTH = 300
MAX_SHOPPING_ITEMS = 40


class DishIdeasForm(forms.Form):
    wish = forms.CharField(
        required=False,
        max_length=WISH_MAX_LENGTH,
        label="Anything you wish for? (optional)",
        widget=forms.TextInput(attrs={"placeholder": "e.g. no oven, something spicy"}),
    )
    shown_ids = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, ask_course=False, **kwargs):
        super().__init__(*args, **kwargs)
        if ask_course:
            self.fields["course"] = forms.ChoiceField(choices=COURSE_CHOICES, label="Course we cook")
            self.order_fields(["course", "wish", "shown_ids"])

    def excluded_ids(self):
        """Ids already shown: comma-separated ints; garbage is ignored, the list is capped."""
        ids = []
        for part in (self.cleaned_data.get("shown_ids") or "").split(","):
            part = part.strip()
            if part.isascii() and part.isdigit() and len(part) <= 9:
                value = int(part)
                if value not in ids:
                    ids.append(value)
        return ids[:MAX_EXCLUDED_IDS]


def _restrictions(dinner):
    """Union of the restriction keys of all non-cancelled teams of the dinner (keys only)."""
    keys = set()
    for restrictions in (
        Team.objects.filter(dinner=dinner)
        .exclude(status=Team.Status.CANCELLED)
        .values_list("dietary_restrictions", flat=True)
    ):
        if isinstance(restrictions, list):
            keys.update(k for k in restrictions if isinstance(k, str))
    return [key for key, _label in DIET_CHOICES if key in keys]


def _safe_url(url):
    return url if url.startswith(("http://", "https://")) else ""


@login_required
def dish_ideas(request, pk):
    dinner = get_object_or_404(Dinner, pk=pk)
    team = active_team_for(request.user, dinner)
    if team is None:
        raise PermissionDenied

    restrictions = _restrictions(dinner)
    labels = dict(DIET_CHOICES)
    ask_course = team.preferred_course == Team.Course.NO_PREFERENCE
    context = {
        "dinner": dinner,
        "team": team,
        "ask_course": ask_course,
        "restriction_labels": [labels[k] for k in restrictions],
        "allergy_note": ALLERGY_NOTE,
        "course_label": None if ask_course else dict(COURSE_CHOICES)[team.preferred_course],
    }

    if request.method == "POST":
        form = DishIdeasForm(request.POST, ask_course=ask_course)
        if form.is_valid():
            course = form.cleaned_data["course"] if ask_course else team.preferred_course
            exclude_ids = form.excluded_ids() if "others" in request.POST else []
            result = suggest_dishes(
                course=course,
                theme=dinner.theme,
                restrictions=restrictions,
                wish=form.cleaned_data["wish"],
                exclude_ids=exclude_ids,
            )
            shown_ids = ",".join(
                str(i) for i in (exclude_ids + [x.recipe.pk for x in result.ideas])[-MAX_EXCLUDED_IDS:]
            )
            context.update(
                course_label=dict(COURSE_CHOICES)[course],
                ideas=[
                    {
                        "recipe": idea.recipe,
                        "why": idea.why[:MAX_WHY_LENGTH],
                        "url": _safe_url(idea.recipe.source_url),
                    }
                    for idea in result.ideas
                ],
                shopping_list=result.shopping_list[:MAX_SHOPPING_ITEMS],
                notice="" if result.ai_used else result.notice,
                vegan_course_note=bool(not result.ideas and "vegan" in restrictions and course != "main"),
                shown_ids=shown_ids,
                searched=True,
            )
            # Re-render the form with the new hidden ids and the same wish and course.
            data = request.POST.copy()
            data["shown_ids"] = shown_ids
            form = DishIdeasForm(data, ask_course=ask_course)
            form.is_valid()
    else:
        form = DishIdeasForm(ask_course=ask_course)
    context["form"] = form
    return render(request, "recipes/dish_ideas.html", context)
