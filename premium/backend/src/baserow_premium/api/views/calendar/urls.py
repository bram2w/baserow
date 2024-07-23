from django.urls import re_path

from .views import (
    CalendarViewView,
    ICalView,
    PublicCalendarViewView,
    RotateIcalFeedSlugView,
)

app_name = "baserow_premium.api.views.calendar"

urlpatterns = [
    re_path(r"(?P<view_id>[0-9]+)/$", CalendarViewView.as_view(), name="list"),
    re_path(
        r"(?P<slug>[-\w]+)/public/rows/$",
        PublicCalendarViewView.as_view(),
        name="public_rows",
    ),
    re_path(
        r"(?P<view_id>[0-9]+)/ical_slug_rotate/$",
        RotateIcalFeedSlugView.as_view(),
        name="ical_slug_rotate",
    ),
    re_path(
        r"(?P<ical_slug>[-\w]+).ics$",
        ICalView.as_view(),
        name="calendar_ical_feed",
    ),
]
