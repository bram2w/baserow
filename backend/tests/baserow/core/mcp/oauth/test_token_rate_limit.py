from django.test import override_settings

import pytest
from freezegun import freeze_time

from baserow.throttling.types import RateLimit
from tests.baserow.core.mcp.oauth.helpers import obtain_tokens

LIMITS = (RateLimit(period_in_seconds=60, number_of_calls=2),)


def _token_request(client, ip):
    return client.post(
        "/oauth/token/",
        {"grant_type": "authorization_code", "code": "nope", "client_id": "x"},
        HTTP_X_FORWARDED_FOR=ip,
    )


@pytest.mark.django_db
@override_settings(BASEROW_MCP_OAUTH_TOKEN_RATE_LIMITS=LIMITS)
def test_token_endpoint_is_rate_limited_per_ip(client):
    with freeze_time("2026-01-01 12:00:00"):
        assert _token_request(client, "1.1.1.1").status_code != 429
        assert _token_request(client, "1.1.1.1").status_code != 429
        limited = _token_request(client, "1.1.1.1")
        other_ip = _token_request(client, "2.2.2.2")

    assert limited.status_code == 429
    assert limited.json()["error"] == "slow_down"
    assert int(limited["Retry-After"]) > 0
    assert other_ip.status_code != 429


def _authorize_request(client, ip):
    return client.get("/oauth/authorize/?client_id=x", HTTP_X_FORWARDED_FOR=ip)


@pytest.mark.django_db
@override_settings(BASEROW_MCP_OAUTH_AUTHORIZE_RATE_LIMITS=LIMITS)
def test_authorize_endpoint_is_rate_limited_per_ip(client):
    with freeze_time("2026-01-01 12:00:00"):
        assert _authorize_request(client, "1.1.1.1").status_code != 429
        assert _authorize_request(client, "1.1.1.1").status_code != 429
        limited = _authorize_request(client, "1.1.1.1")
        other_ip = _authorize_request(client, "2.2.2.2")

    assert limited.status_code == 429
    assert limited.json()["error"] == "slow_down"
    assert int(limited["Retry-After"]) > 0
    assert other_ip.status_code != 429


@pytest.mark.django_db
@override_settings(BASEROW_MCP_OAUTH_AUTHORIZE_RATE_LIMITS=LIMITS)
def test_consent_api_is_rate_limited_per_user(api_client, data_fixture):
    from django.urls import reverse

    def consent(jwt, ip):
        return api_client.get(
            reverse("api:mcp:oauth_consent"),
            {"query": "client_id=x"},
            HTTP_AUTHORIZATION=f"JWT {jwt}",
            HTTP_X_FORWARDED_FOR=ip,
        )

    with freeze_time("2026-01-01 12:00:00"):
        # Made inside the frozen time, so the JWTs aren't issued in the future.
        _, token = data_fixture.create_user_and_token()
        _, other_token = data_fixture.create_user_and_token()
        assert consent(token, "1.1.1.1").status_code != 429
        assert consent(token, "2.2.2.2").status_code != 429
        # Another IP doesn't help: the limit is per user.
        limited = consent(token, "3.3.3.3")
        other_user = consent(other_token, "1.1.1.1")

    assert limited.status_code == 429
    assert other_user.status_code != 429


def _revoke_request(client, ip):
    return client.post(
        "/oauth/revoke_token/",
        {"token": "nope", "client_id": "https://evil.example/client.json"},
        HTTP_X_FORWARDED_FOR=ip,
    )


@pytest.mark.django_db
@override_settings(BASEROW_MCP_OAUTH_TOKEN_RATE_LIMITS=LIMITS)
def test_revoke_endpoint_is_rate_limited_per_ip(client):
    with freeze_time("2026-01-01 12:00:00"):
        assert _revoke_request(client, "1.1.1.1").status_code != 429
        assert _revoke_request(client, "1.1.1.1").status_code != 429
        limited = _revoke_request(client, "1.1.1.1")
        other_ip = _revoke_request(client, "2.2.2.2")

    assert limited.status_code == 429
    assert limited.json()["error"] == "slow_down"
    assert other_ip.status_code != 429


@pytest.mark.django_db
@override_settings(BASEROW_MCP_OAUTH_TOKEN_RATE_LIMITS=LIMITS)
def test_successful_token_calls_do_not_count(client, api_client, data_fixture):
    user, jwt = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    tokens = obtain_tokens(client, api_client, jwt, workspace)

    refresh_token = tokens["refresh_token"]
    for _ in range(3):
        response = client.post(
            "/oauth/token/",
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": tokens["client_id"],
            },
        )
        assert response.status_code == 200, response.content
        refresh_token = response.json()["refresh_token"]

    # The two failed calls still use up the limit.
    assert _token_request(client, "127.0.0.1").status_code != 429
    assert _token_request(client, "127.0.0.1").status_code != 429
    assert _token_request(client, "127.0.0.1").status_code == 429
