from django.urls import re_path

from .views import OAuth2CallbackView, OAuth2LoginView

app_name = "baserow_enterprise.api.sso.oauth"

urlpatterns = [
    re_path(
        r"^login/(?P<provider_id>[0-9]+)/$", OAuth2LoginView.as_view(), name="login"
    ),
    re_path(
        r"^callback/(?P<provider_id>[0-9]+)/$",
        OAuth2CallbackView.as_view(),
        name="callback",
    ),
]
