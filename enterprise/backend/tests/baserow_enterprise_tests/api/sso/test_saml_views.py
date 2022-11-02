import base64
import io
import urllib
import zlib
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client
from django.test.utils import override_settings

import pytest
from defusedxml import ElementTree
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_302_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_402_PAYMENT_REQUIRED,
)
from saml2 import saml, samlp, xmldsig
from saml2.xml.schema import validate as validate_saml_xml

from baserow.core.user.exceptions import UserAlreadyExist
from baserow_enterprise.auth_provider.exceptions import DifferentAuthProvider
from baserow_enterprise.auth_provider.handler import AuthProviderHandler, UserInfo


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_saml_provider_get_login_url(api_client, data_fixture, enterprise_data_fixture):
    # create a valid SAML provider
    auth_provider_1 = enterprise_data_fixture.create_saml_auth_provider(
        domain="test1.com"
    )
    auth_provider_login_url = reverse("api:enterprise:sso:saml:login_url")

    _, unauthorized_token = data_fixture.create_user_and_token()

    response = api_client.get(
        auth_provider_login_url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {unauthorized_token}",
    )
    assert response.status_code == HTTP_402_PAYMENT_REQUIRED

    _, token = enterprise_data_fixture.create_enterprise_admin_user_and_token()

    # cannot create a SAML provider with an invalid domain or metadata
    response = api_client.get(
        auth_provider_login_url, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert "redirect_url" in response_json
    assert response_json["redirect_url"] == urljoin(
        settings.PUBLIC_BACKEND_URL, "/api/sso/saml/login/"
    )

    # if more than one SAML provider is enabled, this endpoint need a email address
    auth_provider_2 = enterprise_data_fixture.create_saml_auth_provider(
        domain="test2.com"
    )

    # cannot create a SAML provider with an invalid domain or metadata
    response = api_client.get(
        reverse("api:enterprise:sso:saml:login_url"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_SAML_INVALID_LOGIN_REQUEST"

    query_params = urllib.parse.urlencode(
        {
            "email": f"user@{auth_provider_1.domain}",
            "original": "/database/1/table/1",
        }
    )
    response = api_client.get(
        f"{auth_provider_login_url}?{query_params}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert "redirect_url" in response_json
    assert response_json["redirect_url"] == urljoin(
        settings.PUBLIC_BACKEND_URL, f"/api/sso/saml/login/?{query_params}"
    )

    query_params = urllib.parse.urlencode(
        {
            "email": f"user@{auth_provider_2.domain}",
            "original": "http://external-site.com",
        }
    )
    response = api_client.get(
        f"{auth_provider_login_url}?{query_params}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert "redirect_url" in response_json
    # the original url is not relative so it should be ignored
    response_query_params = urllib.parse.urlencode(
        {
            "email": f"user@{auth_provider_2.domain}",
        }
    )
    assert response_json["redirect_url"] == urljoin(
        settings.PUBLIC_BACKEND_URL, f"/api/sso/saml/login/?{response_query_params}"
    )

    query_params = urllib.parse.urlencode(
        {
            "email": "user@unregistered-domain.com",
            "original": "http://test.com",
        }
    )
    response = api_client.get(
        f"{auth_provider_login_url}?{query_params}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_SAML_INVALID_LOGIN_REQUEST"

    response = api_client.get(
        f"{auth_provider_login_url}?email=invalid_email",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"


@pytest.mark.django_db()
@override_settings(DEBUG=True)
def test_user_cannot_initiate_saml_sso_without_enterprise_license(
    api_client, data_fixture, enterprise_data_fixture
):
    auth_provider_1 = enterprise_data_fixture.create_saml_auth_provider(
        domain="test1.com"
    )
    client = Client()
    response = client.get(reverse("api:enterprise:sso:saml:login"))
    assert response.status_code == HTTP_302_FOUND
    assert (
        response.headers["Location"]
        == "http://localhost:3000/login/error?error=errorSsoFeatureNotActive"
    )


def decode_saml_request(idp_redirect_url):
    parsed_url = urllib.parse.urlparse(idp_redirect_url)
    query_params = urllib.parse.parse_qsl(parsed_url.query)
    encoded_saml_request = [v for k, v in query_params if k == "SAMLRequest"][0]
    saml_request_xml = zlib.decompress(
        base64.b64decode(encoded_saml_request), -15
    ).decode("utf-8")
    return ElementTree.parse(io.BytesIO(saml_request_xml.encode("utf-8")))


@pytest.mark.django_db()
@override_settings(DEBUG=True)
def test_user_can_initiate_saml_sso_with_enterprise_license(
    api_client, data_fixture, enterprise_data_fixture
):
    auth_provider_1 = enterprise_data_fixture.create_saml_auth_provider(
        domain="test1.com"
    )
    _, token = enterprise_data_fixture.create_enterprise_admin_user_and_token()
    client = Client()
    sp_sso_saml_login_url = reverse("api:enterprise:sso:saml:login")
    original_relative_url = "database/1/table/1/"
    request_query_string = urlencode({"original": original_relative_url})

    response = client.get(f"{sp_sso_saml_login_url}?{request_query_string}")
    assert response.status_code == HTTP_302_FOUND
    idp_sign_in_url = response.headers["Location"]
    idp_url_initial_part = (
        "https://samltest.id/idp/profile/SAML2/Redirect/SSO?SAMLRequest="
    )
    assert idp_sign_in_url.startswith(idp_url_initial_part)
    saml_request = decode_saml_request(idp_sign_in_url)
    assert validate_saml_xml(saml_request) is None
    response_query_params = parse_qs(urlparse(idp_sign_in_url).query)
    assert response_query_params["RelayState"][0] == urljoin(
        settings.PUBLIC_WEB_FRONTEND_URL, original_relative_url
    )

    response = client.get(f"{sp_sso_saml_login_url}?email=john@acme.it")
    assert response.status_code == HTTP_302_FOUND
    assert (
        response.headers["Location"]
        == "http://localhost:3000/login/error?error=errorInvalidSamlRequest"
    )


@pytest.mark.django_db()
@override_settings(DEBUG=True)
def test_get_or_create_user_and_sign_in_via_saml_identity(
    api_client, data_fixture, enterprise_data_fixture
):
    auth_provider_1 = enterprise_data_fixture.create_saml_auth_provider(
        domain="test1.com"
    )
    user_info = UserInfo("john@acme.com", "John")

    User = get_user_model()
    assert User.objects.count() == 0

    # test the user is created if not already present in the database
    user = AuthProviderHandler.get_or_create_user_and_sign_in_via_auth_provider(
        user_info, auth_provider_1
    )

    assert user is not None
    assert user.email == user_info.email
    assert user.first_name == user_info.name
    assert user.password == ""
    assert User.objects.count() == 1
    assert user.groupuser_set.count() == 1
    assert user.auth_providers.filter(id=auth_provider_1.id).exists()

    # check that the second time the user is not created again
    # but if we use another auth_provider to login, this is added
    # in the m2m
    auth_provider_2 = enterprise_data_fixture.create_saml_auth_provider(
        domain="test2.com"
    )
    with pytest.raises(DifferentAuthProvider):
        user = AuthProviderHandler.get_or_create_user_and_sign_in_via_auth_provider(
            user_info, auth_provider_2
        )

    assert User.objects.count() == 1
    assert not user.auth_providers.filter(id=auth_provider_2.id).exists()

    # a disabled user will raise a UserAlreadyExist exception
    user.is_active = False
    user.save()

    with pytest.raises(UserAlreadyExist):
        AuthProviderHandler.get_or_create_user_and_sign_in_via_auth_provider(
            user_info, auth_provider_2
        )


@pytest.mark.django_db()
@override_settings(DEBUG=True)
def test_saml_assertion_consumer_service(
    api_client, data_fixture, enterprise_data_fixture
):
    enterprise_data_fixture.create_saml_auth_provider(domain="test1.com")
    enterprise_data_fixture.create_enterprise_admin_user_and_token()

    client = Client()
    sp_sso_saml_acs_url = reverse("api:enterprise:sso:saml:acs")

    saml_response = samlp.Response()
    saml_response.id = "id"
    saml_response.in_response_to = "request_id"
    saml_response.version = "2.0"
    saml_response.issue_instant = "2021-10-28T10:05:02Z"
    saml_response.destination = "http://localhost:8000/api/sso/saml/acs/"
    saml_response.issuer = saml.Issuer()
    saml_response.signature = xmldsig.Signature()
    saml_response.extensions = samlp.Extensions()
    saml_response.status = samlp.Status()
    saml_response.assertion.append(saml.Assertion())
    saml_response.encrypted_assertion.append(saml.EncryptedAssertion())
    request_payload = base64.b64encode(saml_response.to_string()).decode("utf-8")
    response = client.post(sp_sso_saml_acs_url, data={"SAMLResponse": request_payload})
    assert response.status_code == HTTP_302_FOUND
    assert (
        response.headers["Location"]
        == "http://localhost:3000/login/error?error=errorInvalidSamlResponse"
    ), response.content
