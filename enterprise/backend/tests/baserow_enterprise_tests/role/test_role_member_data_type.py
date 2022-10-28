from django.test import override_settings

import pytest
from baserow_enterprise_tests.role.test_role_permission_manager import (
    _populate_test_data,
)

from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.member_data_types import EnterpriseRolesDataType


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise):
    pass


@pytest.mark.django_db
@override_settings(
    PERMISSION_MANAGERS=["core", "staff", "member", "basic", "role"],
)
def test_roles_member_data_type(data_fixture, enterprise_data_fixture, synced_roles):
    (
        admin,
        builder,
        editor,
        viewer,
        viewer_plus,
        builder_less,
        no_role,
        group_1,
        group_2,
        database_1,
        database_2,
        table_1_1,
        table_1_2,
        table_2_1,
        table_2_2,
    ) = _populate_test_data(data_fixture, enterprise_data_fixture)

    users = [admin, builder, editor, viewer, viewer_plus, builder_less, no_role]

    result = EnterpriseRolesDataType().annotate_serialized_data(
        group_1,
        [
            {
                "user_id": u.id,
                "permissions": RoleAssignmentHandler()
                .get_current_role_assignment(u, group_1)
                .role.uid,
            }
            for u in users
        ],
    )
    assert result == [
        {"permissions": "ADMIN", "role_uid": "ADMIN", "user_id": admin.id},
        {"permissions": "BUILDER", "role_uid": "BUILDER", "user_id": builder.id},
        {"permissions": "EDITOR", "role_uid": "EDITOR", "user_id": editor.id},
        {"permissions": "VIEWER", "role_uid": "VIEWER", "user_id": viewer.id},
        {"permissions": "VIEWER", "role_uid": "VIEWER", "user_id": viewer_plus.id},
        {"permissions": "BUILDER", "role_uid": "BUILDER", "user_id": builder_less.id},
        {"permissions": "NO_ROLE", "role_uid": "NO_ROLE", "user_id": no_role.id},
    ]

    result = EnterpriseRolesDataType().annotate_serialized_data(
        group_2,
        [
            {
                "user_id": u.id,
                "permissions": RoleAssignmentHandler()
                .get_current_role_assignment(u, group_2)
                .role.uid,
            }
            for u in users
        ],
    )
    assert result == [
        {"permissions": "NO_ROLE", "role_uid": "NO_ROLE", "user_id": admin.id},
        {"permissions": "NO_ROLE", "role_uid": "NO_ROLE", "user_id": builder.id},
        {"permissions": "NO_ROLE", "role_uid": "NO_ROLE", "user_id": editor.id},
        {"permissions": "NO_ROLE", "role_uid": "NO_ROLE", "user_id": viewer.id},
        {"permissions": "NO_ROLE", "role_uid": "NO_ROLE", "user_id": viewer_plus.id},
        {"permissions": "NO_ROLE", "role_uid": "NO_ROLE", "user_id": builder_less.id},
        {"permissions": "NO_ROLE", "role_uid": "NO_ROLE", "user_id": no_role.id},
    ]
