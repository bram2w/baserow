from baserow.contrib.database.api.rows.serializers import (
    get_row_serializer_class,
    RowSerializer,
)
from baserow.contrib.database.webhooks.registries import WebhookEventType

from .signals import row_created, row_updated, row_deleted


class RowEventType(WebhookEventType):
    def get_row_serializer(self, webhook, model):
        return get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            user_field_names=webhook.use_user_field_names,
        )

    def get_payload(self, event_id, webhook, model, table, row, **kwargs):
        payload = super().get_payload(event_id, webhook, **kwargs)
        payload["row_id"] = row.id
        payload["values"] = self.get_row_serializer(webhook, model)(row).data
        return payload


class RowCreatedEventType(RowEventType):
    type = "row.created"
    signal = row_created


class RowUpdatedEventType(RowEventType):
    type = "row.updated"
    signal = row_updated

    def get_payload(
        self, event_id, webhook, model, table, row, before_return, **kwargs
    ):
        payload = super().get_payload(event_id, webhook, model, table, row, **kwargs)
        payload["old_values"] = self.get_row_serializer(webhook, model)(
            before_return
        ).data
        return payload


class RowDeletedEventType(WebhookEventType):
    type = "row.deleted"
    signal = row_deleted

    def get_payload(self, event_id, webhook, row, **kwargs):
        payload = super().get_payload(event_id, webhook, **kwargs)
        payload["row_id"] = row.id
        return payload
