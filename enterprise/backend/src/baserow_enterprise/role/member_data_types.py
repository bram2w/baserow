from collections import defaultdict
from typing import List, OrderedDict

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from baserow_enterprise.role.models import RoleAssignment

from baserow.api.user.registries import MemberDataType
from baserow.core.models import Group
from baserow.core.registries import permission_manager_type_registry


class EnterpriseRolesDataType(MemberDataType):
    type = "role"

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

        subject_role_data = defaultdict(dict)
        group_ct = ContentType.objects.get_for_model(Group)
        user_ct = ContentType.objects.get_for_model(User)

        subject_ids = [member["user_id"] for member in serialized_data]
        all_role_data = RoleAssignment.objects.filter(
            subject_id__in=subject_ids,
            subject_type=user_ct,
            scope_type=group_ct,
            scope_id=group.id,
        ).values("subject_id", "role__uid")

        for role_data in all_role_data:
            subject_role_data[role_data["subject_id"]] = role_data["role__uid"]

        for member in serialized_data:
            member["role_uid"] = subject_role_data.get(member["user_id"], None)

        return serialized_data
