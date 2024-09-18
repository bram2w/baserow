from datetime import datetime, timezone

from baserow.contrib.database.webhooks.models import (
    TableWebhook,
    TableWebhookCall,
    TableWebhookEvent,
    TableWebhookHeader,
)


class TableWebhookFixture:
    def create_table_webhook(self, user=None, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "url" not in kwargs:
            kwargs["url"] = self.fake.url()

        events = kwargs.pop("events", [])
        headers = kwargs.pop("headers", {})

        webhook = TableWebhook.objects.create(**kwargs)

        TableWebhookEvent.objects.bulk_create(
            [TableWebhookEvent(webhook=webhook, event_type=event) for event in events]
        )

        TableWebhookHeader.objects.bulk_create(
            [
                TableWebhookHeader(webhook=webhook, name=name, value=value)
                for name, value in headers.items()
            ]
        )

        return webhook

    def create_table_webhook_call(self, user=None, **kwargs):
        if "webhook" not in kwargs:
            kwargs["webhook"] = self.create_table_webhook(user=None)

        if "event_type" not in kwargs:
            kwargs["event_type"] = "rows.created"

        if "called_url" not in kwargs:
            kwargs["called_url"] = self.fake.url()

        if "called_time" not in kwargs:
            kwargs["called_time"] = datetime.now(tz=timezone.utc)

        if "request" not in kwargs:
            kwargs["request"] = "Baserow-header: test\n\n{}"

        if "response" not in kwargs:
            kwargs["response"] = "Baserow-header: test\n\n{}"

        if "response_status" not in kwargs:
            kwargs["response_status"] = 200

        return TableWebhookCall.objects.create(**kwargs)
