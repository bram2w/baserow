from django.apps import AppConfig
from django.db.models.signals import post_migrate

from tqdm import tqdm


class BaserowEnterpriseConfig(AppConfig):
    name = "baserow_enterprise"

    def ready(self):
        from baserow.core.jobs.registries import job_type_registry
        from baserow_enterprise.audit_log.job_types import AuditLogExportJobType
        from baserow_enterprise.audit_log.operations import (
            ListWorkspaceAuditLogEntriesOperationType,
        )

        job_type_registry.register(AuditLogExportJobType())

        from baserow.api.user.registries import member_data_registry
        from baserow.core.action.registries import (
            action_scope_registry,
            action_type_registry,
        )
        from baserow.core.registries import (
            object_scope_type_registry,
            operation_type_registry,
            plugin_registry,
        )
        from baserow.core.trash.registries import trash_item_type_registry
        from baserow_enterprise.api.member_data_types import (
            EnterpriseMemberTeamsDataType,
        )
        from baserow_enterprise.role.actions import BatchAssignRoleActionType
        from baserow_enterprise.scopes import TeamsActionScopeType
        from baserow_enterprise.teams.actions import (
            CreateTeamActionType,
            CreateTeamSubjectActionType,
            DeleteTeamActionType,
            DeleteTeamSubjectActionType,
            UpdateTeamActionType,
        )
        from baserow_enterprise.teams.object_scopes import (
            TeamObjectScopeType,
            TeamSubjectObjectScopeType,
        )
        from baserow_enterprise.teams.operations import (
            CreateTeamOperationType,
            CreateTeamSubjectOperationType,
            DeleteTeamOperationType,
            DeleteTeamSubjectOperationType,
            ListTeamsOperationType,
            ListTeamSubjectsOperationType,
            ReadTeamOperationType,
            ReadTeamSubjectOperationType,
            RestoreTeamOperationType,
            UpdateTeamOperationType,
        )
        from baserow_enterprise.trash_types import TeamTrashableItemType

        from .plugins import EnterprisePlugin
        from .role.member_data_types import EnterpriseRolesDataType
        from .role.operations import (
            AssignRoleWorkspaceOperationType,
            ReadRoleApplicationOperationType,
            ReadRoleTableOperationType,
            ReadRoleWorkspaceOperationType,
            UpdateRoleApplicationOperationType,
            UpdateRoleTableOperationType,
        )
        from .teams.subjects import TeamSubjectType

        plugin_registry.register(EnterprisePlugin())

        action_type_registry.register(CreateTeamActionType())
        action_type_registry.register(UpdateTeamActionType())
        action_type_registry.register(DeleteTeamActionType())
        action_type_registry.register(CreateTeamSubjectActionType())
        action_type_registry.register(DeleteTeamSubjectActionType())
        action_type_registry.register(BatchAssignRoleActionType())

        trash_item_type_registry.register(TeamTrashableItemType())

        member_data_registry.register(EnterpriseMemberTeamsDataType())
        member_data_registry.register(EnterpriseRolesDataType())

        object_scope_type_registry.register(TeamObjectScopeType())
        object_scope_type_registry.register(TeamSubjectObjectScopeType())

        action_scope_registry.register(TeamsActionScopeType())

        operation_type_registry.register(CreateTeamOperationType())
        operation_type_registry.register(ReadTeamOperationType())
        operation_type_registry.register(ListTeamsOperationType())
        operation_type_registry.register(UpdateTeamOperationType())
        operation_type_registry.register(DeleteTeamOperationType())
        operation_type_registry.register(CreateTeamSubjectOperationType())
        operation_type_registry.register(ReadTeamSubjectOperationType())
        operation_type_registry.register(ListTeamSubjectsOperationType())
        operation_type_registry.register(DeleteTeamSubjectOperationType())
        operation_type_registry.register(AssignRoleWorkspaceOperationType())
        operation_type_registry.register(ReadRoleWorkspaceOperationType())
        operation_type_registry.register(RestoreTeamOperationType())
        operation_type_registry.register(ReadRoleApplicationOperationType())
        operation_type_registry.register(UpdateRoleApplicationOperationType())
        operation_type_registry.register(ReadRoleTableOperationType())
        operation_type_registry.register(UpdateRoleTableOperationType())
        operation_type_registry.register(ListWorkspaceAuditLogEntriesOperationType())

        from baserow.core.registries import subject_type_registry

        subject_type_registry.register(TeamSubjectType())

        from baserow.core.registries import permission_manager_type_registry

        from .role.permission_manager import RolePermissionManagerType

        permission_manager_type_registry.register(RolePermissionManagerType())

        from baserow_premium.license.registries import license_type_registry

        from baserow_enterprise.license_types import (
            EnterpriseLicenseType,
            EnterpriseWithoutSupportLicenseType,
        )

        license_type_registry.register(EnterpriseWithoutSupportLicenseType())
        license_type_registry.register(EnterpriseLicenseType())

        from baserow.core.registries import auth_provider_type_registry
        from baserow_enterprise.sso.oauth2.auth_provider_types import (
            FacebookAuthProviderType,
            GitHubAuthProviderType,
            GitLabAuthProviderType,
            GoogleAuthProviderType,
            OpenIdConnectAuthProviderType,
        )
        from baserow_enterprise.sso.saml.auth_provider_types import SamlAuthProviderType

        auth_provider_type_registry.register(SamlAuthProviderType())
        auth_provider_type_registry.register(GoogleAuthProviderType())
        auth_provider_type_registry.register(FacebookAuthProviderType())
        auth_provider_type_registry.register(GitHubAuthProviderType())
        auth_provider_type_registry.register(GitLabAuthProviderType())
        auth_provider_type_registry.register(OpenIdConnectAuthProviderType())

        from baserow.core.registries import serialization_processor_registry
        from baserow_enterprise.structure_types import (
            RoleAssignmentSerializationProcessorType,
        )

        serialization_processor_registry.register(
            RoleAssignmentSerializationProcessorType()
        )

        from baserow.core.user_sources.registries import user_source_type_registry
        from baserow_enterprise.integrations.local_baserow.user_source_types import (
            LocalBaserowUserSourceType,
        )

        user_source_type_registry.register(LocalBaserowUserSourceType())

        # Create default roles
        post_migrate.connect(sync_default_roles_after_migrate, sender=self)

        from baserow_enterprise.teams.receivers import (
            connect_to_post_delete_signals_to_cascade_deletion_to_team_subjects,
        )

        connect_to_post_delete_signals_to_cascade_deletion_to_team_subjects()

        from baserow_enterprise.role.receivers import (
            connect_to_post_delete_signals_to_cascade_deletion_to_role_assignments,
        )

        connect_to_post_delete_signals_to_cascade_deletion_to_role_assignments()

        # The signals must always be imported last because they use the registries
        # which need to be filled first.
        import baserow_enterprise.audit_log.signals  # noqa: F
        import baserow_enterprise.ws.signals  # noqa: F


def sync_default_roles_after_migrate(sender, **kwargs):
    from baserow.core.db import LockedAtomicTransaction

    from .role.default_roles import default_roles

    apps = kwargs.get("apps", None)

    if apps is not None:
        try:
            Operation = apps.get_model("core", "Operation")
            Role = apps.get_model("baserow_enterprise", "Role")
        except LookupError:
            print("Skipping role creation as related models does not exist.")
        else:
            # Note: we used to migrate `NO_ROLE` to `NO_ACCESS` here.
            # This was moved to 0010_rename_no_role_to_no_access.
            with LockedAtomicTransaction(Role):
                for role_name, operations in tqdm(
                    default_roles.items(), desc="Syncing default roles"
                ):
                    role, _ = Role.objects.update_or_create(
                        uid=role_name,
                        defaults={"name": f"role.{role_name}", "default": True},
                    )
                    role.operations.clear()

                    to_add = []
                    for operation_type in operations:
                        try:
                            operation, _ = Operation.objects.get_or_create(
                                name=operation_type.type
                            )
                        except Operation.MultipleObjectsReturned:
                            duplicated_operations = Operation.objects.filter(name=operation_type.type)
                            operation = duplicated_operations.first()
                            duplicated_operations.exclude(id=operation.id).delete()
                        to_add.append(operation)

                    role.operations.add(*to_add)
