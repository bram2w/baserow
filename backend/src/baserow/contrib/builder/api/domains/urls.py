from django.urls import re_path

from baserow.contrib.builder.api.domains.views import (
    DomainsView,
    DomainView,
    OrderDomainsView,
)

app_name = "baserow.contrib.builder.api.domains"

urlpatterns_with_builder_id = [
    re_path(
        r"$",
        DomainsView.as_view(),
        name="list",
    ),
    re_path(r"order/$", OrderDomainsView.as_view(), name="order"),
]

urlpatterns_without_builder_id = [
    re_path(r"(?P<domain_id>[0-9]+)/$", DomainView.as_view(), name="item"),
]
