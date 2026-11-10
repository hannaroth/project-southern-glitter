from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Placeholder home page; issue #7 replaces it with the list of upcoming dinners."""

    template_name = "home.html"
