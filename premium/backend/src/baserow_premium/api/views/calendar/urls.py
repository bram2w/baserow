from django.urls import re_path

from .views import CalendarViewView

app_name = "baserow_premium.api.views.calendar"

urlpatterns = [
    re_path(r"(?P<view_id>[0-9]+)/$", CalendarViewView.as_view(), name="list"),
]
