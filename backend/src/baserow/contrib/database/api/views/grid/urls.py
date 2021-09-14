from django.urls import re_path

from .views import GridViewView


app_name = "baserow.contrib.database.api.views.grid"

urlpatterns = [
    re_path(r"(?P<view_id>[0-9]+)/$", GridViewView.as_view(), name="list"),
]
