import dataclasses
from typing import Optional, List

from baserow.contrib.database.action.scopes import TableActionScopeType
from baserow.contrib.database.fields.handler import FieldHandler

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View, ViewFilter, ViewSort
from baserow.core.action.models import Action
from baserow.core.action.registries import ActionScopeStr, ActionType
from baserow.core.action.scopes import ViewActionScopeType
from django.contrib.auth.models import AbstractUser

from baserow.core.trash.handler import TrashHandler


class CreateViewFilterActionType(ActionType):
    type = "create_view_filter"

    @dataclasses.dataclass
    class Params:
        view_filter_id: int
        view_id: int
        field_id: int
        filter_type: str
        filter_value: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        view: View,
        field: Field,
        filter_type: str,
        filter_value: str,
    ) -> ViewFilter:
        """
        Creates a new filter for the provided view.
        See baserow.contrib.database.views.handler.ViewHandler.create_field
        for more. When undone the view_filter is fully deleted from the
        database and when redone it is recreated.

        :param user: The user creating the filter.
        :param view: The view to create the filter for.
        :param field: The field to filter by.
        :param filter_type: Indicates how the field's value
        must be compared to the filter's value.
        :param filter_value: The filter value that must be
        compared to the field's value.
        """

        view_filter = ViewHandler().create_filter(
            user, view, field, filter_type, filter_value
        )
        cls.register_action(
            user=user,
            params=cls.Params(
                view_filter.id, view.id, field.id, filter_type, filter_value
            ),
            scope=cls.scope(view.id),
        )
        return view_filter

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view_filter = ViewHandler().get_filter(user, params.view_filter_id)

        ViewHandler().delete_filter(user, view_filter)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view(params.view_id)
        field = FieldHandler().get_field(params.field_id)

        view_handler.create_filter(
            user,
            view,
            field,
            params.filter_type,
            params.filter_value,
            params.view_filter_id,
        )


class UpdateViewFilterActionType(ActionType):
    type = "update_view_filter"

    @dataclasses.dataclass
    class Params:
        view_filter_id: int
        original_field_id: int
        original_filter_type: str
        original_filter_value: str
        new_field_id: int
        new_filter_type: str
        new_filter_value: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        view_filter: ViewFilter,
        field: Optional[Field] = None,
        filter_type: Optional[str] = None,
        filter_value: Optional[str] = None,
    ) -> ViewFilter:
        """
        Updates the values of an existing view filter.
        See baserow.contrib.database.views.handler.ViewHandler.update_filter
        for more. When undone the view_filter is restored to it's original state
        and when redone it is updated to it's new state.

        :param user: The user on whose behalf the view filter is updated.
        :param view_filter: The view filter that needs to be updated.
        :param field: The model of the field to filter by.
        :param filter_type: Indicates how the field's value
        must be compared to the filter's value.
        :param filter_value: The filter value that must be
        compared to the field's value.
        """

        original_view_filter_field_id = view_filter.field.id
        original_view_filter_type = view_filter.type
        original_view_filter_value = view_filter.value

        view_handler = ViewHandler()
        updated_view_filter = view_handler.update_filter(
            user, view_filter, field, filter_type, filter_value
        )
        cls.register_action(
            user=user,
            params=cls.Params(
                view_filter.id,
                original_view_filter_field_id,
                original_view_filter_type,
                original_view_filter_value,
                updated_view_filter.field.id,
                updated_view_filter.type,
                updated_view_filter.value,
            ),
            scope=cls.scope(view_filter.view.id),
        )

        return updated_view_filter

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        field = FieldHandler().get_field(params.original_field_id)

        view_handler = ViewHandler()
        view_filter = view_handler.get_filter(user, params.view_filter_id)

        view_handler.update_filter(
            user,
            view_filter,
            field,
            params.original_filter_type,
            params.original_filter_value,
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        field = FieldHandler().get_field(params.new_field_id)

        view_handler = ViewHandler()
        view_filter = view_handler.get_filter(user, params.view_filter_id)

        view_handler.update_filter(
            user,
            view_filter,
            field,
            params.new_filter_type,
            params.new_filter_value,
        )


class DeleteViewFilterActionType(ActionType):
    type = "delete_view_filter"

    @dataclasses.dataclass
    class Params:
        view_filter_id: int
        view_id: int
        field_id: int
        filter_type: str
        filter_value: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        view_filter: View,
    ):
        """
        Deletes an existing view filter.
        See baserow.contrib.database.views.handler.ViewHandler.delete_filter
        for more. When undone the view_filter is recreated and when redone
        it is deleted.

        :param user: The user on whose behalf the view filter is deleted.
        :param view_filter: The view filter that needs to be deleted.
        """

        view_filter_id = view_filter.id
        view_id = view_filter.view.id
        field_id = view_filter.field.id
        filter_type = view_filter.type
        filter_value = view_filter.value

        ViewHandler().delete_filter(user, view_filter)

        cls.register_action(
            user=user,
            params=cls.Params(
                view_filter_id,
                view_id,
                field_id,
                filter_type,
                filter_value,
            ),
            scope=cls.scope(view_filter.view.id),
        )

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view(params.view_id)
        field = FieldHandler().get_field(params.field_id)

        view_handler.create_filter(
            user,
            view,
            field,
            params.filter_type,
            params.filter_value,
            params.view_filter_id,
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        view_filter = ViewHandler().get_filter(user, params.view_filter_id)

        ViewHandler().delete_filter(user, view_filter)


class CreateViewSortActionType(ActionType):
    type = "create_view_sort"

    @dataclasses.dataclass
    class Params:
        view_sort_id: int
        view_id: int
        field_id: int
        sort_order: str

    @classmethod
    def do(
        cls, user: AbstractUser, view: View, field: Field, sort_order: str
    ) -> ViewSort:
        """
        Creates a new view sort.
        See baserow.contrib.database.views.handler.ViewHandler.create_sort
        for more. When undone the view_sort is fully deleted from the
        database and when redone it is recreated.

        :param user: The user on whose behalf the view sort is created.
        :param view: The view for which the sort needs to be created.
        :param field: The field that needs to be sorted.
        :param sort_order: The desired order, can either be ascending (A to Z) or
            descending (Z to A).
        """

        view_sort = ViewHandler().create_sort(user, view, field, sort_order)

        cls.register_action(
            user=user,
            params=cls.Params(view_sort.id, view.id, field.id, sort_order),
            scope=cls.scope(view.id),
        )
        return view_sort

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view_sort = ViewHandler().get_sort(user, params.view_sort_id)

        ViewHandler().delete_sort(user, view_sort)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        view_handler = ViewHandler()
        field = FieldHandler().get_field(params.field_id)
        view = view_handler.get_view(params.view_id)

        view_handler.create_sort(
            user, view, field, params.sort_order, params.view_sort_id
        )


class UpdateViewSortActionType(ActionType):
    type = "update_view_sort"

    @dataclasses.dataclass
    class Params:
        view_sort_id: int
        original_field_id: int
        original_sort_order: str
        new_field_id: int
        new_sort_order: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        view_sort: ViewSort,
        field: Optional[Field] = None,
        order: Optional[str] = None,
    ) -> ViewSort:
        """
        Updates the values of an existing view sort.
        See baserow.contrib.database.views.handler.ViewHandler.update_sort
        for more. When undone the view_sort is restored to it's original state
        and when redone it is updated to it's new state.

        :param user: The user on whose behalf the view sort is updated.
        :param view_sort: The view sort that needs to be updated.
        :param field: The field that must be sorted on.
        :param order: Indicates the sort order direction.
        """

        original_view_sort_field_id = view_sort.field.id
        original_view_sort_sort_order = view_sort.order

        handler = ViewHandler()
        updated_view_sort = handler.update_sort(user, view_sort, field, order)

        cls.register_action(
            user=user,
            params=cls.Params(
                view_sort.id,
                original_view_sort_field_id,
                original_view_sort_sort_order,
                updated_view_sort.field.id,
                updated_view_sort.order,
            ),
            scope=cls.scope(view_sort.view.id),
        )

        return updated_view_sort

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        field = FieldHandler().get_field(params.original_field_id)

        view_handler = ViewHandler()
        view_sort = view_handler.get_sort(user, params.view_sort_id)

        view_handler.update_sort(user, view_sort, field, params.original_sort_order)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        field = FieldHandler().get_field(params.new_field_id)

        view_handler = ViewHandler()
        view_sort = view_handler.get_sort(user, params.view_sort_id)

        view_handler.update_sort(user, view_sort, field, params.new_sort_order)


class DeleteViewSortActionType(ActionType):
    type = "delete_view_sort"

    @dataclasses.dataclass
    class Params:
        view_sort_id: int
        view_id: int
        field_id: int
        sort_order: str

    @classmethod
    def do(cls, user: AbstractUser, view_sort: ViewSort):
        """
        Deletes an existing view sort.
        See baserow.contrib.database.views.handler.ViewHandler.delete_sort
        for more. When undone the view_sort is recreated and when redone
        it is deleted.

        :param user: The user on whose behalf the view sort is deleted.
        :param view_sort: The view sort instance that needs
        to be deleted.
        """

        view_sort_id = view_sort.id
        view_id = view_sort.view.id
        field_id = view_sort.field.id
        sort_order = view_sort.order

        ViewHandler().delete_sort(user, view_sort)

        cls.register_action(
            user=user,
            params=cls.Params(
                view_sort_id,
                view_id,
                field_id,
                sort_order,
            ),
            scope=cls.scope(view_sort.view.id),
        )

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view(params.view_id)
        field = FieldHandler().get_field(params.field_id)

        view_handler.create_sort(
            user, view, field, params.sort_order, params.view_sort_id
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        view_sort = ViewHandler().get_sort(user, params.view_sort_id)

        ViewHandler().delete_sort(user, view_sort)


class OrderViewsActionType(ActionType):
    type = "order_views"

    @dataclasses.dataclass
    class Params:
        table_id: int
        original_order: List[int]
        new_order: List[int]

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        table: Table,
        order: List[int],
    ):
        """
        Updates the order of the views in the given table.
        See baserow.contrib.views.handler.ViewsHandler.order_views for further details.
        The order of the views that are not in the `order` parameter set set to `0`.
        Undoing this action restores the original order of the views.
        Redoing this action reorders the views to the new order.

        :param user: The user ordering the views.
        :param table: The table to order the views in.
        :param order: The new order of the views.
        """

        original_order = ViewHandler().get_views_order(user, table)

        ViewHandler().order_views(user, table, order)

        params = cls.Params(table.id, original_order, order)
        cls.register_action(user, params, cls.scope(table.id))

    @classmethod
    def scope(cls, table_id: int) -> ActionScopeStr:
        return TableActionScopeType.value(table_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        table = TableHandler().get_table(params.table_id)
        ViewHandler().order_views(
            user,
            table,
            params.original_order,
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        table = TableHandler().get_table(params.table_id)
        ViewHandler().order_views(
            user,
            table,
            params.new_order,
        )


class DeleteViewActionType(ActionType):
    type = "delete_view"

    @dataclasses.dataclass
    class Params:
        view_id: int

    @classmethod
    def do(cls, user: AbstractUser, view: View):
        """
        Trashes an existing view instance.
        See baserow.contrib.views.handler.ViewsHandler.delete_view for further details.
        Undoing this action restores the view.
        Redoing this action deletes the view again.

        :param user: The user deleting the view.
        :param view: The view to delete.
        """

        ViewHandler().delete_view(user, view)

        cls.register_action(
            user=user,
            params=cls.Params(view.id),
            scope=cls.scope(int(view.table_id)),
        )

    @classmethod
    def scope(cls, table_id: int) -> ActionScopeStr:
        return TableActionScopeType.value(table_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        TrashHandler.restore_item(
            user,
            "view",
            params.view_id,
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        view = ViewHandler().get_view(params.view_id)
        ViewHandler().delete_view(user, view)


class CreateViewActionType(ActionType):
    type = "create_view"

    @dataclasses.dataclass
    class Params:
        view_id: int

    @classmethod
    def do(cls, user: AbstractUser, table: Table, type_name: str, **kwargs) -> View:
        """
        Creates a new view based on the provided type.
        See baserow.contrib.views.handler.ViewsHandler.create_view for further details.
        Undoing this action deletes the view.
        Redoing this action restores the view.

        :param user: The user creating the view.
        :param table: The table to create the view in.
        :param type_name: The type of the view.
        :param kwargs: The parameters of the view.
        """

        view = ViewHandler().create_view(
            user,
            table,
            type_name,
            **kwargs,
        )

        cls.register_action(
            user=user,
            params=cls.Params(view.id),
            scope=cls.scope(table.id),
        )

        return view

    @classmethod
    def scope(cls, table_id: int) -> ActionScopeStr:
        return TableActionScopeType.value(table_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view = ViewHandler().get_view(params.view_id)
        ViewHandler().delete_view(user, view)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        TrashHandler.restore_item(
            user,
            "view",
            params.view_id,
        )
