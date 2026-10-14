from oauth2_provider.cimd import SafeMetadataFetcher

from .validators import ALLOWED_GRANT_TYPES


class MCPMetadataFetcher(SafeMetadataFetcher):
    """
    The library's CIMD fetcher, with the document adjusted so django-oauth-toolkit
    3.4.1 accepts the MCP clients in use. It only reads the singular
    `token_endpoint_auth_method`, which ChatGPT sets to `private_key_jwt` while also
    listing `none` in `token_endpoint_auth_methods_supported`, and it refuses the
    extra grant types Claude and VS Code declare.

    TODO: remove once a django-oauth-toolkit release includes #1856 and #1858.
    """

    def fetch(self, client_id):
        metadata, max_age = super().fetch(client_id)

        auth_methods = metadata.get("token_endpoint_auth_methods_supported")
        if isinstance(auth_methods, list) and "none" in auth_methods:
            metadata["token_endpoint_auth_method"] = "none"

        grant_types = metadata.get("grant_types")
        if isinstance(grant_types, list):
            metadata["grant_types"] = [
                grant
                for grant in grant_types
                if isinstance(grant, str) and grant in ALLOWED_GRANT_TYPES
            ]

        return metadata, max_age
