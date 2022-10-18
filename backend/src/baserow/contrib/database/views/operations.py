from baserow.core.registries import OperationType


class ViewOperationType(OperationType):
    context_scope_name = "view"


class CreateViewSortOperationType(ViewOperationType):
    type = "database.table.view.create_sort"


class ReadViewSortOperationType(ViewOperationType):
    type = "database.table.view.read_sort"


class UpdateViewSortOperationType(ViewOperationType):
    type = "database.table.view.update_sort"


class DeleteViewSortOperationType(ViewOperationType):
    type = "database.table.view.delete_sort"


class UpdateViewSlugOperationType(ViewOperationType):
    type = "database.table.view.update_slug"


class ReadViewsOrderOperationType(ViewOperationType):
    type = "database.table.view.read_order"


class OrderViewsOperationType(ViewOperationType):
    type = "database.table.view.order"


class CreateViewOperationType(ViewOperationType):
    type = "database.table.view.create"


class ListViewsOperationType(ViewOperationType):
    type = "database.table.list_views"
    object_scope_name = "database_views"


class ReadViewOperationType(ViewOperationType):
    type = "database.table.view.read"


class UpdateViewOperationType(ViewOperationType):
    type = "database.table.view.update"


class DeleteViewOperationType(ViewOperationType):
    type = "database.table.view.delete"


class DuplicateViewOperationType(ViewOperationType):
    type = "database.table.view.duplicate"


class CreateViewFilterOperationType(ViewOperationType):
    type = "database.table.view.create_filter"


class ReadViewFilterOperationType(ViewOperationType):
    type = "database.table.view.read_filter"


class UpdateViewFilterOperationType(ViewOperationType):
    type = "database.table.view.update_filter"


class DeleteViewFilterOperationType(ViewOperationType):
    type = "database.table.view.delete_filter"


class DeleteViewDecorationOperationType(ViewOperationType):
    type = "database.table.view.delete_decoration"
