from django.urls import re_path

from baserow.contrib.database.api.webhooks.views import (
    TableWebhooksView,
    TableWebhookView,
    TableWebhookTestCallView,
)


app_name = "baserow.contrib.database.api.webhooks"

urlpatterns = [
    re_path(r"table/(?P<table_id>[0-9]+)/$", TableWebhooksView.as_view(), name="list"),
    re_path(
        r"table/(?P<table_id>[0-9]+)/test-call/$",
        TableWebhookTestCallView.as_view(),
        name="test",
    ),
    re_path(r"(?P<webhook_id>[0-9]+)/$", TableWebhookView.as_view(), name="item"),
]
