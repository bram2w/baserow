from django.urls import re_path

from .views import SettingsView, UpdateSettingsView


app_name = "baserow.api.settings"

urlpatterns = [
    re_path(r"^update/$", UpdateSettingsView.as_view(), name="update"),
    re_path(r"^$", SettingsView.as_view(), name="get"),
]
