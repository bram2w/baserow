from typing import Dict, List, OrderedDict, Union

from django.conf import settings
from django.contrib.auth.models import AbstractUser

from rest_framework import serializers

from baserow.api.user.registries import MemberDataType
from baserow.core.handler import CoreHandler
from baserow.core.models import Group
from baserow.core.operations import ListGroupUsersGroupOperationType
from baserow.core.registries import permission_manager_type_registry
from baserow_enterprise.api.role.serializers import RoleField
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role


class EnterpriseRolesDataType(MemberDataType):
    type = "role"

    def get_request_serializer_field(
        self,
    ) -> Union[serializers.Field, Dict[str, serializers.Field]]:
        return {
            "role_uid": RoleField(
                model=Role,
                required=False,
                allow_null=True,
                help_text=(
                    "Enterprise or advanced only: the uid of the role that is assigned "
                    "to this group user in this group."
                ),
            ),
            "highest_role_uid": RoleField(
                model=Role,
                required=False,
                allow_null=True,
                help_text=(
                    "Enterprise or advanced only: the highest role uid assigned to "
                    "this user in this group on anything, including roles from teams."
                ),
            ),
        }

    def annotate_serialized_data(
        self, group: Group, serialized_data: List[OrderedDict], user: AbstractUser
    ) -> List[OrderedDict]:
        """
        Responsible for annotating team data on `GroupUser` responses.
        Primarily used to inform API consumers of which teams group members
        belong to.
        """

        from baserow_premium.plugins import PremiumPlugin

        from baserow.core.registries import plugin_registry

        if (
            "role" not in settings.PERMISSION_MANAGERS
            or not permission_manager_type_registry.get("role").is_enabled(group)
        ):
            return serialized_data

        if not CoreHandler().check_permissions(
            user,
            ListGroupUsersGroupOperationType.type,
            group=group,
            context=group,
            raise_permission_exceptions=False,
        ):
            return serialized_data

        license_plugin = plugin_registry.get_by_type(PremiumPlugin).get_license_plugin()

        usage = license_plugin.get_seat_usage_for_group(group)
        if usage:
            highest_role_per_user = usage.highest_role_per_user_id
        else:
            highest_role_per_user = None

        for member in serialized_data:
            role = RoleAssignmentHandler().get_role_by_uid(
                role_uid=member["permissions"], use_fallback=True
            )
            member["highest_role_uid"] = highest_role_per_user.get(
                member["user_id"], None
            )
            member["role_uid"] = role.uid

        return serialized_data
