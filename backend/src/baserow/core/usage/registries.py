from abc import ABC, abstractmethod

from baserow.core.registry import Registry, Instance

UsageInBytes = int


class GroupStorageUsageItemType(Instance, ABC):
    """
    A GroupStorageUsageItemType defines an item that can calculate
    the usage of a group in a specific part of the application
    """

    @abstractmethod
    def calculate_storage_usage(self, group_id: int) -> UsageInBytes:
        """
        Calculates the storage usage for a group
        in a specific part of the application
        :param group_id: the group that the usage is calculated for
        :return: the total usage
        """

        pass


class GroupStorageUsageItemTypeRegistry(Registry):
    """
    A trash_item_type_registry contains all the different usage calcualtions
    that should be called when the total usage of a group is
    calculated
    """

    name = "usage"


group_storage_usage_item_registry = GroupStorageUsageItemTypeRegistry()
