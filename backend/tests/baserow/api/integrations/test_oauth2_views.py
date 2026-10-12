from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.test import override_settings
from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_302_FOUND, HTTP_400_BAD_REQUEST

from tests.baserow.contrib.integrations.external_api_test_utils import fake_response

FRONTEND = "http://localhost:3000"
SEND = "baserow.contrib.integrations.oauth2.integration_types.send_http_request"


@pytest.mark.django_db
@override_settings(PUBLIC_WEB_FRONTEND_URL=FRONTEND)
def test_authorize_endpoint(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    integration = data_fixture.create_google_integration(user=user, refresh_token="")
    url = reverse(
        "api:integrations:oauth2_authorize", kwargs={"integration_id": integration.id}
    )

    response = api_client.post(
        url,
        {"return_url": f"{FRONTEND}/automation/1"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    authorization_url = response.json()["authorization_url"]
    assert authorization_url.startswith("https://accounts.google.com/")
    assert "state=" in authorization_url

    response = api_client.post(
        url,
        {"return_url": "https://elsewhere.example/"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_OAUTH2_INVALID_RETURN_URL"

    unconfigured = data_fixture.create_google_integration(user=user, client_id="")
    response = api_client.post(
        reverse(
            "api:integrations:oauth2_authorize",
            kwargs={"integration_id": unconfigured.id},
        ),
        {"return_url": f"{FRONTEND}/automation/1"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.json()["error"] == "ERROR_OAUTH2_INTEGRATION_NOT_CONFIGURED"

    slack = data_fixture.create_slack_bot_integration(user=user)
    response = api_client.post(
        reverse(
            "api:integrations:oauth2_authorize", kwargs={"integration_id": slack.id}
        ),
        {"return_url": f"{FRONTEND}/automation/1"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.json()["error"] == "ERROR_OAUTH2_NOT_SUPPORTED"

    _, other_token = data_fixture.create_user_and_token()
    response = api_client.post(
        url,
        {"return_url": f"{FRONTEND}/automation/1"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {other_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"


@pytest.mark.django_db
@override_settings(PUBLIC_WEB_FRONTEND_URL=FRONTEND)
def test_callback_hands_the_code_to_the_frontend(api_client):
    url = reverse("api:integrations:oauth2_callback")

    # Nothing is exchanged without a session; the frontend completes it.
    with patch(SEND) as send:
        response = api_client.get(url, {"code": "c", "state": "s", "scope": "ignored"})
    send.assert_not_called()
    assert response.status_code == HTTP_302_FOUND
    redirected = urlparse(response["Location"])
    assert f"{redirected.scheme}://{redirected.netloc}" == FRONTEND
    assert redirected.path == "/integration/oauth2/complete"
    assert parse_qs(redirected.query) == {"code": ["c"], "state": ["s"]}

    response = api_client.get(
        url, {"error": "access_denied", "state": "s", "error_description": "No"}
    )
    assert parse_qs(urlparse(response["Location"]).query) == {
        "error": ["access_denied"],
        "state": ["s"],
        "error_description": ["No"],
    }


@pytest.mark.django_db
@override_settings(PUBLIC_WEB_FRONTEND_URL=FRONTEND, OAUTH_BACKEND_URL="http://api")
def test_redirect_uri_endpoint(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token()
    response = api_client.get(
        reverse("api:integrations:oauth2_redirect_uri"),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "redirect_uri": "http://api/api/integration/oauth2/callback/"
    }


def _start(api_client, integration, token):
    response = api_client.post(
        reverse(
            "api:integrations:oauth2_authorize",
            kwargs={"integration_id": integration.id},
        ),
        {"return_url": f"{FRONTEND}/automation/1?tab=integrations"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    return parse_qs(urlparse(response.json()["authorization_url"]).query)["state"][0]


@pytest.mark.django_db
@override_settings(PUBLIC_WEB_FRONTEND_URL=FRONTEND)
def test_complete_endpoint_connects_the_account_once(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    integration = data_fixture.create_google_integration(user=user, refresh_token="")
    state = _start(api_client, integration, token)
    url = reverse("api:integrations:oauth2_complete")

    responses = [
        fake_response(200, {"access_token": "at", "refresh_token": "rt"}),
        fake_response(200, {"email": "me@example.com"}),
    ]
    with patch(SEND, side_effect=responses):
        response = api_client.post(
            url,
            {"code": "c", "state": state},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "integration_id": integration.id,
        "return_url": f"{FRONTEND}/automation/1?tab=integrations",
    }
    integration.refresh_from_db()
    assert integration.account_email == "me@example.com"

    # A replayed state is refused before anything reaches the provider.
    with patch(SEND) as send:
        response = api_client.post(
            url,
            {"code": "c", "state": state},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
    send.assert_not_called()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_OAUTH2_INVALID_STATE"

    # The provider's refusal reaches the user as the error's detail.
    state = _start(api_client, integration, token)
    with patch(
        SEND,
        return_value=fake_response(
            400, {"error": "invalid_grant", "error_description": "Bad code"}
        ),
    ):
        response = api_client.post(
            url,
            {"code": "c", "state": state},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_OAUTH2_TOKEN_REQUEST_FAILED"
    assert "Bad code" in response.json()["detail"]


@pytest.mark.django_db
@override_settings(PUBLIC_WEB_FRONTEND_URL=FRONTEND)
def test_complete_endpoint_refuses_another_user(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    integration = data_fixture.create_google_integration(user=user, refresh_token="")
    state = _start(api_client, integration, token)
    # Even a member allowed to change the integration cannot finish someone
    # else's flow, which would connect their own account instead.
    _, other_token = data_fixture.create_user_and_token(
        workspace=integration.application.workspace
    )
    url = reverse("api:integrations:oauth2_complete")

    with patch(SEND) as send:
        response = api_client.post(
            url,
            {"code": "c", "state": state},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {other_token}",
        )
    send.assert_not_called()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_OAUTH2_INVALID_STATE"
    integration.refresh_from_db()
    assert integration.refresh_token == ""

    # Nor without a session at all.
    response = api_client.post(url, {"code": "c", "state": state}, format="json")
    assert response.status_code == 401
