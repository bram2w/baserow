from baserow.contrib.database.api.rows.serializers import (
    get_row_serializer_class,
    remap_serialized_row_to_user_field_names,
    RowSerializer,
)
from baserow.contrib.database.webhooks.registries import WebhookEventType
from baserow.contrib.database.ws.rows.signals import before_row_update
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

    def get_test_call_before_return(self, table, row, model):
        return {
            before_row_update: before_row_update(
                row=row,
                model=model,
                sender=None,
                user=None,
                table=None,
                updated_field_ids=None,
            )
        }

    def get_payload(
        self, event_id, webhook, model, table, row, before_return, **kwargs
    ):
        payload = super().get_payload(event_id, webhook, model, table, row, **kwargs)
        old_values = dict(before_return)[before_row_update]

        if webhook.use_user_field_names:
            old_values = remap_serialized_row_to_user_field_names(old_values, model)

        payload["old_values"] = old_values

        return payload


class RowDeletedEventType(WebhookEventType):
    type = "row.deleted"
    signal = row_deleted

    def get_payload(self, event_id, webhook, row, **kwargs):
        payload = super().get_payload(event_id, webhook, **kwargs)
        payload["row_id"] = row.id
        return payload
