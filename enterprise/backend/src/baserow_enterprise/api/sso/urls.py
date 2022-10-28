from django.urls import include, path

from .saml import urls as saml_urls

app_name = "baserow_enterprise.api.sso"

urlpatterns = [
    path("saml/", include(saml_urls, namespace="saml")),
]
