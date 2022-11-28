from django.test.utils import override_settings

import pytest

from baserow_enterprise.sso.saml.exceptions import InvalidSamlRequest
from baserow_enterprise.sso.saml.handler import SamlAuthProviderHandler


@pytest.mark.django_db()
@override_settings(DEBUG=True)
def test_get_user_info_from_authn_user_identity():
    user_info = SamlAuthProviderHandler.get_user_info_from_authn_user_identity(
        {"user.email": ["some@email.com"], "user.name": ["John"]}
    )
    assert user_info.email == "some@email.com"
    assert user_info.name == "John"

    user_info = SamlAuthProviderHandler.get_user_info_from_authn_user_identity(
        {
            "user.email": ["some@email.com"],
            "user.first_name": ["John"],
        }
    )
    assert user_info.email == "some@email.com"
    assert user_info.name == "John"

    user_info = SamlAuthProviderHandler.get_user_info_from_authn_user_identity(
        {
            "user.email": ["some@email.com"],
            "user.first_name": ["John"],
            "user.last_name": ["Doe"],
        }
    )
    assert user_info.email == "some@email.com"
    assert user_info.name == "John Doe"
    assert user_info.language is None
    assert user_info.group_invitation_token is None

    user_info = SamlAuthProviderHandler.get_user_info_from_authn_user_identity(
        {"user.email": ["some@email.com"]}
    )
    assert user_info.email == "some@email.com"
    assert user_info.name == "some@email.com"

    user_info = SamlAuthProviderHandler.get_user_info_from_authn_user_identity(
        {"user.email": ["some@email.com"], "user.name": ["John Doe"]},
        {"language": "it", "group_invitation_token": "1234"},
    )
    assert user_info.email == "some@email.com"
    assert user_info.name == "John Doe"
    assert user_info.language == "it"
    assert user_info.group_invitation_token == "1234"


@pytest.mark.django_db()
@override_settings(DEBUG=True)
def test_no_need_for_email_if_single_saml_provider(enterprise_data_fixture):
    saml_provider = enterprise_data_fixture.create_saml_auth_provider(
        domain="test1.com"
    )

    assert (
        SamlAuthProviderHandler.get_saml_auth_provider_from_email().domain
        == saml_provider.domain
    )


@pytest.mark.django_db()
@override_settings(DEBUG=True)
def test_need_valid_email_if_multiple_saml_providers(enterprise_data_fixture):
    saml_provider = enterprise_data_fixture.create_saml_auth_provider(
        domain="test1.com"
    )
    enterprise_data_fixture.create_saml_auth_provider(domain="test2.com")

    with pytest.raises(InvalidSamlRequest):
        assert (
            SamlAuthProviderHandler.get_saml_auth_provider_from_email().domain
            == saml_provider.domain
        )

    assert (
        SamlAuthProviderHandler.get_saml_auth_provider_from_email(
            "hello@test1.com"
        ).domain
        == saml_provider.domain
    )


@pytest.mark.django_db()
@override_settings(DEBUG=True)
def test_cannot_retrieve_saml_provider_from_invalid_mail(enterprise_data_fixture):
    enterprise_data_fixture.create_saml_auth_provider(domain="test1.com")
    with pytest.raises(InvalidSamlRequest):
        SamlAuthProviderHandler.get_saml_auth_provider_from_email("invalid_mail")
