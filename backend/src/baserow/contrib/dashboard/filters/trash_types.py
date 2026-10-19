from baserow.core.trash.registries import TrashableItemType

from .handler import DashboardFilterHandler
from .models import DashboardFilter
from .operations import RestoreDashboardFilterOperationType
from .signals import dashboard_filters_updated


class DashboardFilterTrashableItemType(TrashableItemType):
    type = "dashboard_filter"
    model_class = DashboardFilter

    def get_parent(self, trashed_item):
        return trashed_item.dashboard

    def get_name(self, trashed_item):
        return trashed_item.label

    def restore(self, trashed_item, trash_entry):
        super().restore(trashed_item, trash_entry)
        dashboard_filters_updated.send(self, dashboard=trashed_item.dashboard)

    def get_restore_operation_type(self):
        return RestoreDashboardFilterOperationType.type

    def permanently_delete_item(self, trashed_item, trash_item_lookup_cache=None):
        DashboardFilterHandler().delete_filter(trashed_item)
