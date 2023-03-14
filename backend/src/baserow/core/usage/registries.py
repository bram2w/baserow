from abc import ABC, abstractmethod

from baserow.core.registry import Instance, Registry

UsageInBytes = int


class WorkspaceStorageUsageItemType(Instance, ABC):
    """
    A GroupStorageUsageItemType defines an item that can calculate
    the usage of a group in a specific part of the application
    """

    @abstractmethod
    def calculate_storage_usage(self, workspace_id: int) -> UsageInBytes:
        """
        Calculates the storage usage for a group
        in a specific part of the application
        :param workspace_id: the group that the usage is calculated for
        :return: the total usage
        """

        pass


class WorkspaceStorageUsageItemTypeRegistry(Registry):
    """
    A trash_item_type_registry contains all the different usage calculations
    that should be called when the total usage of a group is
    calculated
    """

    name = "usage"


workspace_storage_usage_item_registry = WorkspaceStorageUsageItemTypeRegistry()
