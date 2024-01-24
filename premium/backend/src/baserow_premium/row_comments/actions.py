import dataclasses
from typing import Any, Dict

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.contrib.database.action.scopes import (
    TABLE_ACTION_CONTEXT,
    TableActionScopeType,
)
from baserow.contrib.database.table.handler import TableHandler
from baserow.core.action.models import Action
from baserow.core.action.registries import ActionTypeDescription, UndoableActionType
from baserow.core.trash.handler import TrashHandler

from .handler import RowCommentHandler
from .models import RowComment


class CreateRowCommentActionType(UndoableActionType):
    type = "create_row_comment"
    description = ActionTypeDescription(
        _("Create row comment"),
        _("Comment (%(comment_id)s) has been added to row (%(row_id)s)"),
        TABLE_ACTION_CONTEXT,
    )
    analytics_params = [
        "comment_id",
        "row_id",
        "table_id",
        "database_id",
        "workspace_id",
    ]

    @dataclasses.dataclass
    class Params:
        comment_id: int
        message: Dict[str, Any]
        row_id: int
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        workspace_id: int
        workspace_name: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        table_id: int,
        row_id: int,
        message: Dict[str, Any],
    ) -> RowComment:
        """
        Creates a new comment for the given row.
        Look at .handler.RowCommentHandler.create_comment for
        more information about the parameters.
        Undo this action soft-delete this comment.
        Redo this action will restore the comment.
        """

        row_comment = RowCommentHandler.create_comment(user, table_id, row_id, message)

        table = TableHandler().get_table(table_id)
        database = table.database
        workspace = database.workspace

        cls.register_action(
            user,
            cls.Params(
                row_comment.id,
                row_comment.message,
                row_id,
                table.id,
                table.name,
                database.id,
                database.name,
                workspace.id,
                workspace.name,
            ),
            cls.scope(table_id),
            workspace,
        )
        return row_comment

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        row_comment = RowCommentHandler.get_comment_by_id(
            user, params.table_id, params.comment_id
        )
        RowCommentHandler.delete_comment(user, row_comment)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TrashHandler.restore_item(
            user, "row_comment", params.comment_id, parent_trash_item_id=None
        )

    @classmethod
    def scope(cls, table_id: int):
        return TableActionScopeType.value(table_id)


class UpdateRowCommentActionType(UndoableActionType):
    type = "update_row_comment"
    description = ActionTypeDescription(
        _("Update row comment"),
        _("Comment (%(comment_id)s) has been updated in row (%(row_id)s)"),
        TABLE_ACTION_CONTEXT,
    )
    analytics_params = [
        "comment_id",
        "row_id",
        "table_id",
        "database_id",
        "workspace_id",
    ]

    @dataclasses.dataclass
    class Params:
        comment_id: int
        message: Dict[str, Any]
        row_id: int
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        workspace_id: int
        workspace_name: str
        original_message: Dict[str, Any]

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        table_id: int,
        row_comment_id: int,
        comment_content: str,
    ) -> RowComment:
        """
        Updates a comment with the given comment_content.
        Look at .handler.RowCommentHandler.update_comment for
        more information about the parameters.
        Undo this action will restore the original comment_content.
        Redo this action will update the comment_content again.
        """

        row_comment = RowCommentHandler.get_comment_by_id(
            user, table_id, row_comment_id
        )

        table = row_comment.table
        database = table.database
        workspace = database.workspace
        original_message = row_comment.message

        updated_comment = RowCommentHandler.update_comment(
            user, row_comment, comment_content
        )

        cls.register_action(
            user,
            cls.Params(
                row_comment.id,
                updated_comment.message,
                row_comment.row_id,
                table.id,
                table.name,
                database.id,
                database.name,
                workspace.id,
                workspace.name,
                original_message,
            ),
            cls.scope(table_id),
            workspace,
        )
        return row_comment

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        row_comment = RowCommentHandler.get_comment_by_id(
            user, params.table_id, params.comment_id
        )
        RowCommentHandler.update_comment(user, row_comment, params.original_message)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        row_comment = RowCommentHandler.get_comment_by_id(
            user, params.table_id, params.comment_id
        )
        RowCommentHandler.update_comment(user, row_comment, params.message)

    @classmethod
    def scope(cls, table_id: int):
        return TableActionScopeType.value(table_id)


class DeleteRowCommentActionType(UndoableActionType):
    type = "delete_row_comment"
    description = ActionTypeDescription(
        _("Delete row comment"),
        _("Comment (%(comment_id)s) has been deleted from row (%(row_id)s)"),
        TABLE_ACTION_CONTEXT,
    )
    analytics_params = [
        "comment_id",
        "row_id",
        "table_id",
        "database_id",
        "workspace_id",
    ]

    @dataclasses.dataclass
    class Params:
        comment_id: int
        message: Dict[str, Any]
        row_id: int
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        workspace_id: int
        workspace_name: str

    @classmethod
    def do(cls, user: AbstractUser, table_id: int, row_comment_id: int) -> RowComment:
        """
        Deletes a comment from the given row.
        Look at .handler.RowCommentHandler.delete_comment for
        more information about the parameters.
        Undo this action will restore the visibility of the comment.
        Redo this action soft-delete this comment.
        """

        row_comment = RowCommentHandler.get_comment_by_id(
            user, table_id, row_comment_id
        )
        RowCommentHandler.delete_comment(user, row_comment)

        table = row_comment.table
        database = table.database
        workspace = database.workspace

        cls.register_action(
            user,
            cls.Params(
                row_comment.id,
                row_comment.message,
                row_comment.row_id,
                table.id,
                table.name,
                database.id,
                database.name,
                workspace.id,
                workspace.name,
            ),
            cls.scope(table_id),
            workspace,
        )
        return row_comment

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        TrashHandler.restore_item(
            user, "row_comment", params.comment_id, parent_trash_item_id=None
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        row_comment = RowCommentHandler.get_comment_by_id(
            user, params.table_id, params.comment_id
        )
        RowCommentHandler.delete_comment(user, row_comment)

    @classmethod
    def scope(cls, table_id: int):
        return TableActionScopeType.value(table_id)
