from django.urls import re_path

from .views import AuthProvidersLoginOptionsView

app_name = "baserow.api.auth_provider"

urlpatterns = [
    re_path(
        r"^login-options/$",
        AuthProvidersLoginOptionsView.as_view(),
        name="login_options",
    ),
]
