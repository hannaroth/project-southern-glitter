from django.urls import path

from .views import DinnerDetailView

app_name = "dinners"

urlpatterns = [
    path("dinners/<int:pk>/", DinnerDetailView.as_view(), name="detail"),
]
