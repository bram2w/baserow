from copy import deepcopy
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from oauth2_provider.models import Application

from tests.baserow.core.mcp.oauth.helpers import authorize_query, pkce_pair

CLAUDE_CLIENT = "https://claude.ai/oauth/mcp-oauth-client-metadata"
CLAUDE_REDIRECT = "https://claude.ai/api/mcp/auth_callback"
EVIL_CLIENT = "https://evil.example/client.json"
EVIL_REDIRECT = "https://evil.example/cb"
FETCH = "baserow.core.mcp.oauth.cimd.MCPMetadataFetcher.download"


def _metadata(client_id, redirect_uri):
    return {
        "client_id": client_id,
        "client_name": "Claude",
        "redirect_uris": [redirect_uri],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    }


@pytest.mark.django_db
def test_cimd_allowlisted_host_reaches_consent(client):
    _, challenge = pkce_pair()
    with patch(FETCH, return_value=(_metadata(CLAUDE_CLIENT, CLAUDE_REDIRECT), 300)):
        query = authorize_query(CLAUDE_CLIENT, challenge, redirect_uri=CLAUDE_REDIRECT)
        response = client.get(f"/oauth/authorize/?{query}")

    assert response.status_code == 302
    assert "/mcp-authorize" in response["Location"]
    application = Application.objects.get(client_id=CLAUDE_CLIENT)
    assert application.redirect_uris == CLAUDE_REDIRECT


@pytest.mark.django_db
def test_cimd_other_host_is_rejected(client, settings):
    settings.OAUTH2_PROVIDER = {
        **settings.OAUTH2_PROVIDER,
        "CIMD_ALLOWED_HOSTS": ["claude.ai", ".chatgpt.com"],
    }
    _, challenge = pkce_pair()
    with patch(
        FETCH, return_value=(_metadata(EVIL_CLIENT, EVIL_REDIRECT), 300)
    ) as fetch:
        query = authorize_query(EVIL_CLIENT, challenge, redirect_uri=EVIL_REDIRECT)
        response = client.get(f"/oauth/authorize/?{query}")

    fetch.assert_not_called()
    # Re-adding the server wouldn't help, so the page says the app can't sign in.
    assert response.status_code == 302
    location = response["Location"]
    assert location.startswith(f"{settings.BASEROW_EMBEDDED_SHARE_URL}/mcp-authorize?")
    assert parse_qs(urlparse(location).query) == {"error": ["client_rejected"]}
    assert EVIL_REDIRECT not in location
    assert "code=" not in location
    assert not Application.objects.filter(client_id=EVIL_CLIENT).exists()


@pytest.mark.django_db
def test_cimd_can_be_turned_off(client, settings):
    settings.OAUTH2_PROVIDER = {**settings.OAUTH2_PROVIDER, "CIMD_ENABLED": False}
    _, challenge = pkce_pair()
    with patch(
        FETCH, return_value=(_metadata(CLAUDE_CLIENT, CLAUDE_REDIRECT), 300)
    ) as fetch:
        query = authorize_query(CLAUDE_CLIENT, challenge, redirect_uri=CLAUDE_REDIRECT)
        response = client.get(f"/oauth/authorize/?{query}")

    fetch.assert_not_called()
    assert not Application.objects.filter(client_id=CLAUDE_CLIENT).exists()
    assert "/mcp-authorize?error=" in response["Location"]
    metadata = client.get("/.well-known/oauth-authorization-server").json()
    assert not metadata.get("client_id_metadata_document_supported")


# The documents these clients served on 2026-10-14.
CHATGPT_METADATA = {
    "client_id": "https://chatgpt.com/oauth/client.json",
    "client_uri": "https://chatgpt.com/",
    "redirect_uris": ["https://chatgpt.com/connector_platform_oauth_redirect"],
    "token_endpoint_auth_method": "private_key_jwt",
    "token_endpoint_auth_methods_supported": ["none", "private_key_jwt"],
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"],
    "client_name": "ChatGPT",
    "logo_uri": "https://persistent.oaistatic.com/sonic/misc/openai-logo.png",
    "token_endpoint_auth_signing_alg": "RS256",
    "jwks_uri": "https://chatgpt.com/oauth/jwks.json",
}
CLAUDE_METADATA = {
    "client_id": "https://claude.ai/oauth/mcp-oauth-client-metadata",
    "client_name": "Claude",
    "client_uri": "https://claude.ai",
    "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
    "grant_types": [
        "authorization_code",
        "refresh_token",
        "urn:ietf:params:oauth:grant-type:jwt-bearer",
    ],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none",
}
VSCODE_METADATA = {
    "client_name": "Visual Studio Code",
    "logo_uri": "https://code.visualstudio.com/assets/branding/code-stable.png",
    "grant_types": [
        "authorization_code",
        "refresh_token",
        "urn:ietf:params:oauth:grant-type:device_code",
    ],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none",
    "application_type": "native",
    "client_id": "https://vscode.dev/oauth/client-metadata.json",
    "client_uri": "https://vscode.dev/product",
    "redirect_uris": ["http://127.0.0.1:33418/", "https://vscode.dev/redirect"],
}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "metadata",
    [CHATGPT_METADATA, CLAUDE_METADATA, VSCODE_METADATA],
    ids=["chatgpt", "claude", "vscode"],
)
def test_cimd_real_client_documents_reach_consent(client, metadata):
    client_id = metadata["client_id"]
    redirect_uri = metadata["redirect_uris"][-1]
    _, challenge = pkce_pair()
    with patch(FETCH, return_value=(deepcopy(metadata), 300)):
        query = authorize_query(client_id, challenge, redirect_uri=redirect_uri)
        response = client.get(f"/oauth/authorize/?{query}")

    assert response.status_code == 302
    location = response["Location"]
    assert "/mcp-authorize/" in location
    assert "error" not in parse_qs(urlparse(location).query)
    application = Application.objects.get(client_id=client_id)
    assert application.client_type == Application.CLIENT_PUBLIC
    assert application.authorization_grant_type == Application.GRANT_AUTHORIZATION_CODE


@pytest.mark.django_db
def test_cimd_client_that_cannot_use_none_is_rejected(client):
    metadata = {
        **CHATGPT_METADATA,
        "token_endpoint_auth_methods_supported": ["private_key_jwt"],
    }
    _, challenge = pkce_pair()
    with patch(FETCH, return_value=(metadata, 300)):
        query = authorize_query(
            metadata["client_id"],
            challenge,
            redirect_uri=metadata["redirect_uris"][0],
        )
        response = client.get(f"/oauth/authorize/?{query}")

    assert "/mcp-authorize?error=client_rejected" in response["Location"]
    assert not Application.objects.filter(client_id=metadata["client_id"]).exists()


@pytest.mark.django_db
def test_cimd_client_without_authorization_code_is_rejected(client):
    metadata = {
        **CLAUDE_METADATA,
        "grant_types": ["urn:ietf:params:oauth:grant-type:jwt-bearer"],
    }
    _, challenge = pkce_pair()
    with patch(FETCH, return_value=(metadata, 300)):
        query = authorize_query(
            metadata["client_id"],
            challenge,
            redirect_uri=metadata["redirect_uris"][0],
        )
        response = client.get(f"/oauth/authorize/?{query}")

    assert "/mcp-authorize?error=client_rejected" in response["Location"]
    assert not Application.objects.filter(client_id=metadata["client_id"]).exists()
