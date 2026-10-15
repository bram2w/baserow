import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from oauth2_provider.views import DynamicClientRegistrationView

from .throttling import MCPOAuthRegistrationRateThrottle, rate_limited
from .validators import ALLOWED_GRANT_TYPES, is_allowed_redirect_uri

# RFC 7592 fields; the management endpoint isn't offered.
MANAGEMENT_FIELDS = ("registration_access_token", "registration_client_uri")

# Registration is anonymous, so these bound what one request can store. The body
# limit matches the library's CIMD document limit.
MAX_REGISTRATION_BYTES = 16 * 1024
MAX_REDIRECT_URIS = 10


def _error(error: str, description: str) -> JsonResponse:
    return JsonResponse({"error": error, "error_description": description}, status=400)


class MCPRegistrationView(DynamicClientRegistrationView):
    """
    The library's RFC 7591 registration endpoint, rate-limited per client IP and
    narrowed to public clients using the authorization code grant with HTTPS or
    loopback redirect URIs.
    """

    def post(self, request, *args, **kwargs):
        limited = rate_limited(MCPOAuthRegistrationRateThrottle(), request, self)
        if limited is not None:
            return limited

        try:
            content_length = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            content_length = 0
        if content_length > MAX_REGISTRATION_BYTES or (
            len(request.body) > MAX_REGISTRATION_BYTES
        ):
            return _error(
                "invalid_client_metadata", "The registration request is too large."
            )

        try:
            metadata = json.loads(request.body)
        except ValueError:
            metadata = None
        if not isinstance(metadata, dict):
            # The library returns the metadata error.
            return super().post(request, *args, **kwargs)

        auth_method = metadata.setdefault("token_endpoint_auth_method", "none")
        if auth_method != "none":
            return _error(
                "invalid_client_metadata",
                "Only public clients (token_endpoint_auth_method none) can register.",
            )
        grant_types = metadata.get("grant_types") or ["authorization_code"]
        if not isinstance(grant_types, list) or not all(
            isinstance(grant, str) and grant in ALLOWED_GRANT_TYPES
            for grant in grant_types
        ):
            return _error(
                "invalid_client_metadata",
                "Only the authorization_code and refresh_token grants are supported.",
            )
        redirect_uris = metadata.get("redirect_uris") or []
        if not isinstance(redirect_uris, list):
            redirect_uris = []
        # Older Cursor builds also send a `cursor://` URI next to the loopback one
        # they use. RFC 7591 lets the server drop the ones it doesn't accept.
        redirect_uris = [uri for uri in redirect_uris if is_allowed_redirect_uri(uri)]
        if not redirect_uris:
            return _error(
                "invalid_redirect_uri",
                "Redirect URIs must use https or a loopback http address.",
            )
        if len(redirect_uris) > MAX_REDIRECT_URIS:
            return _error(
                "invalid_redirect_uri",
                f"At most {MAX_REDIRECT_URIS} redirect URIs can be registered.",
            )
        metadata["redirect_uris"] = redirect_uris

        # The library reads `request.body`, which Django serves from `_body`; give
        # it the defaulted auth method.
        request._body = json.dumps(metadata).encode()
        response = super().post(request, *args, **kwargs)
        if response.status_code != 201:
            return response
        data = json.loads(response.content)
        for field in MANAGEMENT_FIELDS:
            data.pop(field, None)
        return JsonResponse(data, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class RegistrationManagementNotOffered(View):
    """
    Stands in for RFC 7592 management. The library's registration response
    reverses this route's name, so the name must exist. CSRF exempt so PUT and
    DELETE get the 404 too.
    """

    def dispatch(self, request, *args, **kwargs):
        return JsonResponse({"error": "not_found"}, status=404)
