import dataclasses
from typing import List, Optional, Any

from django.contrib.auth.models import AbstractUser

from baserow.core.utils import Progress
from baserow.contrib.database.handler import DatabaseHandler
from baserow.contrib.database.models import Database
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.models import Table
from baserow.core.action.models import Action
from baserow.core.action.registries import ActionType, ActionScopeStr
from baserow.core.action.scopes import ApplicationActionScopeType
from baserow.core.trash.handler import TrashHandler
from baserow.core.utils import ChildProgressBuilder


class CreateTableActionType(ActionType):
    type = "create_table"

    @dataclasses.dataclass
    class Params:
        table_id: int

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        database: Database,
        name: str,
        data: Optional[List[List[Any]]] = None,
        first_row_header: bool = True,
        progress: Optional[Progress] = None,
    ) -> Table:
        """
        Create a table in the specified database.
        Undoing this action trashes the table and redoing restores it.

        :param user: The user on whose behalf the table is created.
        :param database: The database that the table instance belongs to.
        :param name: The name of the table is created.
        :param data: A list containing all the rows that need to be inserted is
            expected. All the values will be inserted in the database.
        :param first_row_header: Indicates if the first row are the fields. The names
            of these rows are going to be used as fields. If `fields` is provided,
            this options is ignored.
        :param progress: An optional progress instance if you want to track the progress
            of the task.
        :return: The created table and the error report.
        """

        table, error_report = TableHandler().create_table(
            user,
            database,
            name,
            data=data,
            first_row_header=first_row_header,
            fill_example=True,
            progress=progress,
        )

        params = cls.Params(table.id)
        cls.register_action(user, params, cls.scope(table.database.id))

        return table, error_report

    @classmethod
    def scope(cls, database_id) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        table = Table.objects.get(id=params.table_id)
        TableHandler().delete_table(user, table)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TrashHandler.restore_item(
            user, "table", params.table_id, parent_trash_item_id=None
        )


class DeleteTableActionType(ActionType):
    type = "delete_table"

    @dataclasses.dataclass
    class Params:
        table_id: int

    @classmethod
    def do(cls, user: AbstractUser, table: Table):
        """
        Deletes a table in the database.
        See baserow.contrib.database.table.handler.TableHandler.delete_table
        for further details.
        Undoing this action restore the original table from trash and redoing trash it.

        :param user: The user on whose behalf the table is deleted.
        :param table: The table instance that needs to be deleted.
        :raises ValueError: When the provided table is not an instance of Table.
        """

        params = cls.Params(table.id)
        database_id = table.database_id

        TableHandler().delete_table(user, table)

        cls.register_action(user, params, cls.scope(database_id))

    @classmethod
    def scope(cls, database_id) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        TrashHandler.restore_item(
            user, "table", params.table_id, parent_trash_item_id=None
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TableHandler().delete_table_by_id(user, params.table_id)


class OrderTableActionType(ActionType):
    type = "order_table"

    @dataclasses.dataclass
    class Params:
        database_id: int
        original_tables_order: List[int]
        new_tables_order: List[int]

    @classmethod
    def do(cls, user: AbstractUser, database: Database, order: List[int]):
        """
        Updates the order of the tables in the given database.
        See baserow.contrib.database.table.handler.TableHandler.order_table
        for further details.
        Undoing this action restore the previous order and redoing set the new order.

        :param user: The user on whose behalf the tables are ordered.
        :param database: The database of which the views must be updated.
        :param order: A list containing the table ids in the desired order.
        :raises TableNotInDatabase: If one of the table ids in the order does not belong
            to the database.
        """

        table_handler = TableHandler()
        original_table_order = table_handler.get_tables_order(database)
        params = cls.Params(database.id, original_table_order, new_tables_order=order)

        table_handler.order_tables(user, database, order=order)

        cls.register_action(user, params, cls.scope(database.id))

    @classmethod
    def scope(cls, database_id) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):

        TableHandler().order_tables(
            user,
            DatabaseHandler().get_database(params.database_id),
            order=params.original_tables_order,
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TableHandler().order_tables(
            user,
            DatabaseHandler().get_database(params.database_id),
            order=params.new_tables_order,
        )


class UpdateTableActionType(ActionType):
    type = "update_table"

    @dataclasses.dataclass
    class Params:
        table_id: int
        original_table_name: str
        new_table_name: str

    @classmethod
    def do(cls, user: AbstractUser, table: Table, name: str) -> Table:
        """
        Updates the table.
        See baserow.contrib.database.table.handler.TableHandler.update_table
        for further details.
        Undoing this action restore the original table name and redoing
        set the new name again.

        :param user: The user on whose behalf the table is updated.
        :param table: The table instance that needs to be updated.
        :param kwargs: The fields that need to be updated.
        :raises ValueError: When the provided table is not an instance of Table.
        :return: The updated table instance.
        """

        original_table_name = table.name

        TableHandler().update_table(user, table, name=name)

        params = cls.Params(
            table.id,
            original_table_name,
            new_table_name=name,
        )

        cls.register_action(user, params, cls.scope(table.database_id))
        return table

    @classmethod
    def scope(cls, database_id) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        TableHandler().update_table_by_id(
            user, params.table_id, name=params.original_table_name
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TableHandler().update_table_by_id(
            user, params.table_id, name=params.new_table_name
        )


class DuplicateTableActionType(ActionType):
    type = "duplicate_table"

    @dataclasses.dataclass
    class Params:
        table_id: int

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        table: Table,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> Table:
        """
        Duplicate the table.
        Undoing this action trashes the duplicated table and redoing restores it.

        :param user: The user on whose behalf the table is created.
        :param table: The name of the table is created.
        :param progress_builder: A progress builder instance that can be used to
            track the progress of the duplication.
        :return: The duplicated table instance.
        """

        new_table_clone = TableHandler().duplicate_table(
            user, table, progress_builder=progress_builder
        )
        cls.register_action(
            user, cls.Params(new_table_clone.id), cls.scope(table.database_id)
        )
        return new_table_clone

    @classmethod
    def scope(cls, database_id) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        table = Table.objects.get(id=params.table_id)
        TableHandler().delete_table(user, table)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TrashHandler.restore_item(
            user, "table", params.table_id, parent_trash_item_id=None
        )
