from django.apps import AppConfig


class BaserowEnterpriseConfig(AppConfig):
    name = "baserow_enterprise"

    def ready(self):
        from baserow_enterprise.api.member_data_types import (
            EnterpriseMemberTeamsDataType,
        )
        from baserow_enterprise.teams.actions import (
            CreateTeamActionType,
            CreateTeamSubjectActionType,
            DeleteTeamActionType,
            DeleteTeamSubjectActionType,
            UpdateTeamActionType,
        )
        from baserow_enterprise.trash_types import TeamTrashableItemType

        from baserow.api.user.registries import member_data_registry
        from baserow.core.action.registries import action_type_registry
        from baserow.core.registries import plugin_registry
        from baserow.core.trash.registries import trash_item_type_registry

        from .plugins import EnterprisePlugin

        plugin_registry.register(EnterprisePlugin())
        action_type_registry.register(CreateTeamActionType())
        action_type_registry.register(UpdateTeamActionType())
        action_type_registry.register(DeleteTeamActionType())
        action_type_registry.register(CreateTeamSubjectActionType())
        action_type_registry.register(DeleteTeamSubjectActionType())
        trash_item_type_registry.register(TeamTrashableItemType())

        member_data_registry.register(EnterpriseMemberTeamsDataType())
