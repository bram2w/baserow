"""Replay and follow background chat-run output over HTTP."""

import asyncio
from typing import Any, AsyncIterator, Callable

from django.contrib.auth import get_user_model
from django.db import connections

from asgiref.sync import sync_to_async

from baserow.config.db_routers import clear_db_state, set_db_alias

from .buffer import (
    READ_BLOCK_MILLISECONDS,
    ChatRunBuffer,
    ReplayUnavailable,
    parse_cursor,
    stream_id_key,
)
from .exceptions import ChatRunDoesNotExist
from .models import ACTIVE_CHAT_RUN_STATUSES

STATUS_INTERVAL_SECONDS = 5.0


def _fresh_snapshot(user: Any, run_id: Any) -> dict:
    from .service import ChatRunService

    try:
        # Do not keep a cached active/permission state for a long-lived response.
        set_db_alias("default")
        fresh_user = (
            get_user_model()
            .objects.using("default")
            .select_related("profile")
            .get(pk=user.pk)
        )
        if not fresh_user.is_active:
            raise ChatRunDoesNotExist()
        return ChatRunService().snapshot(fresh_user, run_id)
    except get_user_model().DoesNotExist:
        raise ChatRunDoesNotExist() from None
    finally:
        clear_db_state()
        connections.close_all()


def _fold(events: list[dict]) -> dict:
    text, segment, progress, variant = "", None, None, None
    for event in events:
        data = event["data"]
        if event["kind"] == "text.delta":
            if segment != data["segment"]:
                text, segment = "", data["segment"]
            text += data["text"]
            variant = data.get("variant")
        elif event["kind"] == "progress":
            progress = data
    return {"text": text, "segment": segment, "progress": progress, "variant": variant}


async def follow_run(
    run: Any,
    user: Any,
    cursor: str | None = None,
    *,
    replay: bool = True,
    snapshot: Callable | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Yield ordered output, compatible heartbeats, and authoritative completion.

    ``snapshot`` is an optional async callback for consumers/tests with their own
    permission context; the default rechecks the product's read permission on the
    primary. Redis failures never restart work, and never prevent durable recovery.
    ``replay=False`` is only for the response which created a brand-new run.
    """

    if cursor:
        parse_cursor(cursor)
    buffer = ChatRunBuffer(run.id)

    async def get_snapshot():
        if snapshot is not None:
            return await snapshot()
        return await sync_to_async(_fresh_snapshot, thread_sensitive=False)(
            user, run.id
        )

    state = await get_snapshot()
    if state["status"] not in ACTIVE_CHAT_RUN_STATUSES:
        yield {
            "kind": "run.finished",
            "data": state,
            "cursor": cursor,
            "replayed": True,
        }
        return
    next_status = asyncio.get_running_loop().time() + STATUS_INTERVAL_SECONDS
    high_water: tuple[int, int] | None = None
    attached = False
    unavailable_reported = False
    invalid_cursor = False
    baseline_needed = bool(cursor)
    while True:
        now = asyncio.get_running_loop().time()
        if now >= next_status:
            state = await get_snapshot()
            next_status = asyncio.get_running_loop().time() + STATUS_INTERVAL_SECONDS
            if state["status"] not in ACTIVE_CHAT_RUN_STATUSES:
                yield {
                    "kind": "run.finished",
                    "data": state,
                    "cursor": cursor,
                    "replayed": True,
                }
                return
        try:
            if invalid_cursor:
                await asyncio.sleep(READ_BLOCK_MILLISECONDS / 1000)
                batch = None
            else:
                batch = await buffer.read(cursor, block_ms=READ_BLOCK_MILLISECONDS)
                if not attached:
                    if replay and batch.high_water:
                        high_water = stream_id_key(parse_cursor(batch.high_water)[1])
                    attached = True
                if baseline_needed:
                    prefix = await buffer.recover(cursor)
                    if prefix is None:
                        raise ReplayUnavailable("prefix")
                    baseline = _fold(prefix)
                    del prefix
                    yield {
                        "kind": "run.baseline",
                        "data": baseline,
                        "cursor": cursor,
                        "replayed": True,
                    }
                    del baseline
                    baseline_needed = False
            # A terminal commit may have happened while XREAD was blocked. Once
            # observed it wins; no subsequent Redis event can modify the answer.
            if asyncio.get_running_loop().time() >= next_status:
                state = await get_snapshot()
                next_status = (
                    asyncio.get_running_loop().time() + STATUS_INTERVAL_SECONDS
                )
                if state["status"] not in ACTIVE_CHAT_RUN_STATUSES:
                    yield {
                        "kind": "run.finished",
                        "data": state,
                        "cursor": cursor,
                        "replayed": True,
                    }
                    return
            had_events = bool(batch and batch.events)
            for event in batch.events if batch else []:
                cursor = event["cursor"]
                if event["kind"] == "run.finished":
                    state = await get_snapshot()
                    if state["status"] not in ACTIVE_CHAT_RUN_STATUSES:
                        yield {
                            "kind": "run.finished",
                            "data": state,
                            "cursor": cursor,
                            "replayed": True,
                        }
                        return
                    continue
                position = stream_id_key(parse_cursor(cursor)[1])
                yield {
                    **event,
                    "replayed": high_water is not None and position <= high_water,
                }
            # Do not pin the previous replay page while the next XREAD blocks.
            batch = None
            event = None
            if not had_events:
                yield {
                    "kind": "run.heartbeat",
                    "data": {},
                    "cursor": cursor,
                    "replayed": False,
                }
        except (ReplayUnavailable, ConnectionError, TimeoutError, OSError) as exc:
            reason = exc.reason if isinstance(exc, ReplayUnavailable) else "connection"
            if not unavailable_reported:
                yield {
                    "kind": "run.replay_unavailable",
                    "data": {"reason": reason},
                    "cursor": cursor,
                    "replayed": True,
                }
                unavailable_reported = True
            # A newly queued run might not have its first stream event yet. Only
            # an empty attachment may later begin with a complete new prefix.
            invalid_cursor = cursor is not None or reason not in (
                "missing",
                "connection",
            )
            await asyncio.sleep(min(1.0, STATUS_INTERVAL_SECONDS))
        except Exception as exc:
            # redis-py uses its own ConnectionError hierarchy. Keep product/auth
            # failures visible; only buffer-client failures enter waiting mode.
            from redis.exceptions import RedisError

            if not isinstance(exc, RedisError):
                raise
            if not unavailable_reported:
                yield {
                    "kind": "run.replay_unavailable",
                    "data": {"reason": "connection"},
                    "cursor": cursor,
                    "replayed": True,
                }
                unavailable_reported = True
            invalid_cursor = cursor is not None
            await asyncio.sleep(min(1.0, STATUS_INTERVAL_SECONDS))
