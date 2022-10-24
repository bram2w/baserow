from django.test import override_settings

import pytest
from baserow_enterprise.role.member_data_types import EnterpriseRolesDataType
from baserow_enterprise_tests.role.test_role_permission_manager import (
    _populate_test_data,
)


@pytest.mark.django_db
@override_settings(
    FEATURE_FLAGS=["roles"],
    PERMISSION_MANAGERS=["core", "staff", "member", "basic", "role"],
)
def test_roles_member_data_type(data_fixture, enterprise_data_fixture):
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
        group_1, [{"user_id": u.id} for u in users]
    )
    assert result == [
        {"role_uid": "ADMIN", "user_id": admin.id},
        {"role_uid": "BUILDER", "user_id": builder.id},
        {"role_uid": "EDITOR", "user_id": editor.id},
        {"role_uid": "VIEWER", "user_id": viewer.id},
        {"role_uid": "VIEWER", "user_id": viewer_plus.id},
        {
            "role_uid": "builder",
            "user_id": builder_less.id,
        },
        {"role_uid": None, "user_id": no_role.id},
    ]

    result = EnterpriseRolesDataType().annotate_serialized_data(
        group_2, [{"user_id": u.id} for u in users]
    )
    assert result == [
        {"role_uid": None, "user_id": admin.id},
        {"role_uid": None, "user_id": builder.id},
        {"role_uid": None, "user_id": editor.id},
        {"role_uid": None, "user_id": viewer.id},
        {"role_uid": None, "user_id": viewer_plus.id},
        {
            "role_uid": None,
            "user_id": builder_less.id,
        },
        {"role_uid": None, "user_id": no_role.id},
    ]
