from typing import List, OrderedDict

from django.conf import settings

from rest_framework import serializers

from baserow.api.user.registries import MemberDataType
from baserow.core.models import Group
from baserow.core.registries import permission_manager_type_registry
from baserow_enterprise.api.role.serializers import RoleField
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role


class EnterpriseRolesDataType(MemberDataType):
    type = "role"

    def get_request_serializer_field(self) -> serializers.Field:
        return RoleField(
            model=Role,
            required=False,
            allow_null=True,
            help_text=(
                "Enterprise only: the uid of the role that is assigned to this group user in this group."
            ),
        )

    def annotate_serialized_data(
        self, group: Group, serialized_data: List[OrderedDict]
    ) -> List[OrderedDict]:
        """
        Responsible for annotating team data on `GroupUser` responses.
        Primarily used to inform API consumers of which teams group members
        belong to.
        """

        if (
            "role" not in settings.PERMISSION_MANAGERS
            or not permission_manager_type_registry.get("role").is_enabled(group)
        ):
            return serialized_data

        for member in serialized_data:
            role = RoleAssignmentHandler().get_role_by_uid(
                role_uid=member["permissions"], use_fallback=True
            )
            member["role_uid"] = role.uid

        return serialized_data
