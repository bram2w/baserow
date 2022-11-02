from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    name = "baserow.core"

    def ready(self):
        from baserow.core.action.registries import (
            action_scope_registry,
            action_type_registry,
        )
        from baserow.core.trash.registries import trash_item_type_registry
        from baserow.core.trash.trash_types import (
            ApplicationTrashableItemType,
            GroupTrashableItemType,
        )

        trash_item_type_registry.register(GroupTrashableItemType())
        trash_item_type_registry.register(ApplicationTrashableItemType())

        from baserow.core.permission_manager import (
            BasicPermissionManagerType,
            CorePermissionManagerType,
            GroupMemberOnlyPermissionManagerType,
            StaffOnlyPermissionManagerType,
        )
        from baserow.core.registries import (
            object_scope_type_registry,
            operation_type_registry,
            permission_manager_type_registry,
        )

        permission_manager_type_registry.register(CorePermissionManagerType())
        permission_manager_type_registry.register(StaffOnlyPermissionManagerType())
        permission_manager_type_registry.register(BasicPermissionManagerType())
        permission_manager_type_registry.register(
            GroupMemberOnlyPermissionManagerType()
        )

        from .object_scopes import (
            ApplicationObjectScopeType,
            CoreObjectScopeType,
            GroupInvitationObjectScopeType,
            GroupObjectScopeType,
            GroupUserObjectScopeType,
        )
        from .snapshots.object_scopes import SnapshotObjectScopeType

        object_scope_type_registry.register(CoreObjectScopeType())
        object_scope_type_registry.register(ApplicationObjectScopeType())
        object_scope_type_registry.register(GroupObjectScopeType())
        object_scope_type_registry.register(GroupInvitationObjectScopeType())
        object_scope_type_registry.register(SnapshotObjectScopeType())
        object_scope_type_registry.register(GroupUserObjectScopeType())

        from .operations import (
            CreateApplicationsGroupOperationType,
            CreateGroupOperationType,
            CreateInvitationsGroupOperationType,
            DeleteApplicationOperationType,
            DeleteGroupInvitationOperationType,
            DeleteGroupOperationType,
            DeleteGroupUserOperationType,
            DuplicateApplicationOperationType,
            ListApplicationsGroupOperationType,
            ListGroupsOperationType,
            ListGroupUsersGroupOperationType,
            ListInvitationsGroupOperationType,
            OrderApplicationsOperationType,
            ReadApplicationOperationType,
            ReadGroupOperationType,
            ReadInvitationGroupOperationType,
            RestoreApplicationOperationType,
            RestoreGroupOperationType,
            UpdateApplicationOperationType,
            UpdateGroupInvitationType,
            UpdateGroupOperationType,
            UpdateGroupUserOperationType,
            UpdateSettingsOperationType,
        )
        from .snapshots.operations import (
            CreateSnapshotApplicationOperationType,
            DeleteApplicationSnapshotOperationType,
            ListSnapshotsApplicationOperationType,
            RestoreApplicationSnapshotOperationType,
        )
        from .trash.operations import (
            EmptyApplicationTrashOperationType,
            EmptyGroupTrashOperationType,
            ReadApplicationTrashOperationType,
            ReadGroupTrashOperationType,
        )

        operation_type_registry.register(CreateApplicationsGroupOperationType())
        operation_type_registry.register(CreateGroupOperationType())
        operation_type_registry.register(CreateInvitationsGroupOperationType())
        operation_type_registry.register(DeleteGroupInvitationOperationType())
        operation_type_registry.register(DeleteGroupOperationType())
        operation_type_registry.register(ListApplicationsGroupOperationType())
        operation_type_registry.register(ListInvitationsGroupOperationType())
        operation_type_registry.register(ReadInvitationGroupOperationType())
        operation_type_registry.register(ListGroupsOperationType())
        operation_type_registry.register(UpdateGroupInvitationType())
        operation_type_registry.register(ReadGroupOperationType())
        operation_type_registry.register(UpdateGroupOperationType())
        operation_type_registry.register(ListGroupUsersGroupOperationType())
        operation_type_registry.register(OrderApplicationsOperationType())
        operation_type_registry.register(UpdateGroupUserOperationType())
        operation_type_registry.register(DeleteGroupUserOperationType())
        operation_type_registry.register(UpdateApplicationOperationType())
        operation_type_registry.register(DuplicateApplicationOperationType())
        operation_type_registry.register(DeleteApplicationOperationType())
        operation_type_registry.register(UpdateSettingsOperationType())
        operation_type_registry.register(CreateSnapshotApplicationOperationType())
        operation_type_registry.register(DeleteApplicationSnapshotOperationType())
        operation_type_registry.register(ListSnapshotsApplicationOperationType())
        operation_type_registry.register(RestoreApplicationSnapshotOperationType())
        operation_type_registry.register(ReadGroupTrashOperationType())
        operation_type_registry.register(ReadApplicationTrashOperationType())
        operation_type_registry.register(EmptyApplicationTrashOperationType())
        operation_type_registry.register(EmptyGroupTrashOperationType())
        operation_type_registry.register(RestoreApplicationOperationType())
        operation_type_registry.register(RestoreGroupOperationType())
        operation_type_registry.register(ReadApplicationOperationType())

        from baserow.core.actions import (
            CreateApplicationActionType,
            CreateGroupActionType,
            DeleteApplicationActionType,
            DeleteGroupActionType,
            DuplicateApplicationActionType,
            InstallTemplateActionType,
            OrderApplicationsActionType,
            OrderGroupsActionType,
            UpdateApplicationActionType,
            UpdateGroupActionType,
        )

        action_type_registry.register(CreateGroupActionType())
        action_type_registry.register(DeleteGroupActionType())
        action_type_registry.register(UpdateGroupActionType())
        action_type_registry.register(OrderGroupsActionType())
        action_type_registry.register(CreateApplicationActionType())
        action_type_registry.register(UpdateApplicationActionType())
        action_type_registry.register(DeleteApplicationActionType())
        action_type_registry.register(OrderApplicationsActionType())
        action_type_registry.register(DuplicateApplicationActionType())
        action_type_registry.register(InstallTemplateActionType())

        from baserow.core.action.scopes import (
            ApplicationActionScopeType,
            GroupActionScopeType,
            RootActionScopeType,
        )

        action_scope_registry.register(RootActionScopeType())
        action_scope_registry.register(GroupActionScopeType())
        action_scope_registry.register(ApplicationActionScopeType())

        from baserow.core.jobs.registries import job_type_registry

        from .job_types import DuplicateApplicationJobType, InstallTemplateJobType
        from .snapshots.job_type import CreateSnapshotJobType, RestoreSnapshotJobType

        job_type_registry.register(DuplicateApplicationJobType())
        job_type_registry.register(InstallTemplateJobType())
        job_type_registry.register(CreateSnapshotJobType())
        job_type_registry.register(RestoreSnapshotJobType())

        from baserow.core.auth_provider.auth_provider_types import (
            PasswordAuthProviderType,
        )
        from baserow.core.registries import auth_provider_type_registry

        auth_provider_type_registry.register_default(PasswordAuthProviderType())

        # Clear the key after migration so we will trigger a new template sync.
        post_migrate.connect(start_sync_templates_task_after_migrate, sender=self)
        # Create all operations from registry
        post_migrate.connect(sync_operations_after_migrate, sender=self)


# noinspection PyPep8Naming
def start_sync_templates_task_after_migrate(sender, **kwargs):
    from baserow.core.tasks import sync_templates_task

    if settings.BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION and not settings.TESTS:
        print(
            "Submitting the sync templates task to run asynchronously in "
            "celery after the migration..."
        )
        sync_templates_task.delay()


def sync_operations_after_migrate(sender, **kwargs):

    apps = kwargs.get("apps", None)

    if apps is not None:
        try:
            Operation = apps.get_model("core", "Operation")
        except LookupError:
            print("Skipping operation creation as Operation model does not exist.")
        else:
            from baserow.core.registries import operation_type_registry

            print("Creating all operations...")
            all_operation_types = [
                Operation(name=o.type) for o in operation_type_registry.get_all()
            ]
            Operation.objects.bulk_create(all_operation_types, ignore_conflicts=True)
