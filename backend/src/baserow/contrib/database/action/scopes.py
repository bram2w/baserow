from typing import cast, Optional

from rest_framework import serializers
from baserow.core.action.registries import ActionScopeStr, ActionScopeType


class TableActionScopeType(ActionScopeType):
    type = "table"

    @classmethod
    def value(cls, table_id: int) -> ActionScopeStr:
        return cast(ActionScopeStr, cls.type + str(table_id))

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.IntegerField(
            min_value=0,
            allow_null=True,
            required=False,
            help_text="If set to a table id then any actions directly related "
            "to that table will be be included when undoing or redoing.",
        )

    def valid_serializer_value_to_scope_str(
        self, value: int
    ) -> Optional[ActionScopeStr]:
        return self.value(value)
