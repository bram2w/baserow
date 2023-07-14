from django.urls import re_path

from .views import NotificationMarkAllAsReadView, NotificationsView, NotificationView

app_name = "baserow.api.notifications"

urlpatterns = [
    re_path(
        r"^(?P<workspace_id>[0-9]+)/$",
        NotificationsView.as_view(),
        name="list",
    ),
    re_path(
        r"^(?P<workspace_id>[0-9]+)/mark-all-as-read/$",
        NotificationMarkAllAsReadView.as_view(),
        name="mark_all_as_read",
    ),
    re_path(
        r"^(?P<workspace_id>[0-9]+)/(?P<notification_id>[0-9]+)/$",
        NotificationView.as_view(),
        name="item",
    ),
]
