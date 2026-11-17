from django.urls import path

from . import views

app_name = "recipes"

urlpatterns = [
    path("dinners/<int:pk>/dish-ideas/", views.dish_ideas, name="dish_ideas"),
]
