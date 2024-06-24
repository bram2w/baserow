from django.urls import re_path

from .views import DownloadView

app_name = "baserow_enterprise.api.files"

urlpatterns = [
    re_path(r"(?P<signed_data>.*)", DownloadView.as_view(), name="download"),
]
