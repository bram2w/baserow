from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
    remap_serialized_rows_to_user_field_names,
    serialize_rows_for_response,
)
from baserow.contrib.database.webhooks.registries import WebhookEventType
from baserow.contrib.database.ws.rows.signals import serialize_rows_values

from .signals import rows_created, rows_deleted, rows_updated


class RespectSendWebhookEvents:
    def listener(self, **kwargs: dict):
        """
        The method that is called when the signal is triggered. By default it will
        wait for the transition to commit to call the `listener_after_commit` method.

        :param kwargs: The arguments of the signal.
        """

        # Don't do anything if `send_webhook_events` is provided and `false` because
        # then the webhook must not be triggered.
        if kwargs.get("send_webhook_events", True) is False:
            return

        return super().listener(**kwargs)


class RowsEventType(RespectSendWebhookEvents, WebhookEventType):
    def get_row_serializer(self, webhook, model):
        return get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            user_field_names=webhook.use_user_field_names,
        )

    def get_payload(self, event_id, webhook, model, table, rows, **kwargs):
        payload = super().get_payload(event_id, webhook, **kwargs)
        payload["items"] = self.get_row_serializer(webhook, model)(rows, many=True).data
        return payload


class RowsCreatedEventType(RowsEventType):
    type = "rows.created"
    signal = rows_created

    def get_test_call_payload(self, table, model, event_id, webhook):
        rows = [model(id=0, order=0)]
        payload = self.get_payload(
            event_id=event_id,
            webhook=webhook,
            model=model,
            table=table,
            rows=rows,
        )
        return payload


class RowsUpdatedEventType(RowsEventType):
    type = "rows.updated"
    signal = rows_updated

    def get_payload(
        self, event_id, webhook, model, table, rows, before_return, **kwargs
    ):
        payload = super().get_payload(event_id, webhook, model, table, rows, **kwargs)

        old_items = dict(before_return)[serialize_rows_values]

        if webhook.use_user_field_names:
            old_items = remap_serialized_rows_to_user_field_names(old_items, model)

        payload["old_items"] = old_items

        return payload

    def get_test_call_payload(self, table, model, event_id, webhook):
        rows = [model(id=0, order=0)]
        before_return = {
            serialize_rows_values: serialize_rows_for_response(rows, model)
        }
        payload = self.get_payload(
            event_id=event_id,
            webhook=webhook,
            model=model,
            table=table,
            rows=rows,
            before_return=before_return,
        )
        return payload


class RowsDeletedEventType(RespectSendWebhookEvents, WebhookEventType):
    type = "rows.deleted"
    signal = rows_deleted

    def get_payload(self, event_id, webhook, rows, **kwargs):
        payload = super().get_payload(event_id, webhook, **kwargs)
        payload["row_ids"] = [row.id for row in rows]
        return payload

    def get_test_call_payload(self, table, model, event_id, webhook):
        rows = [model(id=0, order=0)]

        payload = self.get_payload(
            event_id=event_id,
            webhook=webhook,
            model=model,
            table=table,
            rows=rows,
        )
        return payload
