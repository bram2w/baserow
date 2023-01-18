from typing import Optional, cast

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from baserow.core.action.registries import ActionScopeStr, ActionScopeType

DATABASE_ACTION_CONTEXT = _('in database "%(database_name)s" (%(database_id)s).')


TABLE_ACTION_CONTEXT = _(
    'in table "%(table_name)s" (%(table_id)s) '
    'of database "%(database_name)s" (%(database_id)s).'
)


VIEW_ACTION_CONTEXT = _(
    'in view "%(view_name)s" (%(view_id)s) '
    'of table "%(table_name)s" (%(table_id)s) '
    'in database "%(database_name)s" (%(database_id)s).'
)


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
