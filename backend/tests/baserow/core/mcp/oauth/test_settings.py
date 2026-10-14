import runpy
from pathlib import Path

import pytest

import baserow.config.settings.base as base_settings


def test_trailing_slash_in_public_backend_url_is_stripped(monkeypatch):
    monkeypatch.setenv("BASEROW_PUBLIC_URL", "")
    monkeypatch.setenv("PUBLIC_BACKEND_URL", "https://baserow.example/")
    settings = runpy.run_path(str(Path(base_settings.__file__)))

    assert settings["MCP_RESOURCE_URL"] == "https://baserow.example/mcp"
    oauth = settings["OAUTH2_PROVIDER"]
    assert oauth["OIDC_ISS_ENDPOINT"] == "https://baserow.example"
    assert oauth["OAUTH2_PROTECTED_RESOURCE_IDENTIFIER"] == (
        "https://baserow.example/mcp"
    )
    assert oauth["OAUTH2_PROTECTED_RESOURCE_AUTHORIZATION_SERVERS"] == [
        "https://baserow.example"
    ]


def test_cimd_can_be_turned_off_with_an_env_var(monkeypatch):
    monkeypatch.setenv("BASEROW_MCP_OAUTH_CIMD_ENABLED", "false")
    settings = runpy.run_path(str(Path(base_settings.__file__)))

    assert settings["OAUTH2_PROVIDER"]["CIMD_ENABLED"] is False


@pytest.mark.parametrize(
    "public_url,expected",
    [
        ("https://Baserow.Example:443", "https://baserow.example"),
        ("http://baserow.example:80/", "http://baserow.example"),
        ("HTTPS://baserow.example:8443", "https://baserow.example:8443"),
        ("http://[::1]:8000", "http://[::1]:8000"),
    ],
)
def test_public_backend_url_is_canonicalized(monkeypatch, public_url, expected):
    # MCP SDK clients normalize the resource like a browser URL before sending it,
    # and the resource is compared as a string.
    monkeypatch.setenv("BASEROW_PUBLIC_URL", "")
    monkeypatch.setenv("PUBLIC_BACKEND_URL", public_url)
    settings = runpy.run_path(str(Path(base_settings.__file__)))

    assert settings["MCP_AUTHORIZATION_SERVER_URL"] == expected
    assert settings["MCP_RESOURCE_URL"] == f"{expected}/mcp"
