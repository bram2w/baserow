from django.conf.urls import url

from .views import SettingsView, UpdateSettingsView


app_name = "baserow.api.settings"

urlpatterns = [
    url(r"^update/$", UpdateSettingsView.as_view(), name="update"),
    url(r"^$", SettingsView.as_view(), name="get"),
]
