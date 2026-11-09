from django.urls import path

from . import views

app_name = "abtest"

# No trailing slashes: the course checks /c6a680e exactly, with no redirect.
urlpatterns = [
    path("c6a680e", views.ab_page, name="page"),
    path("c6a680e/stats", views.ab_stats, name="stats"),
]
