import dataclasses
from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List, Optional

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.contrib.database.action.scopes import (
    TABLE_ACTION_CONTEXT,
    VIEW_ACTION_CONTEXT,
    TableActionScopeType,
    ViewActionScopeType,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.exceptions import ViewDoesNotExist, ViewNotInTable
from baserow.contrib.database.views.handler import FieldOptionsDict, ViewHandler
from baserow.contrib.database.views.models import (
    View,
    ViewDecoration,
    ViewFilter,
    ViewSort,
)
from baserow.contrib.database.views.registries import view_type_registry
from baserow.core.action.models import Action
from baserow.core.action.registries import (
    ActionScopeStr,
    ActionTypeDescription,
    UndoableActionType,
)
from baserow.core.trash.handler import TrashHandler


class CreateViewFilterActionType(UndoableActionType):
    type = "create_view_filter"
    description = ActionTypeDescription(
        _("Create a view filter"),
        _('View filter created on field "%(field_name)s" (%(field_id)s)'),
        VIEW_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        view_id: int
        view_name: str
        field_id: int
        field_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        view_filter_id: int
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

        group = view.table.database.group
        params = cls.Params(
            view.id,
            view.name,
            field.id,
            field.name,
            view.table.id,
            view.table.name,
            view.table.database.id,
            view.table.database.name,
            view_filter.id,
            filter_type,
            filter_value,
        )
        cls.register_action(user, params, cls.scope(view.id), group)
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


# TODO: What to do here with fast UI updates?
class UpdateViewFilterActionType(UndoableActionType):
    type = "update_view_filter"
    description = ActionTypeDescription(
        _("Update a view filter"),
        _('View filter updated on field "%(field_name)s" (%(field_id)s)'),
        VIEW_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        field_id: int
        field_name: str
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        view_filter_id: int
        filter_type: str
        filter_value: str
        original_field_id: int
        original_field_name: str
        original_filter_type: str
        original_filter_value: str

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
        original_view_filter_field_name = view_filter.field.name
        original_view_filter_type = view_filter.type
        original_view_filter_value = view_filter.value

        view_handler = ViewHandler()
        updated_view_filter = view_handler.update_filter(
            user, view_filter, field, filter_type, filter_value
        )
        view = view_filter.view
        params = cls.Params(
            updated_view_filter.field.id,
            updated_view_filter.field.name,
            view.id,
            view.name,
            view.table.id,
            view.table.name,
            view.table.database.id,
            view.table.database.name,
            view_filter.id,
            updated_view_filter.type,
            updated_view_filter.value,
            original_view_filter_field_id,
            original_view_filter_field_name,
            original_view_filter_type,
            original_view_filter_value,
        )
        group = updated_view_filter.field.table.database.group
        cls.register_action(
            user,
            params,
            cls.scope(view_filter.view_id),
            group,
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
        field = FieldHandler().get_field(params.field_id)

        view_handler = ViewHandler()
        view_filter = view_handler.get_filter(user, params.view_filter_id)

        view_handler.update_filter(
            user,
            view_filter,
            field,
            params.filter_type,
            params.filter_value,
        )


class DeleteViewFilterActionType(UndoableActionType):
    type = "delete_view_filter"
    description = ActionTypeDescription(
        _("Delete a view filter"),
        _('View filter deleted from field "%(field_name)s" (%(field_id)s)'),
        VIEW_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        field_id: int
        field_name: str
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        view_filter_id: int
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
        view_name = view_filter.view.name
        field_id = view_filter.field_id
        field_name = view_filter.field.name
        view_filter_type = view_filter.type
        view_filter_value = view_filter.value

        ViewHandler().delete_filter(user, view_filter)

        params = cls.Params(
            field_id,
            field_name,
            view_id,
            view_name,
            view_filter.view.table.id,
            view_filter.view.table.name,
            view_filter.view.table.database.id,
            view_filter.view.table.database.name,
            view_filter_id,
            view_filter_type,
            view_filter_value,
        )
        group = view_filter.view.table.database.group
        cls.register_action(
            user,
            params,
            cls.scope(
                view_filter.view_id,
            ),
            group,
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


class CreateViewSortActionType(UndoableActionType):
    type = "create_view_sort"
    description = ActionTypeDescription(
        _("Create a view sort"),
        _('View sorted on field "%(field_name)s" (%(field_id)s)'),
        VIEW_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        field_id: int
        field_name: str
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        view_sort_id: int
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

        params = cls.Params(
            field.id,
            field.name,
            view.id,
            view.name,
            view.table.id,
            view.table.name,
            view.table.database.id,
            view.table.database.name,
            view_sort.id,
            sort_order,
        )
        group = view.table.database.group
        cls.register_action(user, params, cls.scope(view.id), group)
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


class UpdateViewSortActionType(UndoableActionType):
    type = "update_view_sort"
    description = ActionTypeDescription(
        _("Update a view sort"),
        _('View sort updated on field "%(field_name)s" (%(field_id)s)'),
        VIEW_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        field_id: int
        field_name: str
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        view_sort_id: int
        sort_order: str
        original_field_id: int
        original_field_name: str
        original_sort_order: str

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

        original_field_id = view_sort.field.id
        original_field_name = view_sort.field.name
        view_id = view_sort.view.id
        view_name = view_sort.view.name
        original_sort_order = view_sort.order

        handler = ViewHandler()
        updated_view_sort = handler.update_sort(user, view_sort, field, order)

        cls.register_action(
            user=user,
            params=cls.Params(
                updated_view_sort.field.id,
                updated_view_sort.field.name,
                view_id,
                view_name,
                updated_view_sort.view.table.id,
                updated_view_sort.view.table.name,
                updated_view_sort.view.table.database.id,
                updated_view_sort.view.table.database.name,
                updated_view_sort.id,
                updated_view_sort.order,
                original_field_id,
                original_field_name,
                original_sort_order,
            ),
            scope=cls.scope(view_sort.view.id),
            group=view_sort.view.table.database.group,
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
        field = FieldHandler().get_field(params.field_id)

        view_handler = ViewHandler()
        view_sort = view_handler.get_sort(user, params.view_sort_id)

        view_handler.update_sort(user, view_sort, field, params.sort_order)


class DeleteViewSortActionType(UndoableActionType):
    type = "delete_view_sort"
    description = ActionTypeDescription(
        _("Delete a view sort"),
        _('View sort deleted from field "%(field_name)s" (%(field_id)s)'),
        VIEW_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        field_id: int
        field_name: str
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        view_sort_id: int
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
        view_name = view_sort.view.name
        field_id = view_sort.field.id
        field_name = view_sort.field.name
        sort_order = view_sort.order

        ViewHandler().delete_sort(user, view_sort)

        params = cls.Params(
            field_id,
            field_name,
            view_id,
            view_name,
            view_sort.view.table.id,
            view_sort.view.table.name,
            view_sort.view.table.database.id,
            view_sort.view.table.database.name,
            view_sort_id,
            sort_order,
        )
        group = view_sort.view.table.database.group
        cls.register_action(user, params, cls.scope(view_sort.view.id), group)

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


class OrderViewsActionType(UndoableActionType):
    type = "order_views"
    description = ActionTypeDescription(
        _("Order views"), _("Views order changed"), TABLE_ACTION_CONTEXT
    )

    @dataclasses.dataclass
    class Params:
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        order: List[int]
        original_order: List[int]

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
        The order of the views that are not in the `order` parameter set to `0`.
        Undoing this action restores the original order of the views.
        Redoing this action reorders the views to the new order.

        :param user: The user ordering the views.
        :param table: The table to order the views in.
        :param order: The new order of the views.
        """

        try:
            view = ViewHandler().get_view(order[0])
        except ViewDoesNotExist:
            raise ViewNotInTable
        original_order = ViewHandler().get_views_order(user, table, view.ownership_type)

        ViewHandler().order_views(user, table, order)

        params = cls.Params(
            table.id,
            table.name,
            table.database.id,
            table.database.name,
            order,
            original_order,
        )
        cls.register_action(user, params, cls.scope(table.id), table.database.group)

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
        ViewHandler().order_views(user, table, params.order)


class UpdateViewFieldOptionsActionType(UndoableActionType):
    type = "update_view_field_options"
    description = ActionTypeDescription(
        _("Update view field options"),
        _("ViewFieldOptions updated"),
        VIEW_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        field_options: FieldOptionsDict
        original_field_options: FieldOptionsDict

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
                view.name,
                view.table.id,
                view.table.name,
                view.table.database.id,
                view.table.database.name,
                dict(new_field_options_to_save),
                dict(original_field_options_to_save),
            ),
            scope=cls.scope(view.id),
            group=view.table.database.group,
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
            user=user, view=view, field_options=params.field_options
        )


class RotateViewSlugActionType(UndoableActionType):
    type = "rotate_view_slug"
    description = ActionTypeDescription(
        _("View slug URL updated"),
        _("View changed public slug URL"),
        VIEW_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        slug: str
        original_slug: str

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
            params=cls.Params(
                view.id,
                view.name,
                view.table.id,
                view.table.name,
                view.table.database.id,
                view.table.database.name,
                view.slug,
                original_slug,
            ),
            scope=cls.scope(view.id),
            group=view.table.database.group,
        )
        return view

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view_for_update(user, params.view_id)
        view_handler.update_view_slug(user, view, params.original_slug)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view_for_update(user, params.view_id)
        view_handler.update_view_slug(user, view, params.slug)


class UpdateViewActionType(UndoableActionType):
    type = "update_view"
    description = ActionTypeDescription(
        _("Update view"),
        _('View "%(view_name)s" (%(view_id)s) updated'),
        TABLE_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        data: Dict[str, Any]
        original_data: Dict[str, Any]

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
            params=cls.Params(
                view.id,
                view.name,
                view.table.id,
                view.table.name,
                view.table.database.id,
                view.table.database.name,
                new_data,
                original_data,
            ),
            scope=cls.scope(view.id),
            group=view.table.database.group,
        )
        return view

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view_for_update(user, params.view_id).specific
        view_handler.update_view(user, view, **params.original_data)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_to_redo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view_for_update(user, params.view_id).specific
        view_handler.update_view(user, view, **params.data)


class CreateViewActionType(UndoableActionType):
    type = "create_view"
    description = ActionTypeDescription(
        _("Create view"),
        _('View "%(view_name)s" (%(view_id)s) created'),
        TABLE_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        view_id: int
        view_name: str
        view_type: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str

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
            params=cls.Params(
                view.id,
                view.name,
                type_name,
                table.id,
                table.name,
                table.database.id,
                table.database.name,
            ),
            scope=cls.scope(table.id),
            group=table.database.group,
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


class DuplicateViewActionType(UndoableActionType):
    type = "duplicate_view"
    description = ActionTypeDescription(
        _("Duplicate view"),
        _(
            'View "%(view_name)s" (%(view_id)s) duplicated from '
            'view "%(original_view_name)s" (%(original_view_id)s)'
        ),
        TABLE_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        original_view_id: int
        original_view_name: str

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
            params=cls.Params(
                view.id,
                view.name,
                original_view.table.id,
                original_view.table.name,
                original_view.table.database.id,
                original_view.table.database.name,
                original_view.id,
                original_view.name,
            ),
            scope=cls.scope(original_view.table.id),
            group=original_view.table.database.group,
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


class DeleteViewActionType(UndoableActionType):
    type = "delete_view"
    description = ActionTypeDescription(
        _("Delete view"),
        _('View "%(view_name)s" (%(view_id)s) deleted'),
        TABLE_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str

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
            params=cls.Params(
                view.id,
                view.name,
                view.table.id,
                view.table.name,
                view.table.database.id,
                view.table.database.name,
            ),
            scope=cls.scope(view.table_id),
            group=view.table.database.group,
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


class CreateDecorationActionType(UndoableActionType):
    type = "create_decoration"
    description = ActionTypeDescription(
        _("Create decoration"),
        _("View decoration %(decorator_id)s created"),
        VIEW_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
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
                view.name,
                view.table.id,
                view.table.name,
                view.table.database.id,
                view.table.database.name,
                decoration.id,
                decorator_type_name,
                value_provider_type_name,
                value_provider_conf,
            ),
            scope=cls.scope(view.id),
            group=view.table.database.group,
        )

        return decoration

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_to_undo: Action):
        view_decoration = ViewHandler().get_decoration(user, params.decorator_id)
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


class UpdateDecorationActionType(UndoableActionType):
    type = "update_decoration"
    description = ActionTypeDescription(
        _("Update decoration"),
        _("View decoration %(decorator_id)s updated"),
        VIEW_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
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
        view = view_decoration.view

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
                view.id,
                view.name,
                view.table.id,
                view.table.name,
                view.table.database.id,
                view.table.database.name,
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
            group=view.table.database.group,
        )

        return view_decoration_updated

    @classmethod
    def scope(cls, view_id: int) -> ActionScopeStr:
        return ViewActionScopeType.value(view_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        view_decoration = ViewHandler().get_decoration(user, params.decorator_id)
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
        view_decoration = ViewHandler().get_decoration(user, params.decorator_id)
        ViewHandler().update_decoration(
            view_decoration,
            user=user,
            decorator_type_name=params.new_decorator_type_name,
            value_provider_type_name=params.new_value_provider_type_name,
            value_provider_conf=params.new_value_provider_conf,
            order=params.new_order,
        )


class DeleteDecorationActionType(UndoableActionType):
    type = "delete_decoration"
    description = ActionTypeDescription(
        _("Delete decoration"),
        _("View decoration %(decorator_id)s deleted"),
        VIEW_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        view_id: int
        view_name: str
        table_id: int
        table_name: str
        database_id: int
        database_name: str
        decorator_id: int
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

        view = view_decoration.view
        cls.register_action(
            user=user,
            params=cls.Params(
                view.id,
                view.name,
                view.table.id,
                view.table.name,
                view.table.database.id,
                view.table.database.name,
                view_decoration.id,
                original_view_decoration.id,
                original_view_decoration.type,
                original_view_decoration.value_provider_type,
                original_view_decoration.value_provider_conf,
                original_view_decoration.order,
            ),
            scope=cls.scope(view_decoration.view_id),
            group=view.table.database.group,
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
        view_decoration = ViewHandler().get_decoration(
            user, params.original_decorator_id
        )
        ViewHandler().delete_decoration(view_decoration, user=user)
