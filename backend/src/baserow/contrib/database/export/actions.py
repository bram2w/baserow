import dataclasses
from typing import Any, Dict, Optional

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.contrib.database.action.scopes import (
    DATABASE_ACTION_CONTEXT,
    TABLE_ACTION_CONTEXT,
    TableActionScopeType,
)
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.models import View
from baserow.core.action.registries import ActionType, ActionTypeDescription


class ExportTableActionType(ActionType):
    type = "export_table"
    description = ActionTypeDescription(
        _("Export Table"),
        _('View "%(view_name)s" (%(view_id)s) exported to %(export_type)s'),
        TABLE_ACTION_CONTEXT,
    )
    analytics_params = [
        "table_id",
        "export_type",
        "database_id",
        "workspace_id",
        "view_id",
    ]

    @dataclasses.dataclass
    class Params:
        table_id: int
        table_name: str
        export_type: str
        database_id: int
        database_name: str
        workspace_id: int
        workspace_name: str
        view_id: Optional[int]
        view_name: Optional[str]

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        table: Table,
        export_type: str,
        view: Optional[View] = None,
    ):
        """
        Creates a new webhook for the given table.
        Look at .handler.WebhookHandler.create_table_webhook for
        more information about the parameters.
        """

        database = table.database
        workspace = database.workspace
        view_id, view_name = None, None
        if view:
            view_id, view_name = view.id, view.name

        cls.register_action(
            user,
            cls.Params(
                table.id,
                table.name,
                export_type.upper(),
                database.id,
                database.name,
                workspace.id,
                workspace.name,
                view_id,
                view_name,
            ),
            cls.scope(workspace.id),
            workspace,
        )

    @classmethod
    def scope(cls, table_id: int):
        return TableActionScopeType.value(table_id)

    @classmethod
    def get_long_description(cls, params_dict: Dict[str, Any], *args, **kwargs) -> str:
        if params_dict.get("view_id") is None:
            long_descr = _(
                'Table "%(table_name)s" (%(table_id)s) exported to %(export_type)s'
            )
            return f"{long_descr % params_dict} {DATABASE_ACTION_CONTEXT % params_dict}"
        return super().get_long_description(params_dict, *args, **kwargs)
