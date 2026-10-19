import asyncio
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from django.http import JsonResponse, StreamingHttpResponse
from django.urls import reverse

import pytest
from asgiref.sync import SyncToAsync

from baserow.config import streaming
from baserow.config.streaming import AsyncStreamingHTTPRouter


def _scope(path="/stream/", method="POST", origin=None):
    return {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [(b"host", b"testserver")]
        + ([(b"origin", origin.encode())] if origin else []),
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 1000),
        "scheme": "http",
    }


@pytest.mark.asyncio
async def test_http_stream_admission_does_not_hold_rest_capacity_or_thread_context(
    monkeypatch,
):
    monkeypatch.setattr(streaming, "_paths", [])
    streaming.register_async_stream_path(r"/stream/")
    prepared = asyncio.Event()
    closed = asyncio.Event()
    observed_contexts = []

    async def chunks():
        observed_contexts.append(SyncToAsync.thread_sensitive_context.get(None))
        prepared.set()
        try:
            await asyncio.Event().wait()
            yield b"unused"
        finally:
            closed.set()

    monkeypatch.setattr(
        streaming, "_prepare", lambda scope, body: StreamingHttpResponse(chunks())
    )
    fallback = AsyncMock()
    router = AsyncStreamingHTTPRouter(fallback, max_streams=1)
    incoming = asyncio.Queue()
    await incoming.put({"type": "http.request", "body": b"{}"})
    output = []
    active = asyncio.create_task(
        router(_scope(), incoming.get, AsyncMock(side_effect=output.append))
    )
    await asyncio.wait_for(prepared.wait(), 1)
    assert router.active == 1
    assert observed_contexts == [None]

    rejection = []
    await router(
        _scope(origin="https://frontend.example"),
        AsyncMock(),
        AsyncMock(side_effect=rejection.append),
    )
    assert rejection[0]["status"] == 503
    assert b"access-control-allow-origin" in dict(rejection[0]["headers"])
    assert dict(rejection[0]["headers"])[b"retry-after"] == b"1"
    await router(_scope("/ordinary/", "GET"), AsyncMock(), AsyncMock())
    fallback.assert_awaited_once()
    await incoming.put({"type": "http.disconnect"})
    await asyncio.wait_for(active, 1)
    assert router.active == 0
    assert closed.is_set()


@pytest.mark.asyncio
async def test_failed_http_iterator_releases_admission_and_closes_response(monkeypatch):
    monkeypatch.setattr(streaming, "_paths", [])
    streaming.register_async_stream_path(r"/stream/")
    closed = []

    async def chunks():
        raise RuntimeError("broken translator")
        yield b"unreachable"

    response = StreamingHttpResponse(chunks())
    response._resource_closers.append(lambda: closed.append(True))
    monkeypatch.setattr(streaming, "_prepare", lambda scope, body: response)
    incoming = asyncio.Queue()
    await incoming.put({"type": "http.request", "body": b"{}"})
    router = AsyncStreamingHTTPRouter(AsyncMock(), max_streams=1)
    await asyncio.wait_for(router(_scope(), incoming.get, AsyncMock()), 1)
    assert router.active == 0
    assert closed == [True]


@pytest.mark.asyncio
@pytest.mark.parametrize("incomplete,status", [(True, 408), (False, 413)])
async def test_initial_body_limits_release_admission_before_authentication(
    monkeypatch, incomplete, status
):
    monkeypatch.setattr(streaming, "_paths", [])
    streaming.register_async_stream_path(r"/stream/")
    monkeypatch.setattr(streaming, "REQUEST_BODY_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(streaming, "MAX_BODY_BYTES", 3)
    prepare = Mock()
    monkeypatch.setattr(streaming, "_prepare", prepare)
    incoming = asyncio.Queue()
    await incoming.put(
        {
            "type": "http.request",
            "body": b"{" if incomplete else b"1234",
            "more_body": incomplete,
        }
    )
    output = []
    router = AsyncStreamingHTTPRouter(AsyncMock(), max_streams=1)
    await asyncio.wait_for(
        router(
            _scope(origin="https://frontend.example"),
            incoming.get,
            AsyncMock(side_effect=output.append),
        ),
        1,
    )
    assert output[0]["status"] == status
    headers = dict(output[0]["headers"])
    assert b"access-control-allow-origin" in headers
    assert headers[b"x-content-type-options"] == b"nosniff"
    assert router.active == 0
    prepare.assert_not_called()


@pytest.mark.asyncio
async def test_nonstream_validation_response_is_preserved(monkeypatch):
    monkeypatch.setattr(streaming, "_paths", [])
    streaming.register_async_stream_path(r"/stream/")
    response = JsonResponse({"error": "ERROR_REQUEST_BODY_VALIDATION"}, status=400)
    monkeypatch.setattr(streaming, "_prepare", lambda scope, body: response)
    incoming = asyncio.Queue()
    await incoming.put({"type": "http.request", "body": b"{}"})
    output = []
    router = AsyncStreamingHTTPRouter(AsyncMock())
    await asyncio.wait_for(
        router(_scope(), incoming.get, AsyncMock(side_effect=output.append)), 1
    )
    assert output[0]["status"] == 400
    assert output[-1]["body"] == response.content
    assert router.active == 0


@pytest.mark.asyncio
async def test_detached_preparation_preserves_real_django_authentication_and_cors(
    monkeypatch,
):
    path = reverse("api:chat_runs:detail", kwargs={"run_id": uuid4()})
    monkeypatch.setattr(streaming, "_paths", [])
    streaming.register_async_stream_path(path, methods=("GET",))
    incoming = asyncio.Queue()
    await incoming.put({"type": "http.request", "body": b"{}"})
    output = []
    router = AsyncStreamingHTTPRouter(AsyncMock())
    await asyncio.wait_for(
        router(
            _scope(path, method="GET", origin="https://frontend.example"),
            incoming.get,
            AsyncMock(side_effect=output.append),
        ),
        2,
    )
    assert output[0]["status"] == 401
    headers = dict(output[0]["headers"])
    assert b"access-control-allow-origin" in headers
    assert headers[b"x-content-type-options"] == b"nosniff"
    assert router.active == 0
