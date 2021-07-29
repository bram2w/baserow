from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict

from baserow.core.exceptions import TrashItemDoesNotExist
from baserow.core.registry import (
    ModelRegistryMixin,
    Registry,
    ModelInstanceMixin,
    Instance,
)


class TrashableItemType(ModelInstanceMixin, Instance, ABC):
    """
    A TrashableItemType specifies a baserow model which can be trashed.
    """

    def lookup_trashed_item(
        self, trashed_entry, trash_item_lookup_cache: Dict[str, Any] = None
    ):
        """
        Returns the actual instance of the trashed item. By default simply does a get
        on the model_class's trash manager.

        :param trash_item_lookup_cache: A dictionary which can be used to store
            expensive objects used to lookup this item which could be re-used when
            looking up other items of this type.
        :param trashed_entry: The entry to get the real trashed instance for.
        :return: An instance of the model_class with trashed_item_id
        """

        try:
            return self.model_class.trash.get(id=trashed_entry.trash_item_id)
        except self.model_class.DoesNotExist:
            raise TrashItemDoesNotExist()

    @abstractmethod
    def permanently_delete_item(
        self,
        trashed_item: Any,
        trash_item_lookup_cache: Dict[str, Any] = None,
    ):
        """
        Should be implemented to actually delete the specified trashed item from the
        database and do any other required clean-up.

        :param trashed_item: The item to delete permanently.
        :param trash_item_lookup_cache: If a cache is being used to speed up trash
            item lookups it should be provided here so trash items can invalidate the
            cache if when they are deleted a potentially cache item becomes invalid.
        """

        pass

    @property
    def requires_parent_id(self) -> bool:
        """
        :returns True if this trash type requires a parent id to lookup a specific item,
            false if only the trash_item_id is required to perform a lookup.
        """
        return False

    @abstractmethod
    def get_parent(self, trashed_item: Any, parent_id: int) -> Optional[Any]:
        """
        Returns the parent for this item.

        :param trashed_item: The item to lookup a parent for.
        :returns Either the parent item or None if this item has no parent.
        """
        pass

    @abstractmethod
    def trashed_item_restored(self, trashed_item: Any, trash_entry):
        """
        Called when a trashed item is restored, should perform any extra operations
        such as sending web socket signals which occur when an item is "created" in
        baserow.

        :param trash_entry: The trash entry that was restored from.
        :param trashed_item: The item that has been restored.
        """
        pass

    @abstractmethod
    def get_name(self, trashed_item: Any) -> str:
        """
        Should return the name of this particular trashed item to display in the trash
        modal.

        :param trashed_item: The item to be named.
        :return The name of the trashed_group
        """
        pass

    # noinspection PyMethodMayBeStatic
    def get_items_to_trash(self, trashed_item: Any) -> List[Any]:
        """
        When trashing some items you might also need to mark other related items also
        as trashed. Override this method and return instances of trashable models
        which should also be marked as trashed. Each of these instances will not
        however be given their own unique trash entry, but instead be restored
        all together from a single trash entry made for trashed_item only.

        :return  An iterable of trashable model instances.
        """
        return [trashed_item]

    # noinspection PyMethodMayBeStatic
    def get_extra_description(
        self, trashed_item: Any, parent: Optional[Any]
    ) -> Optional[str]:
        """
        Should return an optional extra description to show along with the trash
        entry for this particular trashed item.

        :return A short string giving extra detail on what has been trashed.
        """
        return None


class TrashableItemTypeRegistry(ModelRegistryMixin, Registry):
    """
    The TrashableItemTypeRegistry contains models which can be "trashed" in baserow.
    When an instance of a trashable model is trashed it is removed from baserow but
    not permanently. Once trashed an item can then be restored to add it back to
    baserow just as it was when it was trashed.
    """

    name = "trashable"


trash_item_type_registry = TrashableItemTypeRegistry()
