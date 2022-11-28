from django.test.utils import override_settings

import pytest

from baserow.core.registries import auth_provider_type_registry
from baserow_enterprise.auth_provider.handler import AuthProviderHandler
from baserow_enterprise.sso.saml.exceptions import SamlProviderForDomainAlreadyExists


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_get_login_options(enterprise_data_fixture):
    enterprise_data_fixture.create_saml_auth_provider(domain="test.com")
    login_options = auth_provider_type_registry.get_all_available_login_options()
    assert "saml" not in login_options

    enterprise_data_fixture.enable_enterprise()
    login_options = auth_provider_type_registry.get_all_available_login_options()
    assert login_options["saml"] == {
        "type": "saml",
        "domain_required": False,
    }

    enterprise_data_fixture.create_saml_auth_provider(domain="acme.com")
    login_options = auth_provider_type_registry.get_all_available_login_options()
    assert login_options["saml"] == {
        "type": "saml",
        "domain_required": True,
    }


@pytest.mark.django_db()
@override_settings(DEBUG=True)
def test_cannot_create_two_saml_providers_for_the_same_domain(enterprise_data_fixture):
    user, _ = enterprise_data_fixture.create_enterprise_admin_user_and_token()
    AuthProviderHandler.create_auth_provider(
        user,
        auth_provider_type_registry.get("saml"),
        domain="test.com",
        metadata=enterprise_data_fixture.get_test_saml_idp_metadata(),
    )
    with pytest.raises(SamlProviderForDomainAlreadyExists):
        AuthProviderHandler.create_auth_provider(
            user,
            auth_provider_type_registry.get("saml"),
            domain="test.com",
            metadata=enterprise_data_fixture.get_test_saml_idp_metadata(),
        )
