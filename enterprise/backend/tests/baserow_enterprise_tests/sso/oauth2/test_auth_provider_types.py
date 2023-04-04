import json
from urllib.parse import parse_qsl, urlparse

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.test.utils import override_settings

import pytest
import responses

from baserow.core.registries import auth_provider_type_registry
from baserow_enterprise.sso.oauth2.auth_provider_types import (
    OAuth2AuthProviderMixin,
    OpenIdConnectAuthProviderType,
    WellKnownUrls,
)


@pytest.mark.parametrize(
    "provider_type,extra_params",
    [
        ("google", {}),
        ("facebook", {}),
        ("github", {}),
        ("gitlab", {"base_url": "https://gitlab.com"}),
        ("openid_connect", {"base_url": "https://gitlab.com"}),
    ],
)
@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_get_login_options(
    provider_type, extra_params, data_fixture, enterprise_data_fixture
):
    data_fixture.create_password_provider()
    provider = enterprise_data_fixture.create_oauth_provider(
        type=provider_type,
        client_id="test_client_id",
        secret="test_secret",
        name="provider1",
        **extra_params,
    )
    provider2 = enterprise_data_fixture.create_oauth_provider(
        type=provider_type,
        client_id="g_client_id",
        secret="g_secret",
        name="provider2",
        enabled=False,
        **extra_params,
    )
    enterprise_data_fixture.enable_enterprise()
    provider_type_instance = auth_provider_type_registry.get_by_model(provider)

    assert provider_type_instance.get_login_options() == {
        "type": provider_type,
        "items": [
            {
                "redirect_url": (
                    f"{settings.PUBLIC_BACKEND_URL}"
                    f"/api/sso/oauth2/login/{provider.id}/"
                ),
                "name": provider.name,
                "type": provider_type,
            }
        ],
        "default_redirect_url": (
            f"{settings.PUBLIC_BACKEND_URL}" f"/api/sso/oauth2/login/{provider.id}/"
        ),
    }


@pytest.mark.parametrize(
    "provider_type,extra_params",
    [
        ("google", {}),
        ("facebook", {}),
        ("github", {}),
        ("gitlab", {"base_url": "https://gitlab.com"}),
        (
            "openid_connect",
            {
                "base_url": "https://gitlab.com",
                "authorization_url": "https://gitlab.com/oauth/authorize",
            },
        ),
    ],
)
@pytest.mark.django_db
def test_get_authorization_url(provider_type, extra_params, enterprise_data_fixture):
    provider = enterprise_data_fixture.create_oauth_provider(
        type=provider_type,
        client_id="test_client_id",
        secret="test_secret",
        name="provider1",
        **extra_params,
    )
    provider_type_instance = auth_provider_type_registry.get_by_model(provider)
    session = SessionBase()
    query_params = {"query_param": "param_value"}

    auth_url = provider_type_instance.get_authorization_url(
        provider, session, query_params
    )

    parsed_url = urlparse(auth_url)
    params = dict(parse_qsl(parsed_url.query))
    assert params["response_type"] == "code"
    assert params["client_id"] == "test_client_id"
    assert f"/api/sso/oauth2/callback/{provider.id}/" in params["redirect_uri"]
    assert params["state"] == session["oauth_state"]
    stored_query_params = json.loads(session["oauth_request_data"])
    assert stored_query_params["query_param"] == "param_value"


@pytest.mark.parametrize(
    "provider_type,extra_params",
    [
        ("google", {}),
        ("facebook", {}),
        ("github", {}),
        ("gitlab", {"base_url": "https://gitlab.com"}),
        (
            "openid_connect",
            {
                "base_url": "https://gitlab.com",
                "authorization_url": "https://gitlab.com/oauth/authorize",
                "access_token_url": "https://gitlab.com/oauth/token",
                "user_info_url": "https://gitlab.com/api/v4/user",
            },
        ),
    ],
)
@pytest.mark.django_db
@responses.activate
def test_get_oauth_token_and_response(
    provider_type, extra_params, enterprise_data_fixture
):
    provider = enterprise_data_fixture.create_oauth_provider(
        type=provider_type,
        client_id="test_client_id",
        secret="test_secret",
        name="provider1",
        **extra_params,
    )
    provider_type_instance = auth_provider_type_registry.get_by_model(provider)
    session = SessionBase()
    code = "testcode"

    # mock access token response
    access_token_response = {
        "access_token": "MTQ0NjJkZmQ5OTM2NDE1ZTZjNGZmZjI3",
        "token_type": "Bearer",
    }
    responses.add(
        responses.POST,
        provider_type_instance.get_access_token_url(provider),
        json=access_token_response,
        status=200,
    )

    # mock get user info response
    oauth_response_data = {
        "email": "testuser@example.com",
        "name": "Test User",
    }
    responses.add(
        responses.GET,
        provider_type_instance.get_user_info_url(provider),
        json=oauth_response_data,
        status=200,
    )

    token, json_response = provider_type_instance.get_oauth_token_and_response(
        provider, code, session
    )
    assert token == access_token_response
    assert json_response["email"] == oauth_response_data["email"]
    assert json_response["name"] == oauth_response_data["name"]


@pytest.mark.parametrize(
    "provider_type,extra_params",
    [
        ("google", {}),
        ("facebook", {}),
        ("github", {}),
        ("gitlab", {"base_url": "https://gitlab.com"}),
        (
            "openid_connect",
            {
                "base_url": "https://gitlab.com",
                "authorization_url": "https://gitlab.com/oauth/authorize",
                "access_token_url": "https://gitlab.com/oauth/token",
                "user_info_url": "https://gitlab.com/api/v4/user",
            },
        ),
    ],
)
@pytest.mark.django_db
@responses.activate
def test_get_user_info(provider_type, extra_params, enterprise_data_fixture):
    provider = enterprise_data_fixture.create_oauth_provider(
        type=provider_type,
        client_id="test_client_id",
        secret="test_secret",
        name="provider1",
        **extra_params,
    )
    provider_type_instance = auth_provider_type_registry.get_by_model(provider)
    session = SessionBase()
    code = "testcode"
    query_params = {
        "workspace_invitation_token": "testgrouptoken",
        "language": "es",
        "original": "templates",
    }
    provider_type_instance.push_request_data_to_session(session, query_params)

    # mock access token response
    access_token_response = {
        "access_token": "MTQ0NjJkZmQ5OTM2NDE1ZTZjNGZmZjI3",
        "token_type": "Bearer",
    }
    responses.add(
        responses.POST,
        provider_type_instance.get_access_token_url(provider),
        json=access_token_response,
        status=200,
    )

    # mock get user info response
    oauth_response_data = {
        "email": "testuser@example.com",
        "name": "Test User",
    }
    responses.add(
        responses.GET,
        provider_type_instance.get_user_info_url(provider),
        json=oauth_response_data,
        status=200,
    )

    # mock emails endpoint for github
    if provider_type == "github":
        responses.add(
            responses.GET,
            provider_type_instance.EMAILS_URL,
            json=[{"email": "testuser@example.com"}],
            status=200,
        )

    user_info, original = provider_type_instance.get_user_info(provider, code, session)
    assert user_info.email == oauth_response_data["email"]
    assert user_info.name == oauth_response_data["name"]
    assert (
        user_info.workspace_invitation_token
        == query_params["workspace_invitation_token"]
    )
    assert user_info.language == query_params["language"]
    assert original == query_params["original"]


@pytest.mark.parametrize(
    "provider_type,extra_params",
    [
        ("google", {}),
        ("facebook", {}),
        ("github", {}),
        ("gitlab", {"base_url": "https://gitlab.com"}),
        (
            "openid_connect",
            {
                "base_url": "https://gitlab.com",
                "authorization_url": "https://gitlab.com/oauth/authorize",
            },
        ),
    ],
)
@pytest.mark.django_db
def test_get_user_info_from_oauth_json_response(
    provider_type, extra_params, enterprise_data_fixture
):
    provider = enterprise_data_fixture.create_oauth_provider(
        type=provider_type,
        client_id="test_client_id",
        secret="test_secret",
        name="provider1",
        **extra_params,
    )
    provider_type_instance = auth_provider_type_registry.get_by_model(provider)
    session = SessionBase()
    query_params = {
        "workspace_invitation_token": "testgrouptoken",
        "language": "es",
        "original": "templates",
    }
    provider_type_instance.push_request_data_to_session(session, query_params)
    oauth_response_data = {
        "email": "testuser@example.com",
        "name": "Test User",
    }

    user_info, original = provider_type_instance.get_user_info_from_oauth_json_response(
        oauth_response_data, session
    )
    assert user_info.email == oauth_response_data["email"]
    assert user_info.name == oauth_response_data["name"]
    assert (
        user_info.workspace_invitation_token
        == query_params["workspace_invitation_token"]
    )
    assert user_info.language == query_params["language"]
    assert original == query_params["original"]

    # missing name
    oauth_response_data = {
        "email": "testuser@example.com",
    }

    user_info, original = provider_type_instance.get_user_info_from_oauth_json_response(
        oauth_response_data, session
    )
    assert user_info.name == oauth_response_data["email"]

    # empty name
    oauth_response_data = {
        "email": "testuser@example.com",
        "name": "   ",
    }

    user_info, original = provider_type_instance.get_user_info_from_oauth_json_response(
        oauth_response_data, session
    )
    assert user_info.name == oauth_response_data["email"]


def test_push_pop_request_data_to_session():
    session = SessionBase()
    query_params = {
        "original": "templates",
        "oauth_state": "state",
        "workspace_invitation_token": "fjkldsfj",
        "language": "es",
    }
    mixin = OAuth2AuthProviderMixin()

    mixin.push_request_data_to_session(session, query_params)
    retrieved_params = mixin.pop_request_data_from_session(session)

    assert query_params == retrieved_params


@responses.activate
def test_openid_get_wellknown_urls():
    base_url = "http://example.com"
    endpoint_response = {
        "authorization_endpoint": "http://example.com/authorization",
        "token_endpoint": "http://example.com/accesstoken",
        "userinfo_endpoint": "http://example.com/userinfo",
    }
    responses.add(
        responses.GET,
        f"{base_url}/.well-known/openid-configuration",
        json=endpoint_response,
        status=200,
    )

    wellknown_urls = OpenIdConnectAuthProviderType().get_wellknown_urls(base_url)

    assert wellknown_urls == WellKnownUrls(
        authorization_url="http://example.com/authorization",
        access_token_url="http://example.com/accesstoken",
        user_info_url="http://example.com/userinfo",
    )
