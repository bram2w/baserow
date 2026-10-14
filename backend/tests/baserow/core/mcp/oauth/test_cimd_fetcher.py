import json
import socket
import threading
import time
from unittest.mock import patch

import pytest
import urllib3
from oauth2_provider.cimd import CIMDError

from baserow.core.mcp.oauth.cimd import MCPMetadataFetcher

CLIENT_ID = "https://client.example/client.json"
DOCUMENT = json.dumps(
    {
        "client_id": CLIENT_ID,
        "redirect_uris": ["https://client.example/cb"],
        "token_endpoint_auth_method": "none",
    }
).encode()
HEAD = (
    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
    b"Content-Length: " + str(len(DOCUMENT)).encode() + b"\r\n\r\n"
)


@pytest.fixture(autouse=True)
def cimd_fetch():
    """Replaces the conftest fixture that stubs the download."""

    yield


class PlainHTTPFetcher(MCPMetadataFetcher):
    """Talks plain HTTP so the test server doesn't need a certificate."""

    def _connection(self, ip, port, hostname, timeout):
        return urllib3.connection.HTTPConnection(host=ip, port=port, timeout=timeout)


def _serve(head_delay, body_delay):
    """
    Serves one response from a local socket, sending the head and then the body a
    byte at a time with the given pause after each byte. Returns the port.
    """

    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)

    def run():
        conn, _ = server.accept()
        try:
            conn.recv(4096)
            for data, delay in ((HEAD, head_delay), (DOCUMENT, body_delay)):
                if not delay:
                    conn.sendall(data)
                    continue
                for index in range(len(data)):
                    conn.sendall(data[index : index + 1])
                    time.sleep(delay)
        except OSError:
            pass
        finally:
            conn.close()
            server.close()

    threading.Thread(target=run, daemon=True).start()
    return server.getsockname()[1]


def _fetch(port, settings):
    settings.OAUTH2_PROVIDER = {
        **settings.OAUTH2_PROVIDER,
        "CIMD_FETCH_TIMEOUT_SECONDS": 1,
    }
    with patch(
        "oauth2_provider.cimd._resolve_and_validate", return_value=["127.0.0.1"]
    ):
        return PlainHTTPFetcher().fetch(f"https://client.example:{port}/client.json")


def test_fetch_reads_the_document(settings):
    port = _serve(head_delay=0, body_delay=0)

    metadata, _ = _fetch(port, settings)

    assert metadata == json.loads(DOCUMENT)


@pytest.mark.parametrize(
    "head_delay,body_delay",
    [(0.05, 0), (0, 0.05)],
    ids=["slow-head", "slow-body"],
)
def test_fetch_stops_at_the_deadline(settings, head_delay, body_delay):
    # Each byte arrives well within the read timeout, so only an overall deadline
    # ends the download.
    port = _serve(head_delay=head_delay, body_delay=body_delay)

    started = time.monotonic()
    with pytest.raises(CIMDError):
        _fetch(port, settings)

    assert time.monotonic() - started < 2
