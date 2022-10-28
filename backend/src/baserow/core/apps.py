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


# noinspection PyPep8Naming
def start_sync_templates_task_after_migrate(sender, **kwargs):
    from baserow.core.tasks import sync_templates_task

    if settings.BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION and not settings.TESTS:
        print(
            "Submitting the sync templates task to run asynchronously in "
            "celery after the migration..."
        )
        sync_templates_task.delay()
