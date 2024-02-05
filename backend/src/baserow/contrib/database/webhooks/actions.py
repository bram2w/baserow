import dataclasses

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.contrib.database.action.scopes import (
    TABLE_ACTION_CONTEXT,
    TableActionScopeType,
)
from baserow.contrib.database.table.models import Table
from baserow.core.action.registries import ActionType, ActionTypeDescription

from .handler import WebhookHandler
from .models import TableWebhook


class CreateWebhookActionType(ActionType):
    type = "create_webhook"
    description = ActionTypeDescription(
        _("Create Webhook"),
        _(
            'Webhook "%(webhook_name)s" (%(webhook_id)s) as %(webhook_request_method)s '
            'to %(webhook_url)s" created'
        ),
        TABLE_ACTION_CONTEXT,
    )
    analytics_params = [
        "webhook_id",
        "webhook_request_method",
        "table_id",
        "database_id",
        "workspace_id",
    ]

    @dataclasses.dataclass
    class Params:
        webhook_id: int
        webhook_name: str
        webhook_request_method: str
        webhook_url: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        workspace_id: int
        workspace_name: str

    @classmethod
    def do(cls, user: AbstractUser, table: Table, **kwargs) -> TableWebhook:
        """
        Creates a new webhook for the given table.
        Look at .handler.WebhookHandler.create_table_webhook for
        more information about the parameters.
        """

        webhook = WebhookHandler().create_table_webhook(user, table, **kwargs)

        database = table.database
        workspace = database.workspace

        cls.register_action(
            user,
            cls.Params(
                webhook.id,
                webhook.name,
                webhook.request_method,
                webhook.url,
                table.id,
                table.name,
                database.id,
                database.name,
                workspace.id,
                workspace.name,
            ),
            cls.scope(table.id),
            workspace,
        )
        return webhook

    @classmethod
    def scope(cls, table_id: int):
        return TableActionScopeType.value(table_id)


class DeleteWebhookActionType(ActionType):
    type = "delete_webhook"
    description = ActionTypeDescription(
        _("Delete Webhook"),
        _(
            'Webhook "%(webhook_name)s" (%(webhook_id)s) as %(webhook_request_method)s '
            'to %(webhook_url)s" deleted'
        ),
        TABLE_ACTION_CONTEXT,
    )
    analytics_params = [
        "webhook_id",
        "webhook_request_method",
        "table_id",
        "database_id",
        "workspace_id",
    ]

    @dataclasses.dataclass
    class Params:
        webhook_id: int
        webhook_name: str
        webhook_request_method: str
        webhook_url: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        workspace_id: int
        workspace_name: str

    @classmethod
    def do(cls, user: AbstractUser, webhook: TableWebhook, **kwargs):
        """
        Deletes the webhook for the given table.
        Look at .handler.WebhookHandler.delete_table_webhook for
        more information about the parameters.
        """

        table = webhook.table
        database = table.database
        workspace = database.workspace
        params = cls.Params(
            webhook.id,
            webhook.name,
            webhook.request_method,
            webhook.url,
            table.id,
            table.name,
            database.id,
            database.name,
            workspace.id,
            workspace.name,
        )

        WebhookHandler().delete_table_webhook(user, webhook)

        cls.register_action(user, params, cls.scope(table.id), workspace)

    @classmethod
    def scope(cls, table_id: int):
        return TableActionScopeType.value(table_id)


class UpdateWebhookActionType(ActionType):
    type = "update_webhook"
    description = ActionTypeDescription(
        _("Update Webhook"),
        _(
            'Webhook "%(webhook_name)s" (%(webhook_id)s) as %(webhook_request_method)s '
            'to %(webhook_url)s" updated'
        ),
        TABLE_ACTION_CONTEXT,
    )
    analytics_params = [
        "webhook_id",
        "webhook_request_method",
        "original_webhook_request_method",
        "table_id",
        "database_id",
        "workspace_id",
    ]

    @dataclasses.dataclass
    class Params:
        webhook_id: int
        webhook_name: str
        webhook_request_method: str
        webhook_url: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        workspace_id: int
        workspace_name: str
        original_webhook_name: str
        original_webhook_request_method: str
        original_webhook_url: str

    @classmethod
    def do(cls, user: AbstractUser, webhook: TableWebhook, **data) -> TableWebhook:
        """
        Updates the webhook for the given table.
        Look at .handler.WebhookHandler.update_table_webhook for
        more information about the parameters.
        """

        original_data = {
            k: getattr(webhook, k) for k in ["name", "request_method", "url"]
        }

        webhook = WebhookHandler().update_table_webhook(user, webhook, **data)

        table = webhook.table
        database = table.database
        workspace = database.workspace
        params = cls.Params(
            webhook.id,
            webhook.name,
            webhook.request_method,
            webhook.url,
            table.id,
            table.name,
            database.id,
            database.name,
            workspace.id,
            workspace.name,
            original_webhook_name=original_data["name"],
            original_webhook_request_method=original_data["request_method"],
            original_webhook_url=original_data["url"],
        )

        cls.register_action(user, params, cls.scope(table.id), workspace)
        return webhook

    @classmethod
    def scope(cls, table_id: int):
        return TableActionScopeType.value(table_id)
