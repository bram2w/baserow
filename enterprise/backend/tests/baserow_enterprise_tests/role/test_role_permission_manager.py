from django.test import override_settings

import pytest

from baserow.contrib.database.fields.operations import (
    ReadFieldOperationType,
    UpdateFieldOperationType,
)
from baserow.contrib.database.models import Database
from baserow.contrib.database.operations import (
    CreateTableDatabaseTableOperationType,
    ListTablesDatabaseTableOperationType,
)
from baserow.contrib.database.rows.operations import (
    DeleteDatabaseRowOperationType,
    ReadDatabaseRowOperationType,
    UpdateDatabaseRowOperationType,
)
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.table.operations import (
    CreateRowDatabaseTableOperationType,
    DeleteDatabaseTableOperationType,
    ListRowsDatabaseTableOperationType,
    ReadDatabaseTableOperationType,
    UpdateDatabaseTableOperationType,
)
from baserow.core.exceptions import PermissionException
from baserow.core.operations import (
    CreateGroupOperationType,
    DeleteGroupOperationType,
    ListApplicationsGroupOperationType,
    ListGroupsOperationType,
    ReadApplicationOperationType,
    ReadGroupOperationType,
    UpdateGroupOperationType,
    UpdateSettingsOperationType,
)
from baserow.core.registries import operation_type_registry
from baserow_enterprise.role.default_roles import default_roles
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role
from baserow_enterprise.role.permission_manager import RolePermissionManagerType


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise, synced_roles):
    pass


def _populate_test_data(data_fixture, enterprise_data_fixture):
    enterprise_data_fixture.enable_enterprise()
    admin = data_fixture.create_user(email="admin@test.net")
    builder = data_fixture.create_user(email="builder@test.net")
    editor = data_fixture.create_user(email="editor@test.net")
    viewer = data_fixture.create_user(email="viewer@test.net")
    viewer_plus = data_fixture.create_user(email="viewer_plus@test.net")
    builder_less = data_fixture.create_user(email="builder_less@test.net")
    no_access = data_fixture.create_user(email="no_access@test.net")
    another_admin = data_fixture.create_user(email="another_admin@test.net")

    group_1 = data_fixture.create_group(
        user=admin,
        members=[builder, viewer, editor, viewer_plus, builder_less, no_access],
    )
    group_2 = data_fixture.create_group(
        user=another_admin,
        custom_permissions=[
            (admin, "NO_ACCESS"),
            (builder, "NO_ACCESS"),
            (viewer, "NO_ACCESS"),
            (editor, "NO_ACCESS"),
            (viewer_plus, "NO_ACCESS"),
            (builder_less, "NO_ACCESS"),
            (no_access, "NO_ACCESS"),
        ],
    )

    database_1 = data_fixture.create_database_application(group=group_1, order=1)
    database_2 = data_fixture.create_database_application(group=group_2, order=2)
    database_3 = data_fixture.create_database_application(group=group_2, order=3)

    table_1_1, _, _ = data_fixture.build_table(
        columns=[("number", "number"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_1,
        order=1,
    )
    table_1_2, _, _ = data_fixture.build_table(
        columns=[("number", "text"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_1,
        order=2,
    )

    table_2_1, _, _ = data_fixture.build_table(
        columns=[("number", "text"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_2,
        order=1,
    )
    table_2_2, _, _ = data_fixture.build_table(
        columns=[("number", "text"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_2,
        order=2,
    )

    role_builder = Role.objects.get(uid="BUILDER")
    role_viewer = Role.objects.get(uid="VIEWER")
    role_editor = Role.objects.get(uid="EDITOR")
    role_no_access = Role.objects.get(uid="NO_ACCESS")

    # Group level assignments
    RoleAssignmentHandler().assign_role(builder, group_1, role=role_builder)
    RoleAssignmentHandler().assign_role(viewer, group_1, role=role_viewer)
    RoleAssignmentHandler().assign_role(editor, group_1, role=role_editor)
    RoleAssignmentHandler().assign_role(viewer_plus, group_1, role=role_viewer)
    RoleAssignmentHandler().assign_role(builder_less, group_1, role=role_builder)
    RoleAssignmentHandler().assign_role(no_access, group_1, role=role_no_access)

    # Table level assignments
    RoleAssignmentHandler().assign_role(
        builder, group_2, role=role_builder, scope=table_2_1
    )
    RoleAssignmentHandler().assign_role(
        viewer_plus, group_1, role=role_builder, scope=table_1_1
    )
    RoleAssignmentHandler().assign_role(
        builder_less, group_1, role=role_viewer, scope=table_1_1
    )

    return (
        admin,
        builder,
        editor,
        viewer,
        viewer_plus,
        builder_less,
        no_access,
        group_1,
        group_2,
        database_1,
        database_2,
        database_3,
        table_1_1,
        table_1_2,
        table_2_1,
        table_2_2,
    )


@pytest.mark.django_db(transaction=True)
@override_settings(
    PERMISSION_MANAGERS=["core", "staff", "member", "role", "basic"],
)
def test_check_permissions(data_fixture, enterprise_data_fixture, synced_roles):

    (
        admin,
        builder,
        editor,
        viewer,
        viewer_plus,
        builder_less,
        no_access,
        group_1,
        group_2,
        database_1,
        database_2,
        database_3,
        table_1_1,
        table_1_2,
        table_2_1,
        table_2_2,
    ) = _populate_test_data(data_fixture, enterprise_data_fixture)

    perm_manager = RolePermissionManagerType()

    def check_perms(user, test_list):
        for (permission, context, result) in test_list:
            if isinstance(context, Table):
                group = context.database.group
            elif isinstance(context, Database):
                group = context.group
            else:
                group = context

            if result:
                try:
                    assert perm_manager.check_permissions(
                        user, permission.type, group=group, context=context
                    ), f"User {user} should have permission {permission.type} on context {context}"
                except PermissionException:
                    print(
                        f"User {user} should have permission {permission.type} on context {context}"
                    )
                    raise
            else:
                with pytest.raises(PermissionException):
                    perm_manager.check_permissions(
                        user, permission.type, group=group, context=context
                    )
                    print(
                        f"User {user} shouldn't have permission {permission.type} on context {context}"
                    )

    no_access_tests = [
        # Group 1
        (ReadGroupOperationType, group_1, False),
        (UpdateGroupOperationType, group_1, False),
        (DeleteGroupOperationType, group_1, False),
        # Group 2
        (ReadGroupOperationType, group_2, False),
        # database1
        (ReadApplicationOperationType, database_1, False),
        (ReadDatabaseTableOperationType, table_1_1, False),
        (UpdateDatabaseTableOperationType, table_1_1, False),
        (DeleteDatabaseTableOperationType, table_1_1, False),
        (ReadDatabaseTableOperationType, table_1_2, False),
        (UpdateDatabaseTableOperationType, table_1_2, False),
        (DeleteDatabaseTableOperationType, table_1_2, False),
        # Table_2_1
        (ListTablesDatabaseTableOperationType, database_2, False),
        (CreateTableDatabaseTableOperationType, database_2, False),
        (ReadDatabaseTableOperationType, table_2_1, False),
        (UpdateDatabaseTableOperationType, table_2_1, False),
        (DeleteDatabaseTableOperationType, table_2_1, False),
        # Table_2_2
        (ReadDatabaseTableOperationType, table_2_2, False),
        (UpdateDatabaseTableOperationType, table_2_2, False),
        (DeleteDatabaseTableOperationType, table_2_2, False),
        # Table_1_1 rows
        (ListRowsDatabaseTableOperationType, table_1_1, False),
        (CreateRowDatabaseTableOperationType, table_1_1, False),
        (ReadDatabaseRowOperationType, table_1_1, False),
        (UpdateDatabaseRowOperationType, table_1_1, False),
        (DeleteDatabaseRowOperationType, table_1_1, False),
    ]

    check_perms(no_access, no_access_tests)

    print("ADMIN")

    admin_tests = [
        # Group 1
        (ReadGroupOperationType, group_1, True),
        (UpdateGroupOperationType, group_1, True),
        (DeleteGroupOperationType, group_1, True),
        # Group 2
        (ReadGroupOperationType, group_2, False),
        (UpdateGroupOperationType, group_2, False),
        (DeleteGroupOperationType, group_2, False),
        # Database_1
        (ReadApplicationOperationType, database_1, True),
        (CreateTableDatabaseTableOperationType, database_1, True),
        (ListTablesDatabaseTableOperationType, database_1, True),
        # Table_1_1
        (ReadDatabaseTableOperationType, table_1_1, True),
        (UpdateDatabaseTableOperationType, table_1_1, True),
        (DeleteDatabaseTableOperationType, table_1_1, True),
        (ListRowsDatabaseTableOperationType, table_1_1, True),
        (CreateRowDatabaseTableOperationType, table_1_1, True),
        # Table_1_2
        (ReadDatabaseTableOperationType, table_1_2, True),
        (UpdateDatabaseTableOperationType, table_1_2, True),
        (DeleteDatabaseTableOperationType, table_1_2, True),
        (ListRowsDatabaseTableOperationType, table_1_2, True),
        (CreateRowDatabaseTableOperationType, table_1_2, True),
        # Database_2
        (ReadApplicationOperationType, database_2, False),
        (CreateTableDatabaseTableOperationType, database_2, False),
        (ListTablesDatabaseTableOperationType, database_2, False),
        # Table_2_1
        (ReadDatabaseTableOperationType, table_2_1, False),
        (UpdateDatabaseTableOperationType, table_2_1, False),
        (DeleteDatabaseTableOperationType, table_2_1, False),
        (ListRowsDatabaseTableOperationType, table_2_1, False),
        (CreateRowDatabaseTableOperationType, table_2_1, False),
        # Table_2_2
        (ReadDatabaseTableOperationType, table_2_2, False),
        (UpdateDatabaseTableOperationType, table_2_2, False),
        (DeleteDatabaseTableOperationType, table_2_2, False),
        (ListRowsDatabaseTableOperationType, table_2_2, False),
        (CreateRowDatabaseTableOperationType, table_2_2, False),
        # Table_1_1 rows
        (ReadDatabaseRowOperationType, table_1_1, True),
        (UpdateDatabaseRowOperationType, table_1_1, True),
        (DeleteDatabaseRowOperationType, table_1_1, True),
        # Table_1_2 rows
        (ReadDatabaseRowOperationType, table_1_2, True),
        (UpdateDatabaseRowOperationType, table_1_2, True),
        (DeleteDatabaseRowOperationType, table_1_2, True),
        # Table_2_1 rows
        (ReadDatabaseRowOperationType, table_2_1, False),
        (UpdateDatabaseRowOperationType, table_2_1, False),
        (DeleteDatabaseRowOperationType, table_2_1, False),
        # Table_2_2 rows
        (ReadDatabaseRowOperationType, table_2_2, False),
        (UpdateDatabaseRowOperationType, table_2_2, False),
        (DeleteDatabaseRowOperationType, table_2_2, False),
    ]

    check_perms(admin, admin_tests)

    print("BUILDER")

    builder_tests = [
        # Group 1
        (ReadGroupOperationType, group_1, True),
        (UpdateGroupOperationType, group_1, False),
        (DeleteGroupOperationType, group_1, False),
        (ListApplicationsGroupOperationType, group_1, True),
        # Group 2
        (ReadGroupOperationType, group_2, True),
        (UpdateGroupOperationType, group_2, False),
        (DeleteGroupOperationType, group_2, False),
        (ListApplicationsGroupOperationType, group_2, True),
        # Database_1
        (ReadApplicationOperationType, database_1, True),
        (CreateTableDatabaseTableOperationType, database_1, True),
        (ListTablesDatabaseTableOperationType, database_1, True),
        # Table_1_1
        (ReadDatabaseTableOperationType, table_1_1, True),
        (UpdateDatabaseTableOperationType, table_1_1, True),
        (DeleteDatabaseTableOperationType, table_1_1, True),
        (ListRowsDatabaseTableOperationType, table_1_1, True),
        (CreateRowDatabaseTableOperationType, table_1_1, True),
        # Table_1_2
        (ReadDatabaseTableOperationType, table_1_2, True),
        (UpdateDatabaseTableOperationType, table_1_2, True),
        (DeleteDatabaseTableOperationType, table_1_2, True),
        (ListRowsDatabaseTableOperationType, table_1_2, True),
        (CreateRowDatabaseTableOperationType, table_1_2, True),
        # Database_2
        (ReadApplicationOperationType, database_2, True),
        (CreateTableDatabaseTableOperationType, database_2, False),
        (ListTablesDatabaseTableOperationType, database_2, True),
        # Table_2_1
        (ReadDatabaseTableOperationType, table_2_1, True),
        (UpdateDatabaseTableOperationType, table_2_1, True),
        (DeleteDatabaseTableOperationType, table_2_1, True),
        (ListRowsDatabaseTableOperationType, table_2_1, True),
        (CreateRowDatabaseTableOperationType, table_2_1, True),
        # Table_2_2
        (ReadDatabaseTableOperationType, table_2_2, False),
        (UpdateDatabaseTableOperationType, table_2_2, False),
        (DeleteDatabaseTableOperationType, table_2_2, False),
        (ListRowsDatabaseTableOperationType, table_2_2, False),
        (CreateRowDatabaseTableOperationType, table_2_2, False),
        # Table_1_1 rows
        (ReadDatabaseRowOperationType, table_1_1, True),
        (UpdateDatabaseRowOperationType, table_1_1, True),
        (DeleteDatabaseRowOperationType, table_1_1, True),
        # Table_1_2 rows
        (ReadDatabaseRowOperationType, table_1_2, True),
        (UpdateDatabaseRowOperationType, table_1_2, True),
        (DeleteDatabaseRowOperationType, table_1_2, True),
        # Table_2_1 rows
        (ReadDatabaseRowOperationType, table_2_1, True),
        (UpdateDatabaseRowOperationType, table_2_1, True),
        (DeleteDatabaseRowOperationType, table_2_1, True),
        # Table_2_2 rows
        (ReadDatabaseRowOperationType, table_2_2, False),
        (UpdateDatabaseRowOperationType, table_2_2, False),
        (DeleteDatabaseRowOperationType, table_2_2, False),
    ]

    check_perms(builder, builder_tests)

    print("EDITOR")

    editor_tests = [
        # Group 1
        (ReadGroupOperationType, group_1, True),
        (UpdateGroupOperationType, group_1, False),
        (DeleteGroupOperationType, group_1, False),
        # Group 2
        (ReadGroupOperationType, group_2, False),
        (UpdateGroupOperationType, group_2, False),
        (DeleteGroupOperationType, group_2, False),
        # Database_1
        (ReadApplicationOperationType, database_1, True),
        (CreateTableDatabaseTableOperationType, database_1, False),
        (ListTablesDatabaseTableOperationType, database_1, True),
        # Table_1_1
        (ReadDatabaseTableOperationType, table_1_1, True),
        (UpdateDatabaseTableOperationType, table_1_1, False),
        (DeleteDatabaseTableOperationType, table_1_1, False),
        (ListRowsDatabaseTableOperationType, table_1_1, True),
        (CreateRowDatabaseTableOperationType, table_1_1, True),
        # Table_1_2
        (ReadDatabaseTableOperationType, table_1_2, True),
        (UpdateDatabaseTableOperationType, table_1_2, False),
        (DeleteDatabaseTableOperationType, table_1_2, False),
        (ListRowsDatabaseTableOperationType, table_1_2, True),
        (CreateRowDatabaseTableOperationType, table_1_2, True),
        # Database_2
        (ReadApplicationOperationType, database_2, False),
        (CreateTableDatabaseTableOperationType, database_2, False),
        (ListTablesDatabaseTableOperationType, database_2, False),
        # Table_2_1
        (ReadDatabaseTableOperationType, table_2_1, False),
        (UpdateDatabaseTableOperationType, table_2_1, False),
        (DeleteDatabaseTableOperationType, table_2_1, False),
        (ListRowsDatabaseTableOperationType, table_2_1, False),
        (CreateRowDatabaseTableOperationType, table_2_1, False),
        # Table_2_2
        (ReadDatabaseTableOperationType, table_2_2, False),
        (UpdateDatabaseTableOperationType, table_2_2, False),
        (DeleteDatabaseTableOperationType, table_2_2, False),
        (ListRowsDatabaseTableOperationType, table_2_2, False),
        (CreateRowDatabaseTableOperationType, table_2_2, False),
        # Table_1_1 rows
        (ReadDatabaseRowOperationType, table_1_1, True),
        (UpdateDatabaseRowOperationType, table_1_1, True),
        (DeleteDatabaseRowOperationType, table_1_1, True),
        # Table_1_2 rows
        (ReadDatabaseRowOperationType, table_1_2, True),
        (UpdateDatabaseRowOperationType, table_1_2, True),
        (DeleteDatabaseRowOperationType, table_1_2, True),
        # Table_2_1 rows
        (ReadDatabaseRowOperationType, table_2_1, False),
        (UpdateDatabaseRowOperationType, table_2_1, False),
        (DeleteDatabaseRowOperationType, table_2_1, False),
        # Table_2_2 rows
        (ReadDatabaseRowOperationType, table_2_2, False),
        (UpdateDatabaseRowOperationType, table_2_2, False),
        (DeleteDatabaseRowOperationType, table_2_2, False),
    ]

    check_perms(editor, editor_tests)

    print("VIEWER")

    viewer_tests = [
        # Group 1
        (ReadGroupOperationType, group_1, True),
        (UpdateGroupOperationType, group_1, False),
        (DeleteGroupOperationType, group_1, False),
        # Group 2
        (ReadGroupOperationType, group_2, False),
        (UpdateGroupOperationType, group_2, False),
        (DeleteGroupOperationType, group_2, False),
        # Database_1
        (ReadApplicationOperationType, database_1, True),
        (CreateTableDatabaseTableOperationType, database_1, False),
        (ListTablesDatabaseTableOperationType, database_1, True),
        # Table_1_1
        (ReadDatabaseTableOperationType, table_1_1, True),
        (UpdateDatabaseTableOperationType, table_1_1, False),
        (DeleteDatabaseTableOperationType, table_1_1, False),
        (ListRowsDatabaseTableOperationType, table_1_1, True),
        (CreateRowDatabaseTableOperationType, table_1_1, False),
        # Table_1_2
        (ReadDatabaseTableOperationType, table_1_2, True),
        (UpdateDatabaseTableOperationType, table_1_2, False),
        (DeleteDatabaseTableOperationType, table_1_2, False),
        (ListRowsDatabaseTableOperationType, table_1_2, True),
        (CreateRowDatabaseTableOperationType, table_1_2, False),
        # Database_2
        (ReadApplicationOperationType, database_2, False),
        (CreateTableDatabaseTableOperationType, database_2, False),
        (ListTablesDatabaseTableOperationType, database_2, False),
        # Table_2_1
        (ReadDatabaseTableOperationType, table_2_1, False),
        (UpdateDatabaseTableOperationType, table_2_1, False),
        (DeleteDatabaseTableOperationType, table_2_1, False),
        (ListRowsDatabaseTableOperationType, table_2_1, False),
        (CreateRowDatabaseTableOperationType, table_2_1, False),
        # Table_2_2
        (ReadDatabaseTableOperationType, table_2_2, False),
        (UpdateDatabaseTableOperationType, table_2_2, False),
        (DeleteDatabaseTableOperationType, table_2_2, False),
        (ListRowsDatabaseTableOperationType, table_2_2, False),
        (CreateRowDatabaseTableOperationType, table_2_2, False),
        # Table_1_1 rows
        (ReadDatabaseRowOperationType, table_1_1, True),
        (UpdateDatabaseRowOperationType, table_1_1, False),
        (DeleteDatabaseRowOperationType, table_1_1, False),
        # Table_1_2 rows
        (ReadDatabaseRowOperationType, table_1_2, True),
        (UpdateDatabaseRowOperationType, table_1_2, False),
        (DeleteDatabaseRowOperationType, table_1_2, False),
        # Table_2_1 rows
        (ReadDatabaseRowOperationType, table_2_1, False),
        (UpdateDatabaseRowOperationType, table_2_1, False),
        (DeleteDatabaseRowOperationType, table_2_1, False),
        # Table_2_2 rows
        (ReadDatabaseRowOperationType, table_2_2, False),
        (UpdateDatabaseRowOperationType, table_2_2, False),
        (DeleteDatabaseRowOperationType, table_2_2, False),
    ]

    check_perms(viewer, viewer_tests)

    print("viewer+")

    viewer_plus_tests = [
        # Group 1
        (ReadGroupOperationType, group_1, True),
        (UpdateGroupOperationType, group_1, False),
        (DeleteGroupOperationType, group_1, False),
        # Group 2
        (ReadGroupOperationType, group_2, False),
        (UpdateGroupOperationType, group_2, False),
        (DeleteGroupOperationType, group_2, False),
        # Database_1
        (ReadApplicationOperationType, database_1, True),
        (CreateTableDatabaseTableOperationType, database_1, False),
        (ListTablesDatabaseTableOperationType, database_1, True),
        # Table_1_1
        (ReadDatabaseTableOperationType, table_1_1, True),
        (UpdateDatabaseTableOperationType, table_1_1, True),
        (DeleteDatabaseTableOperationType, table_1_1, True),
        (ListRowsDatabaseTableOperationType, table_1_1, True),
        (CreateRowDatabaseTableOperationType, table_1_1, True),
        # Table_1_2
        (ReadDatabaseTableOperationType, table_1_2, True),
        (UpdateDatabaseTableOperationType, table_1_2, False),
        (DeleteDatabaseTableOperationType, table_1_2, False),
        (ListRowsDatabaseTableOperationType, table_1_2, True),
        (CreateRowDatabaseTableOperationType, table_1_2, False),
        # Database_2
        (ReadApplicationOperationType, database_2, False),
        (CreateTableDatabaseTableOperationType, database_2, False),
        (ListTablesDatabaseTableOperationType, database_2, False),
        # Table_2_1
        (ReadDatabaseTableOperationType, table_2_1, False),
        (UpdateDatabaseTableOperationType, table_2_1, False),
        (DeleteDatabaseTableOperationType, table_2_1, False),
        (ListRowsDatabaseTableOperationType, table_2_1, False),
        (CreateRowDatabaseTableOperationType, table_2_1, False),
        # Table_2_2
        (ReadDatabaseTableOperationType, table_2_2, False),
        (UpdateDatabaseTableOperationType, table_2_2, False),
        (DeleteDatabaseTableOperationType, table_2_2, False),
        (ListRowsDatabaseTableOperationType, table_2_2, False),
        (CreateRowDatabaseTableOperationType, table_2_2, False),
        # Table_1_1 rows
        (ReadDatabaseRowOperationType, table_1_1, True),
        (UpdateDatabaseRowOperationType, table_1_1, True),
        (DeleteDatabaseRowOperationType, table_1_1, True),
        # Table_1_2 rows
        (ReadDatabaseRowOperationType, table_1_2, True),
        (UpdateDatabaseRowOperationType, table_1_2, False),
        (DeleteDatabaseRowOperationType, table_1_2, False),
        # Table_2_1 rows
        (ReadDatabaseRowOperationType, table_2_1, False),
        (UpdateDatabaseRowOperationType, table_2_1, False),
        (DeleteDatabaseRowOperationType, table_2_1, False),
        # Table_2_2 rows
        (ReadDatabaseRowOperationType, table_2_2, False),
        (UpdateDatabaseRowOperationType, table_2_2, False),
        (DeleteDatabaseRowOperationType, table_2_2, False),
    ]

    check_perms(viewer_plus, viewer_plus_tests)

    print("builder_less")

    builder_less_tests = [
        # Group 1
        (ReadGroupOperationType, group_1, True),
        (UpdateGroupOperationType, group_1, False),
        (DeleteGroupOperationType, group_1, False),
        # Group 2
        (ReadGroupOperationType, group_2, False),
        (UpdateGroupOperationType, group_2, False),
        (DeleteGroupOperationType, group_2, False),
        # Database_1
        (ReadApplicationOperationType, database_1, True),
        (CreateTableDatabaseTableOperationType, database_1, True),
        (ListTablesDatabaseTableOperationType, database_1, True),
        # Table_1_1
        (ReadDatabaseTableOperationType, table_1_1, True),
        (UpdateDatabaseTableOperationType, table_1_1, False),
        (DeleteDatabaseTableOperationType, table_1_1, False),
        (ListRowsDatabaseTableOperationType, table_1_1, True),
        (CreateRowDatabaseTableOperationType, table_1_1, False),
        # Table_1_2
        (ReadDatabaseTableOperationType, table_1_2, True),
        (UpdateDatabaseTableOperationType, table_1_2, True),
        (DeleteDatabaseTableOperationType, table_1_2, True),
        (ListRowsDatabaseTableOperationType, table_1_2, True),
        (CreateRowDatabaseTableOperationType, table_1_2, True),
        # Database_2
        (ReadApplicationOperationType, database_2, False),
        (CreateTableDatabaseTableOperationType, database_2, False),
        (ListTablesDatabaseTableOperationType, database_2, False),
        # Table_2_1
        (ReadDatabaseTableOperationType, table_2_1, False),
        (UpdateDatabaseTableOperationType, table_2_1, False),
        (DeleteDatabaseTableOperationType, table_2_1, False),
        (ListRowsDatabaseTableOperationType, table_2_1, False),
        (CreateRowDatabaseTableOperationType, table_2_1, False),
        # Table_2_2
        (ReadDatabaseTableOperationType, table_2_2, False),
        (UpdateDatabaseTableOperationType, table_2_2, False),
        (DeleteDatabaseTableOperationType, table_2_2, False),
        (ListRowsDatabaseTableOperationType, table_2_2, False),
        (CreateRowDatabaseTableOperationType, table_2_2, False),
        # Table_1_1 rows
        (ReadDatabaseRowOperationType, table_1_1, True),
        (UpdateDatabaseRowOperationType, table_1_1, False),
        (DeleteDatabaseRowOperationType, table_1_1, False),
        # Table_1_2 rows
        (ReadDatabaseRowOperationType, table_1_2, True),
        (UpdateDatabaseRowOperationType, table_1_2, True),
        (DeleteDatabaseRowOperationType, table_1_2, True),
        # Table_2_1 rows
        (ReadDatabaseRowOperationType, table_2_1, False),
        (UpdateDatabaseRowOperationType, table_2_1, False),
        (DeleteDatabaseRowOperationType, table_2_1, False),
        # Table_2_2 rows
        (ReadDatabaseRowOperationType, table_2_2, False),
        (UpdateDatabaseRowOperationType, table_2_2, False),
        (DeleteDatabaseRowOperationType, table_2_2, False),
    ]

    check_perms(builder_less, builder_less_tests)


@pytest.mark.django_db(transaction=True)
@override_settings(
    PERMISSION_MANAGERS=["core", "staff", "member", "role", "basic"],
)
def test_get_permissions_object(data_fixture, enterprise_data_fixture, synced_roles):
    (
        admin,
        builder,
        editor,
        viewer,
        viewer_plus,
        builder_less,
        no_access,
        group_1,
        group_2,
        database_1,
        database_2,
        database_3,
        table_1_1,
        table_1_2,
        table_2_1,
        table_2_2,
    ) = _populate_test_data(data_fixture, enterprise_data_fixture)

    perm_manager = RolePermissionManagerType()

    perms = perm_manager.get_permissions_object(admin, group=group_1)

    assert perms[UpdateGroupOperationType.type]["default"] is True
    assert perms[UpdateGroupOperationType.type]["exceptions"] == []

    perms = perm_manager.get_permissions_object(builder, group=group_1)

    assert perms[UpdateGroupOperationType.type]["default"] is False
    assert perms[UpdateGroupOperationType.type]["exceptions"] == []

    perms = perm_manager.get_permissions_object(builder, group=group_2)

    assert perms[ReadApplicationOperationType.type]["default"] is False
    assert perms[ReadApplicationOperationType.type]["exceptions"] == [database_2.id]

    assert perms[ListApplicationsGroupOperationType.type]["default"] is False
    assert perms[ListApplicationsGroupOperationType.type]["exceptions"] == [group_2.id]

    assert perms[ReadFieldOperationType.type]["default"] is False
    assert perms[ReadFieldOperationType.type]["exceptions"] == list(
        table_2_1.field_set.all().values_list("id", flat=True)
    )

    perms = perm_manager.get_permissions_object(viewer_plus, group=group_1)

    assert perms[UpdateDatabaseRowOperationType.type]["default"] is False
    assert perms[UpdateDatabaseRowOperationType.type]["exceptions"] == [table_1_1.id]

    assert perms[UpdateFieldOperationType.type]["default"] is False
    assert perms[UpdateFieldOperationType.type]["exceptions"] == list(
        table_1_1.field_set.all().values_list("id", flat=True)
    )

    perms = perm_manager.get_permissions_object(builder_less, group=group_1)

    assert perms[UpdateDatabaseRowOperationType.type]["default"] is True
    assert perms[UpdateDatabaseRowOperationType.type]["exceptions"] == [table_1_1.id]

    role_admin = Role.objects.get(uid="ADMIN")

    # Add admin to database 1 for builder_less user
    RoleAssignmentHandler().assign_role(
        builder_less, group_1, role=role_admin, scope=database_1
    )

    perms = perm_manager.get_permissions_object(builder_less, group=group_1)

    assert perms[UpdateDatabaseRowOperationType.type]["default"] is True
    assert perms[UpdateDatabaseRowOperationType.type]["exceptions"] == []


@pytest.mark.django_db(transaction=True)
@override_settings(
    PERMISSION_MANAGERS=["core", "staff", "member", "role", "basic"],
)
def test_filter_queryset(data_fixture, enterprise_data_fixture):
    (
        admin,
        builder,
        editor,
        viewer,
        viewer_plus,
        builder_less,
        no_access,
        group_1,
        group_2,
        database_1,
        database_2,
        database_3,
        table_1_1,
        table_1_2,
        table_2_1,
        table_2_2,
    ) = _populate_test_data(data_fixture, enterprise_data_fixture)

    perm_manager = RolePermissionManagerType()

    table_1_queryset = Table.objects.filter(database__group=group_1)
    table_2_queryset = Table.objects.filter(database__group=group_2)
    database_2_queryset = Database.objects.filter(group=group_2)

    admin_table_queryset = perm_manager.filter_queryset(
        admin,
        ListTablesDatabaseTableOperationType.type,
        table_1_queryset,
        group=group_1,
        context=database_1,
    )

    assert list(admin_table_queryset) == [table_1_1, table_1_2]

    admin_table_queryset_2 = perm_manager.filter_queryset(
        admin,
        ListTablesDatabaseTableOperationType.type,
        table_2_queryset,
        group=group_2,
        context=database_2,
    )

    assert list(admin_table_queryset_2) == []

    no_access_table_queryset = perm_manager.filter_queryset(
        no_access,
        ListTablesDatabaseTableOperationType.type,
        table_1_queryset,
        group=group_1,
        context=database_1,
    )

    assert list(no_access_table_queryset) == []

    builder_table_queryset = perm_manager.filter_queryset(
        builder,
        ListTablesDatabaseTableOperationType.type,
        table_2_queryset,
        group=group_2,
        context=database_2,
    )

    assert list(builder_table_queryset) == [table_2_1]

    viewer_role = Role.objects.get(uid="VIEWER")
    role_no_access = Role.objects.get(uid="NO_ACCESS")

    # In this scenario the user is:
    # - no_access at group_2 level
    # - Builder at table_2_1 level
    # -> should be able to see database_2 because it's parent of table_2_1
    builder_database_queryset = perm_manager.filter_queryset(
        builder,
        ListApplicationsGroupOperationType.type,
        database_2_queryset,
        group=group_2,
        context=group_2,
    )

    assert list(builder_database_queryset) == [database_2]

    # In this scenario the user is:
    # - Viewer at group_2 level
    # - builder at at table_2_1 level
    # -> should be able to see database_2 and database_3
    RoleAssignmentHandler().assign_role(builder, group_2, role=viewer_role)

    builder_database_queryset = perm_manager.filter_queryset(
        builder,
        ListApplicationsGroupOperationType.type,
        database_2_queryset,
        group=group_2,
        context=group_2,
    )

    assert list(builder_database_queryset) == [database_2, database_3]

    # In this scenario the user is:
    # - Viewer at group_2 level
    # - no_access at database_2 level
    # - builder at at table_2_1 level
    # -> should still be able to see database_2 and database_3
    RoleAssignmentHandler().assign_role(
        builder, group_2, role=role_no_access, scope=database_2
    )

    builder_database_queryset = perm_manager.filter_queryset(
        builder,
        ListApplicationsGroupOperationType.type,
        database_2_queryset,
        group=group_2,
        context=group_2,
    )

    assert list(builder_database_queryset) == [database_2, database_3]


@pytest.mark.django_db
def test_all_operations_are_in_at_least_one_default_role(data_fixture):
    exceptions = [
        CreateGroupOperationType.type,
        ListGroupsOperationType.type,
        UpdateSettingsOperationType.type,
    ]

    all_ops_in_roles = set()
    for ops in default_roles.values():
        all_ops_in_roles.update([o.type for o in ops])

    all_ops = set(operation_type_registry.get_all())

    missing_ops = []
    for op in all_ops:
        if op.type not in all_ops_in_roles and op.type not in exceptions:
            missing_ops.append(op)
    assert missing_ops == [], "Non Assigned Ops:\n" + str(
        "\n".join([o.__class__.__name__ + "," for o in missing_ops])
    )
