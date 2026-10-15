from oauth2_provider.views import RevokeTokenView, TokenView

from .throttling import (
    MCPOAuthRevokeRateThrottle,
    MCPOAuthTokenRateThrottle,
    rate_limited,
)


class MCPTokenView(TokenView):
    """
    The library's token endpoint, rate-limited per client IP. Only failed calls
    count: hosted apps refresh every user's token from a few IPs.
    """

    def post(self, request, *args, **kwargs):
        throttle = MCPOAuthTokenRateThrottle()
        limited = rate_limited(throttle, request, self)
        if limited is not None:
            return limited
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            throttle.release()
        return response


class MCPRevokeTokenView(RevokeTokenView):
    """
    The library's revocation endpoint, rate-limited per client IP. It loads the
    client before checking the token, which fetches and stores a CIMD client.
    """

    def post(self, request, *args, **kwargs):
        limited = rate_limited(MCPOAuthRevokeRateThrottle(), request, self)
        if limited is not None:
            return limited
        return super().post(request, *args, **kwargs)
