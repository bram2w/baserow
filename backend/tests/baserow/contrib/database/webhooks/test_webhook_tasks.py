import pytest
import responses

from celery.exceptions import Retry
from django.test import override_settings
from django.db import transaction

from baserow.contrib.database.webhooks.models import TableWebhookCall
from baserow.contrib.database.webhooks.tasks import call_webhook


@pytest.mark.django_db(transaction=True)
@responses.activate
@override_settings(
    WEBHOOKS_MAX_RETRIES_PER_CALL=1, WEBHOOKS_MAX_CONSECUTIVE_TRIGGER_FAILURES=1
)
def test_call_webhook(data_fixture):
    webhook = data_fixture.create_table_webhook()

    call_webhook.run(
        webhook_id=0,
        event_id="00000000-0000-0000-0000-000000000000",
        event_type="row.created",
        method="POST",
        url="http://localhost/",
        headers={"Baserow-header-1": "Value 1"},
        payload={"type": "row.created"},
    )
    assert TableWebhookCall.objects.all().count() == 0

    with pytest.raises(Retry):
        call_webhook.run(
            webhook_id=webhook.id,
            event_id="00000000-0000-0000-0000-000000000000",
            event_type="row.created",
            method="POST",
            url="http://localhost/",
            headers={"Baserow-header-1": "Value 1"},
            payload={"type": "row.created"},
        )
        transaction.commit()

    assert TableWebhookCall.objects.all().count() == 1
    created_call = TableWebhookCall.objects.all().first()
    called_time_1 = created_call.called_time
    assert created_call.webhook_id == webhook.id
    assert created_call.event_type == "row.created"
    assert created_call.called_time
    assert created_call.called_url == "http://localhost/"
    assert "POST http://localhost/" in created_call.request
    assert created_call.response is None
    assert created_call.response_status is None
    assert "Connection refused by Responses" in created_call.error

    call_webhook.push_request(retries=1)
    call_webhook.run(
        webhook_id=webhook.id,
        event_id="00000000-0000-0000-0000-000000000000",
        event_type="row.created",
        method="POST",
        url="http://localhost/",
        headers={"Baserow-header-1": "Value 1"},
        payload={"type": "row.created"},
    )

    webhook.refresh_from_db()
    assert webhook.failed_triggers == 1

    assert TableWebhookCall.objects.all().count() == 1
    created_call = TableWebhookCall.objects.all().first()
    assert created_call.called_time != called_time_1

    call_webhook.push_request(retries=1)
    call_webhook.run(
        webhook_id=webhook.id,
        event_id="00000000-0000-0000-0000-000000000001",
        event_type="row.created",
        method="POST",
        url="http://localhost/",
        headers={"Baserow-header-1": "Value 1"},
        payload={"type": "row.created"},
    )

    webhook.refresh_from_db()
    assert webhook.failed_triggers == 1
    assert webhook.active is False
    assert TableWebhookCall.objects.all().count() == 2

    responses.add(responses.POST, "http://localhost/", json={}, status=200)

    call_webhook.push_request(retries=0)
    call_webhook(
        webhook_id=webhook.id,
        event_id="00000000-0000-0000-0000-000000000002",
        event_type="row.created",
        method="POST",
        url="http://localhost/",
        headers={"Baserow-header-1": "Value 1"},
        payload={"type": "row.created"},
    )

    assert TableWebhookCall.objects.all().count() == 3
    created_call = TableWebhookCall.objects.all().first()
    assert created_call.webhook_id == webhook.id
    assert created_call.event_type == "row.created"
    assert created_call.called_time
    assert created_call.called_url == "http://localhost/"
    assert "POST http://localhost/" in created_call.request
    assert "{}" in created_call.response
    assert created_call.response_status == 200
    assert created_call.error == ""

    webhook.refresh_from_db()
    assert webhook.failed_triggers == 0

    responses.add(responses.POST, "http://localhost2/", json={}, status=400)
    call_webhook.push_request(retries=0)

    with pytest.raises(Retry):
        call_webhook(
            webhook_id=webhook.id,
            event_id="00000000-0000-0000-0000-000000000003",
            event_type="row.created",
            method="POST",
            url="http://localhost2/",
            headers={"Baserow-header-1": "Value 1"},
            payload={"type": "row.created"},
        )

    assert TableWebhookCall.objects.all().count() == 4
    created_call = TableWebhookCall.objects.all().first()
    assert created_call.webhook_id == webhook.id
    assert created_call.event_type == "row.created"
    assert created_call.called_time
    assert created_call.called_url == "http://localhost2/"
    assert "POST http://localhost2/" in created_call.request
    assert "{}" in created_call.response
    assert created_call.response_status == 400
    assert created_call.error == ""
