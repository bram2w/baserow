from django.urls import re_path

from .views import (
    JobsView,
    JobView,
)


app_name = "baserow.api.jobs"

urlpatterns = [
    re_path(r"^$", JobsView.as_view(), name="list"),
    re_path(r"(?P<job_id>[0-9]+)/$", JobView.as_view(), name="item"),
]
