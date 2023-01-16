import dataclasses

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.core.action.registries import (
    ActionScopeStr,
    ActionType,
    ActionTypeDescription,
)
from baserow.core.action.scopes import GroupActionScopeType
from baserow.core.models import Snapshot
from baserow.core.snapshots.exceptions import SnapshotDoesNotExist
from baserow.core.snapshots.handler import SnapshotHandler
from baserow.core.utils import Progress


class CreateSnapshotActionType(ActionType):
    type = "create_snapshot"
    description = ActionTypeDescription(
        _("Create Snapshot"),
        _(
            'Snapshot "%(snapshot_name)s" (%(snapshot_id)s) created for '
            'application "%(application_name)s" (%(application_id)s).'
        ),
    )

    @dataclasses.dataclass
    class Params:
        application_id: int
        application_name: str
        snapshot_id: int
        snapshot_name: str

    @classmethod
    def do(cls, user: AbstractUser, snapshot: Snapshot, progress: Progress):
        """
        Creates a snapshot for the given application.

        :param application_id: The id of the application for which a snapshot will be
            created.
        :param user: The user performing the delete.
        :param name: The name that will be given to the snapshot.
        """

        snapshot_created = SnapshotHandler().perform_create(snapshot, progress)
        application = snapshot.snapshot_from_application
        group = application.group

        cls.register_action(
            user=user,
            params=cls.Params(
                application.id, application.name, snapshot.id, snapshot.name
            ),
            scope=cls.scope(group.id),
            group=group,
        )
        return snapshot_created

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)


class RestoreSnapshotActionType(ActionType):
    type = "restore_snapshot"
    description = ActionTypeDescription(
        _("Restore Snapshot"),
        _(
            'Snapshot "%(snapshot_name)s" (%(snapshot_id)s) restored from application '
            '"%(original_application_name)s" (%(original_application_id)s) '
            'to application "%(application_name)s" (%(application_id)s).'
        ),
    )

    @dataclasses.dataclass
    class Params:
        application_id: int
        application_name: str
        snapshot_id: int
        snapshot_name: str
        original_application_id: int
        original_application_name: str

    @classmethod
    def do(cls, user: AbstractUser, snapshot: Snapshot, progress: Progress):
        """
        Creates a snapshot for the given application.

        :param snapshot_id: The id of the snapshot that will be restored.
        :param user: The user performing the delete.

        :raises SnapshotDoesNotExist: When the snapshot with the provided id
            does not exist.
        """

        original_application = snapshot.snapshot_from_application
        application = SnapshotHandler().perform_restore(snapshot, progress)

        group = application.group
        cls.register_action(
            user=user,
            params=cls.Params(
                application.id,
                application.name,
                snapshot.id,
                snapshot.name,
                original_application.id,
                original_application.name,
            ),
            scope=cls.scope(group.id),
            group=group,
        )
        return application

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)


class DeleteSnapshotActionType(ActionType):
    type = "delete_snapshot"
    description = ActionTypeDescription(
        _("Delete Snapshot"),
        _(
            'Snapshot "%(snapshot_name)s" (%(snapshot_id)s) deleted for '
            'application "%(application_name)s" (%(application_id)s).'
        ),
    )

    @dataclasses.dataclass
    class Params:
        application_id: int
        application_name: str
        snapshot_id: int
        snapshot_name: str

    @classmethod
    def do(cls, user: AbstractUser, snapshot_id: int):
        """
        Creates a snapshot for the given application.

        :param user: The user performing the delete.
        :param snapshot_id: The id of the snapshot that will be deleted.
        :raises SnapshotDoesNotExist: When the snapshot with the provided id
            does not exist.
        """

        try:
            snapshot = (
                Snapshot.objects.filter(id=snapshot_id)
                .select_for_update(of=("self",))
                .select_related("snapshot_from_application__group")
                .get()
            )
        except Snapshot.DoesNotExist:
            raise SnapshotDoesNotExist()

        application = snapshot.snapshot_from_application
        group = application.group
        snapshot_name = snapshot.name

        SnapshotHandler().delete(snapshot.id, performed_by=user)

        cls.register_action(
            user=user,
            params=cls.Params(
                application.id, application.name, snapshot_id, snapshot_name
            ),
            scope=cls.scope(group.id),
            group=group,
        )

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)
