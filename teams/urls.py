from django.urls import path

from . import views

app_name = "teams"

urlpatterns = [
    path("dinners/<int:pk>/signup/", views.signup, name="signup"),
    path("teams/<int:pk>/", views.detail, name="detail"),
]
