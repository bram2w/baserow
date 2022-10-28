from typing import Optional, cast

from rest_framework import serializers

from baserow.core.action.registries import ActionScopeStr, ActionScopeType
from baserow.core.action.scopes import GroupActionScopeType


class TeamsActionScopeType(ActionScopeType):
    type = "teams_in_group"

    @classmethod
    def value(cls, group_id: int) -> ActionScopeStr:
        return (
            cast(ActionScopeStr, GroupActionScopeType.type + str(group_id)) + cls.type
        )

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.IntegerField(
            min_value=0,
            allow_null=True,
            required=False,
            help_text="If set to a group id then any actions directly related to that "
            "group will be be included when undoing or redoing.",
        )

    def valid_serializer_value_to_scope_str(
        self, value: int
    ) -> Optional[ActionScopeStr]:
        return self.value(value)
