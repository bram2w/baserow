from collections import defaultdict
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, F, Q, TextField, Value, When

from baserow_premium.license.registries import SeatUsageSummary

from baserow.contrib.database.models import Database
from baserow.contrib.database.table.models import Table
from baserow.core.models import (
    GROUP_USER_PERMISSION_MEMBER,
    Application,
    Group,
    GroupUser,
)
from baserow_enterprise.role.constants import BUILDER_ROLE_UID, FREE_ROLE_UIDS
from baserow_enterprise.role.default_roles import default_roles
from baserow_enterprise.role.models import RoleAssignment
from baserow_enterprise.teams.models import Team

User = get_user_model()


class RoleBasedSeatUsageSummaryCalculator:
    @classmethod
    def get_seat_usage_for_group(cls, group: Group) -> SeatUsageSummary:
        return cls._get_seat_usage(group)

    @classmethod
    def get_seat_usage_for_entire_instance(cls) -> SeatUsageSummary:
        return cls._get_seat_usage(None)

    @classmethod
    def _get_seat_usage(cls, group: Optional[Group]) -> SeatUsageSummary:
        """
        Checks all the various sources of role information (GroupUser.permissions and
        the RoleAssignments) and calculates how many free/paid/per role seats are in
        use instance wide.

        If a user has a role directly or indirectly from a team which isn't free on
        any scope (group, database, table) then they are counted as needing a paid
        user seat.

        :param group: The summary can be restricted to only looking at roles,
            users and teams in one specific group if provided in this parameter. If
            not provided then the entire instance is checked.
        """

        # The roles are ordered by operations so that we can later use them when
        # generating the `CASE WHEN`.

        user_content_type = ContentType.objects.get_for_model(User)
        team_content_type = ContentType.objects.get_for_model(Team)
        application_content_types = ContentType.objects.get_for_models(
            Database, Application
        ).values()
        table_content_type = ContentType.objects.get_for_model(Table)
        group_content_type = ContentType.objects.get_for_model(Group)

        valid_applications = Application.objects
        valid_tables = Table.objects.filter(database__trashed=False)
        valid_teams = Team.objects.all()
        valid_groups = Group.objects.all()

        activated_user_ids = User.objects.filter(
            profile__to_be_deleted=False, is_active=True
        )

        # This queryset lists all the user ids and permissions set on group level.
        all_group_permission = GroupUser.objects.filter(
            user__profile__to_be_deleted=False, user__is_active=True
        )

        if group:
            all_group_permission = all_group_permission.filter(group=group.id)
            activated_user_ids = activated_user_ids.filter(groupuser__group=group)
            valid_tables = valid_tables.filter(database__group=group)
            valid_applications = valid_applications.filter(group=group)
            valid_teams = valid_teams.filter(group=group)
            valid_groups = valid_groups.filter(id=group.id)

        # These querysets list all the user ids and the related permissions stored in
        # the role assignment table. This works with direct assignments, but also via
        # a team. It also respects the trashed objects and also handles the possibility
        # that a RoleAssignment exists pointing at a scope or subject that no longer
        # exists by excluding said orphans.
        base_role_assignment_permission_queryset = RoleAssignment.objects.filter(
            Q(
                scope_type__in=application_content_types,
                scope_id__in=valid_applications.values_list("id", flat=True),
            )
            | Q(
                scope_id__in=valid_tables.values_list("id", flat=True),
                scope_type=table_content_type,
            )
            | Q(
                scope_id__in=valid_groups.values_list("id", flat=True),
                scope_type=group_content_type,
            ),
            group__trashed=False,
        )
        if group:
            base_role_assignment_permission_queryset = (
                base_role_assignment_permission_queryset.filter(group=group)
            )

        all_group_permission = all_group_permission.annotate(
            role_uid=Case(
                When(
                    permissions=GROUP_USER_PERMISSION_MEMBER,
                    then=Value(BUILDER_ROLE_UID),
                ),
                output_field=TextField(),
                default=F("permissions"),
            ),
        ).values("user_id", "role_uid")

        all_role_assignment_permission = (
            base_role_assignment_permission_queryset.filter(
                subject_id__in=activated_user_ids.values_list("id", flat=True),
                subject_type=user_content_type,
            )
            .annotate(user_id=F("subject_id"), role_uid=F("role__uid"))
            .values("user_id", "role_uid")
        )
        all_team_assignment_role_uid = (
            base_role_assignment_permission_queryset.filter(
                subject_id__in=valid_teams.values_list("id", flat=True),
                subject_type=team_content_type,
                team__subjects__subject_id__in=activated_user_ids,
                team__subjects__subject_type=user_content_type,
            )
            .annotate(user_id=F("team__subjects__subject_id"), role_uid=F("role__uid"))
            .values("user_id", "role_uid")
        )

        user_roles = all_group_permission.union(
            all_role_assignment_permission, all=True
        ).union(all_team_assignment_role_uid, all=True)

        # Always treat custom roles as the highest priority ones to show.
        role_to_priority = defaultdict(lambda: -1)
        num_users_with_highest_role = {}
        for idx, uid in enumerate(default_roles.keys()):
            role_to_priority[uid] = idx
            num_users_with_highest_role[uid] = 0

        # First calculate the highest role every user has globally where the role
        # ordering is defined by the number of operations they grant.
        highest_role_per_user_id = {}
        for user_role in user_roles:
            user_id = user_role["user_id"]
            role_uid = user_role["role_uid"]

            existing_highest_role = highest_role_per_user_id.get(user_id, None)
            if (
                existing_highest_role is None
                or role_to_priority[role_uid] < role_to_priority[existing_highest_role]
            ):
                highest_role_per_user_id[user_id] = role_uid

        # Now count the number of users per highest role and also how many paid
        # users there are.

        num_paid_users = 0
        num_free_users = 0
        for user_id, highest_role_a_user_has in highest_role_per_user_id.items():
            num_users_with_highest_role.setdefault(highest_role_a_user_has, 0)
            num_users_with_highest_role[highest_role_a_user_has] += 1
            if highest_role_a_user_has not in FREE_ROLE_UIDS:
                num_paid_users += 1
            else:
                num_free_users += 1

        return SeatUsageSummary(
            seats_taken=num_paid_users,
            free_users_count=num_free_users,
            num_users_with_highest_role=num_users_with_highest_role,
            highest_role_per_user_id=highest_role_per_user_id,
        )
