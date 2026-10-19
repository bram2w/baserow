"""Shared HTTP streaming outside Django's request-lifetime executor."""

import asyncio
import io
import re
from contextlib import suppress

from django.core import signals
from django.core.handlers.asgi import ASGIRequest
from django.core.handlers.base import BaseHandler
from django.db import connections
from django.http import JsonResponse
from django.middleware.security import SecurityMiddleware

from asgiref.sync import sync_to_async
from corsheaders.middleware import CorsMiddleware
from loguru import logger

from baserow.config.db_routers import clear_db_state
from baserow.middleware import BaserowCredentialedCorsMiddleware

MAX_CONCURRENT_STREAMS = 100
MAX_BODY_BYTES = 2 * 1024 * 1024
REQUEST_BODY_TIMEOUT_SECONDS = 15.0
_paths: list[tuple[re.Pattern, tuple[str, ...]]] = []
_handler: BaseHandler | None = None


def register_async_stream_path(
    pattern: str, methods: tuple[str, ...] = ("POST",)
) -> None:
    """A product's existing URL/view stays responsible for auth and validation."""

    entry = (re.compile(pattern), methods)
    if entry not in _paths:
        _paths.append(entry)


def _prepare(scope: dict, body: bytes):
    global _handler
    try:
        signals.request_started.send(sender=AsyncStreamingHTTPRouter, scope=scope)
        if _handler is None:
            handler = BaseHandler()
            handler.load_middleware(is_async=False)
            _handler = handler
        request = ASGIRequest(scope, io.BytesIO(body))
        return _handler.get_response(request)
    finally:
        # Django's normal ASGI context owns a thread until the iterator ends.
        # Here all middleware/view work is finished before async following starts.
        clear_db_state()
        connections.close_all()


def _close_response(response):
    try:
        response.close()
    finally:
        connections.close_all()


def _error_response(scope: dict, status: int, error: str):
    request = ASGIRequest(scope, io.BytesIO())
    response = JsonResponse({"error": error}, status=status)
    if status == 503:
        response["Retry-After"] = "1"
    # Rejections happen before a view runs, but must still have the deployment's
    # actual security/CORS policy, including the narrower credentialed origins.
    return BaserowCredentialedCorsMiddleware(
        CorsMiddleware(SecurityMiddleware(lambda request: response))
    )(request)


async def _send_response(response, send):
    headers = [
        (key.lower().encode("ascii"), value.encode("latin1"))
        for key, value in response.items()
    ]
    headers.extend(
        (b"set-cookie", cookie.output(header="").strip().encode("latin1"))
        for cookie in response.cookies.values()
    )
    await send(
        {
            "type": "http.response.start",
            "status": response.status_code,
            "headers": headers,
        }
    )
    if not response.streaming:
        await send({"type": "http.response.body", "body": response.content})
        return
    if not response.is_async:
        raise TypeError("Registered streaming paths must return an async iterator")
    try:
        async for chunk in response.streaming_content:
            await send({"type": "http.response.body", "body": chunk, "more_body": True})
        await send({"type": "http.response.body", "body": b""})
    finally:
        close = getattr(response._iterator, "aclose", None)
        if close:
            await close()


class AsyncStreamingHTTPRouter:
    """Admit long-lived streams separately, before the ordinary REST limiter.

    Only registered methods/paths are intercepted. Preparation runs the existing
    Django middleware and view in a short worker section; waiting/token delivery
    holds neither a DB connection nor a request-specific thread-sensitive context.
    """

    def __init__(self, fallback, *, max_streams: int = MAX_CONCURRENT_STREAMS):
        self.fallback = fallback
        self.max_streams = max_streams
        self.active = 0

    async def __call__(self, scope, receive, send):
        if not any(
            scope["method"] in methods and pattern.fullmatch(scope["path"])
            for pattern, methods in _paths
        ):
            return await self.fallback(scope, receive, send)
        if self.active >= self.max_streams:
            response = _error_response(scope, 503, "ERROR_CHAT_STREAM_CAPACITY")
            await _send_response(response, send)
            return
        self.active += 1
        response = None
        disconnected = None
        streaming = None
        try:
            body = bytearray()
            try:
                # Admission happens before authentication. An unfinished request
                # body must not reserve a long-lived follower slot indefinitely.
                async with asyncio.timeout(REQUEST_BODY_TIMEOUT_SECONDS):
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            return
                        body.extend(message.get("body", b""))
                        if len(body) > MAX_BODY_BYTES or not message.get(
                            "more_body", False
                        ):
                            break
            except TimeoutError:
                response = _error_response(scope, 408, "ERROR_REQUEST_BODY_TIMEOUT")
                await _send_response(response, send)
                return
            if len(body) > MAX_BODY_BYTES:
                response = _error_response(scope, 413, "ERROR_REQUEST_BODY_TOO_LARGE")
                await _send_response(response, send)
                return

            async def wait_for_disconnect():
                while (await receive())["type"] != "http.disconnect":
                    pass

            disconnected = asyncio.create_task(wait_for_disconnect())
            # An already authorized send may commit after a disconnect. Finish its
            # short preparation, close the response, and leave the worker running.
            response = await sync_to_async(_prepare, thread_sensitive=False)(
                scope, bytes(body)
            )
            if disconnected.done():
                return
            streaming = asyncio.create_task(_send_response(response, send))
            await asyncio.wait(
                (streaming, disconnected), return_when=asyncio.FIRST_COMPLETED
            )
            if streaming.done():
                await streaming
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Async stream HTTP response failed ({})", type(exc).__name__)
            # Headers may already be sent. Never attempt a second HTTP response.
        finally:
            try:
                for task in (streaming, disconnected):
                    if task is not None:
                        task.cancel()
                        with suppress(asyncio.CancelledError, Exception):
                            await task
                if response is not None:
                    await sync_to_async(_close_response, thread_sensitive=False)(
                        response
                    )
            finally:
                self.active -= 1
