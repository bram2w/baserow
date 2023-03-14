from typing import Optional, cast

from rest_framework import serializers

from baserow.core.action.registries import ActionScopeStr, ActionScopeType
from baserow.core.action.scopes import WorkspaceActionScopeType


class TeamsActionScopeType(ActionScopeType):
    type = "teams_in_workspace"

    @classmethod
    def value(cls, workspace_id: int) -> ActionScopeStr:
        return (
            cast(ActionScopeStr, WorkspaceActionScopeType.type + str(workspace_id))
            + cls.type
        )

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.IntegerField(
            min_value=0,
            allow_null=True,
            required=False,
            help_text="If set to a workspace id then any actions directly related to that "
            "workspace will be be included when undoing or redoing.",
        )

    def valid_serializer_value_to_scope_str(
        self, value: int
    ) -> Optional[ActionScopeStr]:
        return self.value(value)
