import abc

from baserow.contrib.database.table.operations import DatabaseTableOperationType
from baserow.contrib.database.views.object_scopes import (
    DatabaseViewDecorationObjectScopeType,
    DatabaseViewFilterObjectScopeType,
    DatabaseViewObjectScopeType,
    DatabaseViewSortObjectScopeType,
)
from baserow.core.registries import OperationType


class ViewOperationType(OperationType, abc.ABC):
    context_scope_name = DatabaseViewObjectScopeType.type


class ViewFilterOperationType(OperationType, abc.ABC):
    context_scope_name = DatabaseViewFilterObjectScopeType.type


class ViewSortOperationType(OperationType, abc.ABC):
    context_scope_name = DatabaseViewSortObjectScopeType.type


class CreateViewSortOperationType(ViewOperationType):
    type = "database.table.view.create_sort"


class ListViewSortOperationType(ViewOperationType):
    type = "database.table.view.list_sort"
    object_scope_name = DatabaseViewSortObjectScopeType.type


class ReadViewSortOperationType(ViewSortOperationType):
    type = "database.table.view.sort.read"


class UpdateViewSortOperationType(ViewSortOperationType):
    type = "database.table.view.sort.update"


class DeleteViewSortOperationType(ViewSortOperationType):
    type = "database.table.view.sort.delete"


class UpdateViewSlugOperationType(ViewOperationType):
    type = "database.table.view.update_slug"


class ReadViewsOrderOperationType(DatabaseTableOperationType):
    type = "database.table.read_view_order"


class OrderViewsOperationType(DatabaseTableOperationType):
    type = "database.table.order_views"
    object_scope_name = DatabaseViewObjectScopeType.type


class CreateViewOperationType(DatabaseTableOperationType):
    type = "database.table.create_view"


class ListViewsOperationType(DatabaseTableOperationType):
    type = "database.table.list_views"
    object_scope_name = DatabaseViewObjectScopeType.type


class ReadViewOperationType(ViewOperationType):
    type = "database.table.view.read"


class ReadViewFieldOptionsOperationType(ViewOperationType):
    type = "database.table.view.read_field_options"


class UpdateViewFieldOptionsOperationType(ViewOperationType):
    type = "database.table.view.update_field_options"


class UpdateViewOperationType(ViewOperationType):
    type = "database.table.view.update"


class DeleteViewOperationType(ViewOperationType):
    type = "database.table.view.delete"


class RestoreViewOperationType(ViewOperationType):
    type = "database.table.view.restore"


class DuplicateViewOperationType(ViewOperationType):
    type = "database.table.view.duplicate"


class CreateViewFilterOperationType(ViewOperationType):
    type = "database.table.view.create_filter"


class ListViewFilterOperationType(ViewOperationType):
    type = "database.table.view.list_filter"
    object_scope_name = DatabaseViewFilterObjectScopeType.type


class ListAggregationsViewOperationType(ViewOperationType):
    type = "database.table.view.list_aggregations"


class ReadAggregationsViewOperationType(ViewOperationType):
    type = "database.table.view.read_aggregation"


class ReadViewFilterOperationType(ViewFilterOperationType):
    type = "database.table.view.filter.read"


class UpdateViewFilterOperationType(ViewFilterOperationType):
    type = "database.table.view.filter.update"


class DeleteViewFilterOperationType(ViewFilterOperationType):
    type = "database.table.view.filter.delete"


class CreateViewDecorationOperationType(ViewOperationType):
    type = "database.table.view.create_decoration"


class ListViewDecorationOperationType(ViewOperationType):
    type = "database.table.view.list_decoration"
    object_scope_name = DatabaseViewDecorationObjectScopeType.type


class ViewDecorationOperationType(ViewOperationType, abc.ABC):
    context_scope_name = DatabaseViewDecorationObjectScopeType.type


class ReadViewDecorationOperationType(ViewDecorationOperationType):
    type = "database.table.view.decoration.read"
    object_scope_name = DatabaseViewDecorationObjectScopeType.type


class UpdateViewDecorationOperationType(ViewDecorationOperationType):
    type = "database.table.view.decoration.update"


class DeleteViewDecorationOperationType(ViewDecorationOperationType):
    type = "database.table.view.decoration.delete"
