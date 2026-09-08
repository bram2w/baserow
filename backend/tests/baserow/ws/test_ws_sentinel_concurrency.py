from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from time import monotonic

from django.db import IntegrityError, connections
from django.utils import timezone

import pytest

from baserow.ws import realtime_events
from baserow.ws.models import RealtimeEvent, RealtimeEventHistoryState
from baserow.ws.realtime_events import RealtimeEventHandler


@pytest.mark.django_db(transaction=True)
@pytest.mark.websockets
def test_concurrent_sentinel_promotions_preserve_originals_until_retry(monkeypatch):
    monkeypatch.setattr(realtime_events, "REALTIME_EVENTS_CLEANUP_BATCH_SIZE", 1)
    ids = RealtimeEventHandler.record_events(
        [
            (
                "table-1",
                {
                    "type": "broadcast_to_group",
                    "ignore_web_socket_id": None,
                    "payload": {"type": "rows_updated", "value": value},
                },
            )
            for value in range(2)
        ]
    )
    RealtimeEvent.objects.filter(id__in=ids).update(
        created_at=timezone.now() - timedelta(days=2)
    )
    original = RealtimeEvent.objects.get(pk=ids[-1])
    both_routes_checked = Barrier(2)

    def compact_one():
        db = connections["default"]

        def synchronize(execute, sql, params, many, context):
            result = execute(sql, params, many, context)
            if sql.startswith("SELECT id, sentinel_key, channel_group"):
                # Each transaction locked a different pending original and saw
                # no existing sentinel before either attempts the unique key.
                both_routes_checked.wait(timeout=5)
            return result

        try:
            with db.execute_wrapper(synchronize):
                result = RealtimeEventHandler._compact_realtime_events_batch(
                    timezone.now() - timedelta(days=1), monotonic() + 10
                )
            return "committed", result
        except IntegrityError as error:
            cause = error.__cause__
            return "conflict", getattr(cause, "sqlstate", None) or cause.pgcode
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(compact_one) for _ in range(2)]
        try:
            results = [future.result(timeout=10) for future in futures]
        finally:
            both_routes_checked.abort()

    assert sorted(results) == [("committed", (1, 0)), ("conflict", "23505")]
    assert (
        list(RealtimeEvent.objects.order_by("id").values_list("id", flat=True)) == ids
    )
    assert RealtimeEvent.objects.filter(sentinel_key__isnull=False).count() == 1
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0

    assert RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1)) == 1

    retained = RealtimeEvent.objects.get()
    assert retained.id == original.id
    assert retained.payload == original.payload
    assert retained.created_at == original.created_at
    assert retained.sentinel_key is not None
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0
