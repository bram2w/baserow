from typing import Any, Optional

from baserow.core.models import Application, Group, TrashEntry
from baserow.core.operations import (
    RestoreApplicationOperationType,
    RestoreGroupOperationType,
)
from baserow.core.registries import application_type_registry
from baserow.core.signals import application_created, group_restored
from baserow.core.snapshots.handler import SnapshotHandler
from baserow.core.trash.registries import TrashableItemType, trash_item_type_registry


class ApplicationTrashableItemType(TrashableItemType):

    type = "application"
    model_class = Application

    def get_parent(self, trashed_item: Any, parent_id: int) -> Optional[Any]:
        return trashed_item.group

    def get_name(self, trashed_item: Application) -> str:
        return trashed_item.name

    def restore(self, trashed_item: Application, trash_entry: TrashEntry):
        super().restore(trashed_item, trash_entry)
        application_created.send(
            self,
            application=trashed_item,
            user=None,
        )

    def permanently_delete_item(
        self, trashed_item: Application, trash_item_lookup_cache=None
    ):
        """
        Deletes an application and the related relations in the correct way.
        """

        SnapshotHandler().delete_by_application(trashed_item)

        application = trashed_item.specific
        application_type = application_type_registry.get_by_model(application)
        application_type.pre_delete(application)
        application.delete()
        return application

    def get_restore_operation_type(self) -> str:
        return RestoreApplicationOperationType.type


class GroupTrashableItemType(TrashableItemType):

    type = "group"
    model_class = Group

    def get_parent(self, trashed_item: Any, parent_id: int) -> Optional[Any]:
        return None

    def get_name(self, trashed_item: Group) -> str:
        return trashed_item.name

    def restore(self, trashed_item: Group, trash_entry: TrashEntry):
        """
        Informs any clients that the group exists again.
        """

        super().restore(trashed_item, trash_entry)
        for group_user in trashed_item.groupuser_set.all():
            group_restored.send(self, group_user=group_user, user=None)

    def permanently_delete_item(
        self, trashed_group: Group, trash_item_lookup_cache=None
    ):
        """
        Deletes the provided group and all of its applications permanently.
        """

        # Select all the applications so we can delete them via the handler which is
        # needed in order to call the pre_delete method for each application.
        applications = (
            trashed_group.application_set(manager="objects_and_trash")
            .all()
            .select_related("group")
        )
        application_trashable_type = trash_item_type_registry.get("application")
        for application in applications:
            application_trashable_type.permanently_delete_item(application)

        trashed_group.delete()

    def get_restore_operation_type(self) -> str:
        return RestoreGroupOperationType.type
