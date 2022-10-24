import pytest

from baserow.core.handler import CoreHandler
from baserow_enterprise.role.handler import RoleAssignmentHandler
from django.test.utils import override_settings


@pytest.mark.django_db
@override_settings(
    FEATURE_FLAGS=["roles"],
    PERMISSION_MANAGERS=["core", "staff", "member", "role", "basic"],
)
def test_group_user_added_signal_overlapping_roles(data_fixture):
    # TODO once we properly implemented RolePermissionManagerType.is_enabled we will
    # have to make sure that the group in his test is changed to meet the conditions
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group()
    group_user_1 = data_fixture.create_user_group(user=user_1, group=group)
    group_invitation = data_fixture.create_group_invitation(
        email=user_2.email, permissions="ADMIN", group=group
    )

    group_user_2 = CoreHandler().accept_group_invitation(user_2, group_invitation)

    role_assignment = RoleAssignmentHandler().get_current_role_assignment(user_2, group)

    assert role_assignment is not None
    assert group_user_2.permissions == "ADMIN"
    assert role_assignment.role.uid == "ADMIN"


@pytest.mark.django_db
@override_settings(
    FEATURE_FLAGS=["roles"],
    PERMISSION_MANAGERS=["core", "staff", "member", "role", "basic"],
)
def test_group_user_added_signal_not_overlapping_roles(data_fixture):
    # TODO once we properly implemented RolePermissionManagerType.is_enabled we will
    # have to make sure that the group in his test is changed to meet the conditions
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group()
    group_user_1 = data_fixture.create_user_group(user=user_1, group=group)
    group_invitation = data_fixture.create_group_invitation(
        email=user_2.email, permissions="VIEWER", group=group
    )

    group_user_2 = CoreHandler().accept_group_invitation(user_2, group_invitation)

    role_assignment = RoleAssignmentHandler().get_current_role_assignment(user_2, group)

    assert role_assignment is not None
    assert group_user_2.permissions == "MEMBER"
    assert role_assignment.role.uid == "VIEWER"


@pytest.mark.django_db
def test_group_user_added_signal_roles_disabled(data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group()
    group_user_1 = data_fixture.create_user_group(user=user_1, group=group)
    group_invitation = data_fixture.create_group_invitation(
        email=user_2.email, permissions="VIEWER", group=group
    )

    group_user_2 = CoreHandler().accept_group_invitation(user_2, group_invitation)

    role_assignment = RoleAssignmentHandler().get_current_role_assignment(user_2, group)

    assert role_assignment is None
    assert group_user_2.permissions == "MEMBER"
