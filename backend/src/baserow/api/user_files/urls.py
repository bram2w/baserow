from django.conf.urls import url

from .views import UploadFileView, UploadViaURLView


app_name = "baserow.api.user"

urlpatterns = [
    url(r"^upload-file/$", UploadFileView.as_view(), name="upload_file"),
    url(r"^upload-via-url/$", UploadViaURLView.as_view(), name="upload_via_url"),
]
