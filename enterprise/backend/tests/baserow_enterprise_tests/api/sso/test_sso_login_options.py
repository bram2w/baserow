from django.shortcuts import reverse
from django.test.utils import override_settings

import pytest
from rest_framework.status import HTTP_200_OK


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_saml_not_available_without_an_enterprise_license(
    api_client, data_fixture, enterprise_data_fixture
):
    # create a valid SAML provider
    enterprise_data_fixture.create_saml_auth_provider(domain="test1.com")

    response = api_client.get(reverse("api:auth_provider:login_options"), format="json")
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert "saml" not in response_json


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_saml_available_with_an_enterprise_license(
    api_client, data_fixture, enterprise_data_fixture
):
    # create a valid SAML provider
    enterprise_data_fixture.create_saml_auth_provider(domain="test1.com")
    enterprise_data_fixture.create_enterprise_admin_user_and_token()

    response = api_client.get(reverse("api:auth_provider:login_options"), format="json")
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert "saml" in response_json
    assert response_json["saml"]["domain_required"] is False

    enterprise_data_fixture.create_saml_auth_provider(domain="acme.com")
    response = api_client.get(reverse("api:auth_provider:login_options"), format="json")
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert "saml" in response_json
    assert response_json["saml"]["domain_required"] is True
