import importlib
from unittest.mock import patch

from django.http import HttpResponse
from django.urls import Resolver404, path
from django.urls.resolvers import RegexPattern, URLResolver

import pytest
from oauth2_provider import urls as oauth2_urls

from baserow.config import urls as root_urls
from baserow.core.mcp.oauth import urls


def test_unnamed_library_metadata_patterns_are_kept():
    unnamed = path(".well-known/unnamed", lambda request: HttpResponse())
    patterns = oauth2_urls.metadata_urlpatterns + [unnamed]
    try:
        with patch.object(oauth2_urls, "metadata_urlpatterns", patterns):
            importlib.reload(urls)
        assert unnamed in urls.metadata_patterns
    finally:
        importlib.reload(urls)


@pytest.mark.parametrize("enabled", [False, True])
def test_oauth_routes_follow_the_flag(settings, enabled):
    # A fresh resolver, because the cached one was built from the URLconf as first
    # imported.
    def resolves(url):
        resolver = URLResolver(RegexPattern(r"^/"), root_urls.urlpatterns)
        try:
            resolver.resolve(url)
        except Resolver404:
            return False
        return True

    settings.BASEROW_MCP_OAUTH_ENABLED = enabled
    try:
        importlib.reload(root_urls)
        assert resolves("/oauth/register/") is enabled
        assert resolves("/.well-known/oauth-authorization-server") is enabled
    finally:
        settings.BASEROW_MCP_OAUTH_ENABLED = True
        importlib.reload(root_urls)
