import dataclasses

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.contrib.database.action.scopes import (
    TABLE_ACTION_CONTEXT,
    TableActionScopeType,
)
from baserow.contrib.database.table.handler import TableHandler
from baserow.core.action.registries import ActionType, ActionTypeDescription

from .handler import RowCommentHandler
from .models import RowComment


class CreateRowCommentActionType(ActionType):
    type = "create_row_comment"
    description = ActionTypeDescription(
        _("Create row comment"),
        _("Comment (%(comment_id)s) has been added to row (%(row_id)s)"),
        TABLE_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        comment_id: int
        comment_content: str
        row_id: int
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        group_id: int
        group_name: str

    @classmethod
    def do(
        cls, user: AbstractUser, table_id: int, row_id: int, comment: str
    ) -> RowComment:
        """
        Creates a new comment for the given row.
        Look at .handler.RowCommentHandler.create_row_comment for
        more information about the parameters.
        """

        row_comment = RowCommentHandler().create_comment(
            user, table_id, row_id, comment
        )

        table = TableHandler().get_table(table_id)
        database = table.database
        group = database.group

        cls.register_action(
            user,
            cls.Params(
                row_comment.id,
                comment,
                row_id,
                table.id,
                table.name,
                database.id,
                database.name,
                group.id,
                group.name,
            ),
            cls.scope(table_id),
            group,
        )
        return row_comment

    @classmethod
    def scope(cls, table_id: int):
        return TableActionScopeType.value(table_id)
