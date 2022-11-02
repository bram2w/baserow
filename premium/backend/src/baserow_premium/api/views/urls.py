from django.urls import re_path

from baserow_premium.api.views.views import PremiumViewAttributesView

app_name = "baserow_premium.api.views"

urlpatterns = [
    re_path(
        "(?P<view_id>[0-9]+)/premium$",
        PremiumViewAttributesView.as_view(),
        name="premium_view_attributes",
    ),
]
