from typing import Any, Dict, List, Optional

from rest_framework import serializers

from baserow.api.utils import ExceptionMappingType
from baserow.core.auth_provider.auth_provider_types import AuthProviderType
from baserow.core.auth_provider.validators import validate_domain
from baserow_enterprise.api.sso.saml.errors import (
    ERROR_SAML_PROVIDER_FOR_DOMAIN_ALREADY_EXISTS,
)
from baserow_enterprise.api.sso.saml.validators import (
    validate_saml_metadata,
    validate_unique_saml_domain,
)
from baserow_enterprise.api.sso.utils import (
    get_saml_acs_absolute_url,
    get_saml_default_relay_state_url,
)
from baserow_enterprise.sso.saml.exceptions import SamlProviderForDomainAlreadyExists
from baserow_enterprise.sso.utils import is_sso_feature_active

from .models import SamlAuthProviderModel


class SamlAuthProviderType(AuthProviderType):
    """
    The SAML authentication provider type allows users to login using SAML.
    """

    type = "saml"
    model_class = SamlAuthProviderModel
    allowed_fields: List[str] = [
        "id",
        "domain",
        "type",
        "enabled",
        "metadata",
        "is_verified",
    ]
    serializer_field_names = ["domain", "metadata", "enabled", "is_verified"]
    serializer_field_overrides = {
        "domain": serializers.CharField(
            validators=[validate_domain],
            required=True,
            help_text="The email domain registered with this provider.",
        ),
        "enabled": serializers.BooleanField(
            help_text="Whether the provider is enabled or not.",
            required=False,
        ),
        "metadata": serializers.CharField(
            validators=[validate_saml_metadata],
            required=True,
            help_text="The SAML metadata XML provided by the IdP.",
        ),
        "is_verified": serializers.BooleanField(
            required=False,
            read_only=True,
            help_text="Whether or not a user sign in correctly with this SAML provider.",
        ),
    }
    api_exceptions_map: ExceptionMappingType = {
        SamlProviderForDomainAlreadyExists: ERROR_SAML_PROVIDER_FOR_DOMAIN_ALREADY_EXISTS
    }

    def before_create(self, user, **values):
        validate_unique_saml_domain(values["domain"])
        return super().before_create(user, **values)

    def before_update(self, user, provider, **values):
        if "domain" in values:
            validate_unique_saml_domain(values["domain"], provider)
        return super().before_update(user, provider, **values)

    def get_login_options(self, **kwargs) -> Optional[Dict[str, Any]]:

        single_sign_on_feature_active = is_sso_feature_active()
        if not single_sign_on_feature_active:
            return None

        configured_domains = SamlAuthProviderModel.objects.filter(enabled=True).count()
        if not configured_domains:
            return None

        return {
            "type": self.type,
            # if configure_domains = 1, we can redirect directly the user to the
            # IdP login page without asking for the email
            "domain_required": configured_domains > 1,
        }

    def can_create_new_providers(self):
        return True

    def export_serialized(self) -> Dict[str, Any]:
        serialized_data = super().export_serialized()
        serialized_data["relay_state_url"] = get_saml_default_relay_state_url()
        serialized_data["acs_url"] = get_saml_acs_absolute_url()
        return serialized_data
