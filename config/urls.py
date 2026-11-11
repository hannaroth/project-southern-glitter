from django.contrib import admin
from django.urls import include, path

from dinners.views import HomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("abtest.urls")),
    path("", HomeView.as_view(), name="home"),
    path("", include("accounts.urls")),
]
