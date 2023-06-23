from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from baserow_premium.row_comments.exceptions import (
    InvalidRowCommentException,
    RowCommentDoesNotExist,
    UserNotRowCommentAuthorException,
)
from baserow_premium.row_comments.models import RowComment
from baserow_premium.row_comments.operations import (
    CreateRowCommentsOperationType,
    DeleteRowCommentsOperationType,
    ReadRowCommentsOperationType,
    UpdateRowCommentsOperationType,
)
from baserow_premium.row_comments.signals import (
    row_comment_created,
    row_comment_deleted,
    row_comment_updated,
)

from baserow.contrib.database.rows.exceptions import RowDoesNotExist
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.core.handler import CoreHandler
from baserow.core.trash.handler import TrashHandler

User = get_user_model()


class RowCommentHandler:
    @classmethod
    def get_comments(
        cls,
        requesting_user: User,
        table_id: int,
        row_id: int,
        include_trashed: bool = False,
    ) -> QuerySet:
        """
        Returns all the row comments for a given row in a table.

        :param requesting_user: The user who is requesting to lookup the row comments.
        :param table_id: The table to find the row in.
        :param row_id: The id of the row to get comments for.
        :param include_trashed: If True, trashed comments will be included in the
            queryset.
        :return: A queryset of all row comments for that particular row.
        :raises TableDoesNotExist: If the table does not exist.
        :raises RowDoesNotExist: If the row does not exist.
        :raises UserNotInWorkspace: If the user is not a member of the workspace that
            the table is in.
        """

        table = TableHandler().get_table(table_id)
        LicenseHandler.raise_if_user_doesnt_have_feature(
            PREMIUM, requesting_user, table.database.workspace
        )
        # TODO: RBAC -> When row level permissions are introduced we also need to check
        #       that the user can see the row
        CoreHandler().check_permissions(
            requesting_user,
            ReadRowCommentsOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        RowHandler().has_row(requesting_user, table, row_id, raise_error=True)

        row_comment_manager = RowComment.objects
        if include_trashed:
            row_comment_manager = RowComment.objects_and_trash

        return (
            row_comment_manager.select_related("user")
            .filter(table_id=table_id, row_id=row_id)
            .all()
        )

    @classmethod
    def get_comment_by_id(
        cls, requesting_user: User, table_id: int, comment_id: int
    ) -> RowComment:
        """
        Returns the row comment for a given comment id.

        :param requesting_user: The user who is requesting to lookup the row
            comments.
        :param table_id: The table to find the row in.
        :param comment_id: The id of the comment to get.
        :return: the comment for that particular row.
        :raises PermissionException: If the user does not have permission to
            read comment on the table.
        :raises RowCommentDoesNotExist: If the comment does not exist.
        """

        table = TableHandler().get_table(table_id)
        LicenseHandler.raise_if_user_doesnt_have_feature(
            PREMIUM, requesting_user, table.database.workspace
        )

        # TODO: RBAC -> When row level permissions are introduced we also need
        #       to check that the user can see the row
        CoreHandler().check_permissions(
            requesting_user,
            ReadRowCommentsOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        queryset = RowComment.objects.select_related("table__database__workspace")

        try:
            row_comment = queryset.get(pk=comment_id)
            RowHandler().has_row(
                requesting_user, table, row_comment.row_id, raise_error=True
            )
        except (RowComment.DoesNotExist, RowDoesNotExist):
            raise RowCommentDoesNotExist()

        return row_comment

    @classmethod
    def create_comment(
        cls, requesting_user: User, table_id: int, row_id: int, comment: str
    ) -> RowComment:
        """
        Creates a new row comment on the specified row.

        :param requesting_user: The user who is making the comment.
        :param table_id: The table to find the row in.
        :param row_id: The id of the row to post the comment on.
        :param comment: The comment to post.
        :return: The newly created RowComment instance.
        :raises TableDoesNotExist: If the table does not exist.
        :raises RowDoesNotExist: If the row does not exist.
        :raises UserNotInWorkspace: If the user is not a member of the workspace that
            the table is in.
        :raises InvalidRowCommentException: If the comment is blank or None.
        """

        table = TableHandler().get_table(table_id)
        LicenseHandler.raise_if_user_doesnt_have_feature(
            PREMIUM, requesting_user, table.database.workspace
        )

        if comment is None or comment == "":
            raise InvalidRowCommentException()

        # TODO: RBAC -> When row level permissions are introduced we also need to check
        #       that the user can see the row
        CoreHandler().check_permissions(
            requesting_user,
            CreateRowCommentsOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        RowHandler().has_row(requesting_user, table, row_id, raise_error=True)
        row_comment = RowComment.objects.create(
            user=requesting_user, table=table, row_id=row_id, comment=comment
        )
        row_comment_created.send(
            RowHandler,
            row_comment=row_comment,
            user=requesting_user,
        )
        return row_comment

    @classmethod
    def update_comment(
        cls, requesting_user: User, row_comment: RowComment, comment_content: str
    ) -> RowComment:
        """
        Updates a new row comment on the specified row.

        :param requesting_user: The user who is making the comment.
        :param row_comment: The comment content for the update.
        :param comment_content: The new content of the comment.
        :return: The updated RowComment instance.
        :raises PermissionException: If the user does not have permission to delete
            the comment.
        :raises UserNotRowCommentAuthorException: If the user is not the author of the
            comment.
        :raises InvalidRowCommentException: If the comment is blank or None.
        """

        table = row_comment.table
        CoreHandler().check_permissions(
            requesting_user,
            UpdateRowCommentsOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        # only the owner of the comment can update it
        if row_comment.user_id != requesting_user.id:
            raise UserNotRowCommentAuthorException()

        if comment_content is None or comment_content == "":
            raise InvalidRowCommentException()

        row_comment.comment = comment_content
        row_comment.save(update_fields=["comment", "updated_on"])

        row_comment_updated.send(
            RowHandler,
            row_comment=row_comment,
            user=requesting_user,
        )
        return row_comment

    @classmethod
    def delete_comment(cls, requesting_user: User, row_comment: RowComment):
        """
        Set a row comment marked as trashed and so it will not be visible to
        users anymore.

        :param requesting_user: The user who is making the comment.
        :param row_comment: The comment to delete.
        :raises PermissionException: If the user does not have permission to delete
            the comment.
        :raises UserNotRowCommentAuthorException: If the user is not the author of the
            comment.
        """

        table = row_comment.table
        database = table.database
        CoreHandler().check_permissions(
            requesting_user,
            DeleteRowCommentsOperationType.type,
            workspace=database.workspace,
            context=table,
        )

        # only the owner of the comment can trash it
        if row_comment.user_id != requesting_user.id:
            raise UserNotRowCommentAuthorException()

        TrashHandler.trash(requesting_user, database.workspace, database, row_comment)

        row_comment_deleted.send(
            RowHandler,
            row_comment=row_comment,
            user=requesting_user,
        )
