from typing import cast, Optional

from rest_framework import serializers

from baserow.core.action.registries import ActionScopeType, ActionScopeStr


class RootActionScopeType(ActionScopeType):
    type = "root"

    @classmethod
    def value(cls) -> ActionScopeStr:
        return cast(ActionScopeStr, cls.type)

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.BooleanField(
            allow_null=True,
            required=False,
            help_text="If set to true then actions registered in the root scope "
            "will be included when undoing or redoing.",
        )

    def valid_serializer_value_to_scope_str(self, value) -> Optional[ActionScopeStr]:
        return self.value() if value else None


class GroupActionScopeType(ActionScopeType):
    type = "group"

    @classmethod
    def value(cls, group_id: int) -> ActionScopeStr:
        return cast(ActionScopeStr, cls.type + str(group_id))

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.IntegerField(
            min_value=0,
            allow_null=True,
            required=False,
            help_text="If set to a groups id then any actions directly related to that "
            "group will be be included when undoing or redoing.",
        )

    def valid_serializer_value_to_scope_str(
        self, value: int
    ) -> Optional[ActionScopeStr]:
        return self.value(value)


class ApplicationActionScopeType(ActionScopeType):
    type = "application"

    @classmethod
    def value(cls, application_id: int) -> ActionScopeStr:
        return cast(ActionScopeStr, cls.type + str(application_id))

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.IntegerField(
            min_value=0,
            allow_null=True,
            required=False,
            help_text="If set to an applications id then any actions directly related "
            "to that application will be be included when undoing or redoing.",
        )

    def valid_serializer_value_to_scope_str(
        self, value: int
    ) -> Optional[ActionScopeStr]:
        return self.value(value)


class ViewActionScopeType(ActionScopeType):
    type = "view"

    @classmethod
    def value(cls, view_id: int) -> ActionScopeStr:
        return cast(ActionScopeStr, cls.type + str(view_id))

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.IntegerField(
            min_value=0,
            allow_null=True,
            required=False,
            help_text="If set to an view id then any actions directly related "
            "to that view will be be included when undoing or redoing.",
        )

    def valid_serializer_value_to_scope_str(
        self, value: int
    ) -> Optional[ActionScopeStr]:
        return self.value(value)
