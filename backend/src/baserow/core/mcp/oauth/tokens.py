from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from oauth2_provider.models import AccessToken, RefreshToken

from baserow.core.mcp.models import MCPEndpoint

from .validators import endpoint_id_from_scopes


def revoke_endpoint_tokens(endpoint: MCPEndpoint) -> None:
    """
    Deletes every OAuth access and refresh token bound to the given grant. Endpoints
    without an OAuth client never have tokens. The scope is matched as a whole
    space-separated word so `endpoint:1` never matches `endpoint:12`.
    """

    if endpoint.oauth_client_id is None:
        return
    pattern = rf"(^| )endpoint:{int(endpoint.id)}( |$)"
    access_ids = list(
        AccessToken.objects.filter(
            user_id=endpoint.user_id,
            application__client_id=endpoint.oauth_client_id,
            scope__regex=pattern,
        ).values_list("id", flat=True)
    )
    RefreshToken.objects.filter(access_token_id__in=access_ids).delete()
    AccessToken.objects.filter(id__in=access_ids).delete()


def endpoint_ids_with_live_refresh_token(user: AbstractUser) -> set[int]:
    """
    The ids of the user's grants that still have a usable refresh token. A grant
    without one stays listed, but the app has to sign in again to use it. A
    refresh token is linked to its grant through the newest access token's scope.
    """

    cutoff = timezone.now() - timedelta(
        seconds=settings.MCP_REFRESH_TOKEN_EXPIRE_SECONDS
    )
    scopes = RefreshToken.objects.filter(
        user=user,
        revoked__isnull=True,
        created__gt=cutoff,
        access_token__isnull=False,
    ).values_list("access_token__scope", flat=True)
    return {
        endpoint_id
        for scope in scopes
        if (endpoint_id := endpoint_id_from_scopes(scope.split())) is not None
    }
