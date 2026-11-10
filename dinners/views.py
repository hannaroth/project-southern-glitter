from django.utils import timezone
from django.views.generic import ListView

from .models import Dinner


class HomeView(ListView):
    """Home page: dinners dated today or later (project time zone), soonest first."""

    model = Dinner
    template_name = "home.html"
    context_object_name = "dinners"

    def get_queryset(self):
        return Dinner.objects.filter(date__gte=timezone.localdate())
