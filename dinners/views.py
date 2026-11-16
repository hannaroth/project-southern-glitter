from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import Dinner


class HomeView(ListView):
    """Home page: dinners dated today or later (project time zone), soonest first."""

    model = Dinner
    template_name = "home.html"
    context_object_name = "dinners"

    def get_queryset(self):
        return Dinner.objects.filter(date__gte=timezone.localdate())


class DinnerDetailView(DetailView):
    """A dinner's public page, made to be shared (#14).

    Anyone can open it, logged in or not, so it shows only public details:
    no team addresses and no after-party address (those come with #18).
    """

    model = Dinner
    template_name = "dinners/detail.html"
    context_object_name = "dinner"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dinner = self.object
        path = reverse("dinners:detail", args=[dinner.pk])
        context.update(
            share_url=self.request.build_absolute_uri(path),
            login_url=f"{reverse('login')}?next={path}",
            is_past=dinner.date < timezone.localdate(),
            signups_closed=timezone.now() >= dinner.signup_deadline,
        )
        return context
