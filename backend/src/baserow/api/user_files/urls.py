from django.urls import re_path

from .views import UploadFileView, UploadViaURLView

app_name = "baserow.api.user"

urlpatterns = [
    re_path(r"^upload-file/$", UploadFileView.as_view(), name="upload_file"),
    re_path(r"^upload-via-url/$", UploadViaURLView.as_view(), name="upload_via_url"),
]
