from django.conf.urls import url

from .views import GridViewView


app_name = "baserow.contrib.database.api.views.grid"

urlpatterns = [
    url(r"(?P<view_id>[0-9]+)/$", GridViewView.as_view(), name="list"),
]
