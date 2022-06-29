import dataclasses

from collections import defaultdict
from copy import deepcopy
from typing import Dict, Any, Optional, List

from baserow.contrib.database.action.scopes import TableActionScopeType
from baserow.contrib.database.fields.handler import FieldHandler

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.handler import FieldOptionsDict, ViewHandler
from baserow.contrib.database.views.models import (
    View,
    ViewFilter,
    ViewSort,
    ViewDecoration,
)
from baserow.contrib.database.views.registries import view_type_registry
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

        original_view_filter_field_id = view_filter.field_id
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
                updated_view_filter.field_id,
                updated_view_filter.type,
                updated_view_filter.value,
            ),
            scope=cls.scope(view_filter.view_id),
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
        view_filter: ViewFilter,
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
        view_id = view_filter.view_id
        field_id = view_filter.field_id
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
        ViewHandler().order_views(user, table, params.original_order)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        table = TableHandler().get_table(params.table_id)
        ViewHandler().order_views(user, table, params.new_order)


class UpdateViewFieldOptionsActionType(ActionType):
    type = "update_view_field_options"

    @dataclasses.dataclass
    class Params:
        view_id: int
        original_field_options: FieldOptionsDict
        new_field_options: FieldOptionsDict

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        view: View,
        field_options: FieldOptionsDict,
    ):
        """
        Updates the field options for the current view.
        See baserow.contrib.database.views.handler.ViewHandler.update_field_options
        for more.
        Undoing this action restores the original field options.
        Redoing this action updates the field options to the new ones.

        :param user: The user creating the filter.
        :param view: The view of the field_optinos to update.
        :param field_options: The field options to set.
        """

        original_field_options = {
            fo["field_id"]: fo
            for fo in view.get_field_options(create_if_missing=True).values()
        }

        ViewHandler().update_field_options(
            user=user, view=view, field_options=field_options
        )

        # save only field_options that have changed from the original value
        new_field_options_to_save = defaultdict(dict)
        original_field_options_to_save = defaultdict(dict)

        for field_id, new_options in field_options.items():
            original_options = original_field_options.get(field_id, {})
            for key, new_value in new_options.items():
                original_value = original_options.get(key, None)
                if new_value != original_value:
                    original_field_options_to_save[field_id][key] = original_value
                    new_field_options_to_save[field_id][key] = new_value

        cls.register_action(
            user=user,
            params=cls.Params(
                view.id,
                dict(original_field_options_to_save),
                dict(new_field_options_to_save),
            ),
            scope=cls.scope(view.id),
        )

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view(params.view_id).specific
        view_handler.update_field_options(
            user=user, view=view, field_options=params.original_field_options
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view(params.view_id).specific
        view_handler.update_field_options(
            user=user, view=view, field_options=params.new_field_options
        )


class RotateViewSlugActionType(ActionType):
    type = "rotate_view_slug"

    @dataclasses.dataclass
    class Params:
        view_id: int
        original_slug: str
        new_slug: str

    @classmethod
    def do(cls, user: AbstractUser, view: View) -> View:
        """
        Change the slug for the current view.
        See baserow.contrib.database.views.handler.ViewHandler.rotate_slug for more.
        Undoing this action restores the original slug.
        Redoing this action updates the slug to the new one.

        :param user: The user creating the filter.
        :param view: The view of the slug to update.
        """

        original_slug = view.slug

        ViewHandler().rotate_view_slug(user, view)

        cls.register_action(
            user=user,
            params=cls.Params(view.id, original_slug, view.slug),
            scope=cls.scope(view.id),
        )
        return view

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view_for_update(params.view_id)
        view_handler.update_view_slug(user, view, params.original_slug)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view_for_update(params.view_id)
        view_handler.update_view_slug(user, view, params.new_slug)


class UpdateViewActionType(ActionType):
    type = "update_view"

    @dataclasses.dataclass
    class Params:
        view_id: int
        original_data: Dict[str, Any]
        new_data: Dict[str, Any]

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        view: View,
        **data,
    ) -> View:
        """
        Updates the current view.
        See baserow.contrib.database.views.handler.ViewHandler.update_view for more.
        Undoing this action restores the original values.
        Redoing this action updates the values to the new ones.

        :param user: The user creating the filter.
        :param view: The view of the slug to update.
        :params data: The data to update.
        """

        def get_prepared_values_for_data(view):
            return {
                key: value
                for key, value in view_type.export_prepared_values(view).items()
                if key in data
            }

        view_type = view_type_registry.get_by_model(view)
        original_data = get_prepared_values_for_data(view)

        view = ViewHandler().update_view(user, view, **data)

        new_data = get_prepared_values_for_data(view)

        cls.register_action(
            user=user,
            params=cls.Params(view.id, original_data, new_data),
            scope=cls.scope(view.id),
        )
        return view

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view_for_update(params.view_id).specific
        view_handler.update_view(user, view, **params.original_data)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view_for_update(params.view_id).specific
        view_handler.update_view(user, view, **params.new_data)


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
        ViewHandler().delete_view_by_id(user, params.view_id)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        TrashHandler.restore_item(user, "view", params.view_id)


class DuplicateViewActionType(ActionType):
    type = "duplicate_view"

    @dataclasses.dataclass
    class Params:
        view_id: int

    @classmethod
    def do(cls, user: AbstractUser, original_view: View) -> View:
        """
        Duplicate an existing view.

        Undoing this action deletes the new view.
        Redoing this action restores the view.

        :param user: The user creating the view.
        :param original_view: The view to duplicate.
        """

        view = ViewHandler().duplicate_view(
            user,
            original_view,
        )

        cls.register_action(
            user=user,
            params=cls.Params(view.id),
            scope=cls.scope(original_view.table.id),
        )

        return view

    @classmethod
    def scope(cls, table_id: int) -> ActionScopeStr:
        return TableActionScopeType.value(table_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        ViewHandler().delete_view_by_id(user, params.view_id)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        TrashHandler.restore_item(user, "view", params.view_id)


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
            scope=cls.scope(view.table_id),
        )

    @classmethod
    def scope(cls, table_id: int) -> ActionScopeStr:
        return TableActionScopeType.value(table_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        TrashHandler.restore_item(user, "view", params.view_id)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        ViewHandler().delete_view_by_id(user, params.view_id)


class CreateDecorationActionType(ActionType):
    type = "create_decoration"

    @dataclasses.dataclass
    class Params:
        view_id: int
        decorator_id: int
        decorator_type_name: str
        value_provider_type_name: str
        value_provider_conf: Dict[str, Any]

    @classmethod
    def do(
        cls,
        view: View,
        decorator_type_name: str,
        value_provider_type_name: str,
        value_provider_conf: Dict[str, Any],
        user: AbstractUser,
    ) -> ViewDecoration:
        """
        Creates a new decoration based on the provided type.
        See baserow.contrib.decorations.handler.DecorationsHandler.create_decoration
        for further details.
        Undoing this action deletes the decoration.

        :param view: The view for which the filter needs to be created.
        :param decorator_type_name: The type of the decorator.
        :param value_provider_type_name: The value provider that provides the value
            to the decorator.
        :param value_provider_conf: The configuration used by the value provider to
            compute the values for the decorator.
        :param user: Optional user who have created the decoration.
        :return: The created view decoration instance.
        """

        decoration = ViewHandler().create_decoration(
            view,
            decorator_type_name,
            value_provider_type_name,
            value_provider_conf,
            user=user,
        )

        cls.register_action(
            user=user,
            params=cls.Params(
                view.id,
                decoration.id,
                decorator_type_name,
                value_provider_type_name,
                value_provider_conf,
            ),
            scope=cls.scope(view.id),
        )

        return decoration

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view_decoration = ViewHandler().get_decoration(params.decorator_id)
        ViewHandler().delete_decoration(view_decoration, user=user)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        view = ViewHandler().get_view(params.view_id)
        ViewHandler().create_decoration(
            view,
            params.decorator_type_name,
            params.value_provider_type_name,
            params.value_provider_conf,
            user=user,
            primary_key=params.decorator_id,
        )


class UpdateDecorationActionType(ActionType):
    type = "update_decoration"

    @dataclasses.dataclass
    class Params:
        decorator_id: int
        original_decoration_type_name: str
        original_value_provider_type_name: str
        original_value_provider_conf: Dict[str, Any]
        original_order: int
        new_decorator_type_name: str
        new_value_provider_type_name: str
        new_value_provider_conf: Dict[str, Any]
        new_order: int

    @classmethod
    def do(
        cls,
        view_decoration: ViewDecoration,
        user: AbstractUser,
        decorator_type_name: str = None,
        value_provider_type_name: str = None,
        value_provider_conf: Dict[str, Any] = None,
        order: int = None,
    ) -> ViewDecoration:
        """
        Updates the values of an existing view decoration.
        See baserow.contrib.decorations.handler.DecorationsHandler.update_decoration
        for further details.
        Undoing this action will revert the changes.
        Redoing this action will apply the changes again.

        :param view_decoration: The view decoration that needs to be updated.
        :param user: Optional user who have created the decoration..
        :param decorator_type_name: The type of the decorator.
        :param value_provider_type_name: The value provider that provides the value
            to the decorator.
        :param value_provider_conf: The configuration used by the value provider to
            compute the values for the decorator.
        :param order: The order of the decoration.
        :param user: Optional user who have updated the decoration.
        :return: The updated view decoration instance.
        """

        original_view_decoration = deepcopy(view_decoration)
        original_decoration_type_name = original_view_decoration.type
        original_value_provider_type_name = original_view_decoration.value_provider_type
        original_value_provider_conf = original_view_decoration.value_provider_conf
        original_order = original_view_decoration.order

        view_decoration_updated = ViewHandler().update_decoration(
            view_decoration,
            user=user,
            decorator_type_name=decorator_type_name,
            value_provider_type_name=value_provider_type_name,
            value_provider_conf=value_provider_conf,
            order=order,
        )

        cls.register_action(
            user=user,
            params=cls.Params(
                view_decoration.id,
                original_decoration_type_name,
                original_value_provider_type_name,
                original_value_provider_conf,
                original_order,
                decorator_type_name,
                value_provider_type_name,
                value_provider_conf,
                order,
            ),
            scope=cls.scope(view_decoration.view_id),
        )

        return view_decoration_updated

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        view_decoration = ViewHandler().get_decoration(params.decorator_id)
        ViewHandler().update_decoration(
            view_decoration,
            user=user,
            decorator_type_name=params.original_decoration_type_name,
            value_provider_type_name=params.original_value_provider_type_name,
            value_provider_conf=params.original_value_provider_conf,
            order=params.original_order,
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        view_decoration = ViewHandler().get_decoration(params.decorator_id)
        ViewHandler().update_decoration(
            view_decoration,
            user=user,
            decorator_type_name=params.new_decorator_type_name,
            value_provider_type_name=params.new_value_provider_type_name,
            value_provider_conf=params.new_value_provider_conf,
            order=params.new_order,
        )


class DeleteDecorationActionType(ActionType):
    type = "delete_decoration"

    @dataclasses.dataclass
    class Params:
        view_id: int
        original_decorator_id: int
        original_decorator_type_name: str
        original_value_provider_type_name: str
        original_value_provider_conf: str
        original_order: int

    @classmethod
    def do(cls, view_decoration: ViewDecoration, user: AbstractUser):
        """
        Deletes an existing view decoration.
        See baserow.contrib.decorations.handler.DecorationsHandler.delete_decoration
        for further details.
        Undoing this action will restore the decoration.
        Redoing this action will delete the decoration again.

        :param view_decoration: The view decoration instance that needs to be deleted.
        :param user: Optional user who have deleted the decoration.
        """

        original_view_decoration = deepcopy(view_decoration)

        ViewHandler().delete_decoration(view_decoration, user=user)

        cls.register_action(
            user=user,
            params=cls.Params(
                original_view_decoration.view_id,
                original_view_decoration.id,
                original_view_decoration.type,
                original_view_decoration.value_provider_type,
                original_view_decoration.value_provider_conf,
                original_view_decoration.order,
            ),
            scope=cls.scope(view_decoration.view_id),
        )

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Any, action_being_undone: Action):
        view = ViewHandler().get_view(params.view_id)
        ViewHandler().create_decoration(
            view=view,
            user=user,
            decorator_type_name=params.original_decorator_type_name,
            value_provider_type_name=params.original_value_provider_type_name,
            value_provider_conf=params.original_value_provider_conf,
            primary_key=params.original_decorator_id,
            order=params.original_order,
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Any, action_being_redone: Action):
        view_decoration = ViewHandler().get_decoration(params.original_decorator_id)
        ViewHandler().delete_decoration(view_decoration, user=user)
