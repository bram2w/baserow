import http.client
import socket
import ssl
import threading
import time

import urllib3
from oauth2_provider import cimd
from oauth2_provider.settings import oauth2_settings

from .validators import ALLOWED_GRANT_TYPES


def _shut_down(connection):
    """Unblocks a read on `connection` from another thread."""

    sock = connection.sock
    if sock is not None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass


class MCPMetadataFetcher(cimd.SafeMetadataFetcher):
    """
    The library's CIMD fetcher with two changes for django-oauth-toolkit 3.4.1.

    The whole download gets one deadline. The library's timeout applies to each
    read, so a document sent a byte at a time holds the worker far longer, and the
    fetch runs for anonymous callers.

    The document is adjusted so the MCP clients in use are accepted. The library
    only reads the singular `token_endpoint_auth_method`, which ChatGPT sets to
    `private_key_jwt` while also listing `none` in
    `token_endpoint_auth_methods_supported`, and it refuses the extra grant types
    Claude and VS Code declare.

    TODO: drop the adjustments once a django-oauth-toolkit release includes #1856
    and #1858.
    """

    def fetch(self, client_id):
        metadata, max_age = self.download(client_id)

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

    def download(self, client_id):
        """
        Fetches the document like the library does: https only, to an IP that was
        resolved and checked once, no redirects, with the size and content type
        checks of `_read_document`.
        """

        parsed = cimd._validate_client_id_url(client_id)
        port = parsed.port or 443
        ips = cimd._resolve_and_validate(parsed.hostname, port)
        path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
        headers = {
            "Host": parsed.netloc,
            "Accept": "application/json, application/*+json",
        }
        deadline = time.monotonic() + oauth2_settings.CIMD_FETCH_TIMEOUT_SECONDS

        last_error = None
        for ip in ips:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            connection = self._connection(ip, port, parsed.hostname, remaining)
            # Closing the socket when the time is up ends whatever read is waiting.
            watchdog = threading.Timer(remaining, _shut_down, args=(connection,))
            watchdog.start()
            try:
                connection.request("GET", path, headers=headers, preload_content=False)
                return self._read_document(connection.getresponse())
            except (
                OSError,
                http.client.HTTPException,
                urllib3.exceptions.HTTPError,
            ) as error:
                last_error = error
            finally:
                watchdog.cancel()
                connection.close()

        if time.monotonic() >= deadline:
            raise cimd.CIMDError("client_id document took too long to download")
        raise cimd.CIMDError(f"could not fetch client_id document: {last_error}")

    def _connection(self, ip, port, hostname, timeout):
        # Connects to the checked IP while SNI, certificate verification and the
        # Host header use the hostname.
        return urllib3.connection.HTTPSConnection(
            host=ip,
            port=port,
            timeout=timeout,
            ssl_context=ssl.create_default_context(),
            server_hostname=hostname,
        )
