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
from baserow.core.models import Application
from baserow.core.operations import (
    CreateGroupOperationType,
    DeleteGroupOperationType,
    ListApplicationsGroupOperationType,
    ListGroupsOperationType,
    ReadApplicationOperationType,
    ReadGroupOperationType,
    UpdateApplicationOperationType,
    UpdateGroupOperationType,
    UpdateSettingsOperationType,
)
from baserow.core.registries import operation_type_registry
from baserow_enterprise.role.default_roles import default_roles
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role
from baserow_enterprise.role.permission_manager import RolePermissionManagerType


@pytest.fixture(autouse=True)
def enable_enterprise_and_roles_for_all_tests_here(enable_enterprise, synced_roles):
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
def test_check_permissions(data_fixture, enterprise_data_fixture):

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
                except Exception:
                    print(
                        f"Fails to check permission {permission.type} for user {user} "
                        f"on context {context}"
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
        (ReadApplicationOperationType, group_1, False),
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
        (ReadApplicationOperationType, group_1, True),
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
        (ReadApplicationOperationType, group_2, False),
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
        (ReadApplicationOperationType, group_1, True),
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
        (ReadApplicationOperationType, group_2, True),
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
        (ReadApplicationOperationType, group_1, True),
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
        (ReadApplicationOperationType, group_2, False),
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
        (ReadApplicationOperationType, group_1, True),
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
        (ReadApplicationOperationType, group_2, False),
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
        (ReadApplicationOperationType, group_1, True),
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
        (ReadApplicationOperationType, group_2, False),
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
        (ReadApplicationOperationType, group_1, True),
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
        (ReadApplicationOperationType, group_2, False),
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


def test_check_permissions_with_teams(
    data_fixture, enterprise_data_fixture, synced_roles
):
    enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()

    group_1 = data_fixture.create_group(
        user=user,
    )
    database_1 = data_fixture.create_database_application(group=group_1, order=1)

    table_1_1, _, _ = data_fixture.build_table(
        columns=[("number", "number"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_1,
        order=1,
    )

    table_1_2, _, _ = data_fixture.build_table(
        columns=[("number", "number"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_1,
        order=2,
    )

    team1 = enterprise_data_fixture.create_team(group=group_1, members=[user])

    role_builder = Role.objects.get(uid="BUILDER")
    role_viewer = Role.objects.get(uid="VIEWER")
    role_no_access = Role.objects.get(uid="NO_ACCESS")
    low_priority_role = Role.objects.get(uid="NO_ROLE_LOW_PRIORITY")

    perm_manager = RolePermissionManagerType()

    # The low priority role gives no permissions
    RoleAssignmentHandler().assign_role(user, group_1, role=low_priority_role)

    with pytest.raises(PermissionException):
        perm_manager.check_permissions(
            user,
            ReadApplicationOperationType.type,
            group=group_1,
            context=database_1,
        )

    # The user role should take the precedence
    RoleAssignmentHandler().assign_role(user, group_1, role=role_builder)
    RoleAssignmentHandler().assign_role(team1, group_1, role=role_viewer)

    assert (
        perm_manager.check_permissions(
            user,
            UpdateApplicationOperationType.type,
            group=group_1,
            context=database_1,
        )
        is True
    )

    # Now the user role is low_priority the team role should work
    RoleAssignmentHandler().assign_role(user, group_1, role=low_priority_role)

    assert (
        perm_manager.check_permissions(
            user,
            ReadApplicationOperationType.type,
            group=group_1,
            context=database_1.application_ptr,
        )
        is True
    )

    with pytest.raises(PermissionException):
        perm_manager.check_permissions(
            user,
            UpdateApplicationOperationType.type,
            group=group_1,
            context=database_1.application_ptr,
        )

    # Prevent from accessing the table at team level
    RoleAssignmentHandler().assign_role(
        team1, group_1, role=role_no_access, scope=table_1_1
    )

    with pytest.raises(PermissionException):
        perm_manager.check_permissions(
            user,
            ReadDatabaseTableOperationType.type,
            group=group_1,
            context=table_1_1,
        )

    assert (
        perm_manager.check_permissions(
            user,
            ReadDatabaseTableOperationType.type,
            group=group_1,
            context=table_1_2,
        )
        is True
    )

    # And now user level table role should override the team role
    RoleAssignmentHandler().assign_role(
        user, group_1, role=role_builder, scope=table_1_1
    )

    assert (
        perm_manager.check_permissions(
            user,
            UpdateDatabaseTableOperationType.type,
            group=group_1,
            context=table_1_1,
        )
        is True
    )

    with pytest.raises(PermissionException):
        perm_manager.check_permissions(
            user,
            UpdateDatabaseTableOperationType.type,
            group=group_1,
            context=table_1_2,
        )

    # User is now BUILDER at database level. Team most precise role should be used
    RoleAssignmentHandler().assign_role(user, group_1, role=None, scope=table_1_1)
    RoleAssignmentHandler().assign_role(
        user, group_1, role=role_builder, scope=database_1
    )

    with pytest.raises(PermissionException):
        perm_manager.check_permissions(
            user,
            ReadDatabaseTableOperationType.type,
            group=group_1,
            context=table_1_1,
        )

    assert (
        perm_manager.check_permissions(
            user,
            ReadDatabaseTableOperationType.type,
            group=group_1,
            context=table_1_2,
        )
        is True
    )


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
    assert perms[ReadApplicationOperationType.type]["exceptions"] == [
        database_2.application_ptr_id
    ]

    assert perms[ListApplicationsGroupOperationType.type]["default"] is False
    assert perms[ListApplicationsGroupOperationType.type]["exceptions"] == [group_2.id]

    assert perms[ReadFieldOperationType.type]["default"] is False
    assert sorted(perms[ReadFieldOperationType.type]["exceptions"]) == sorted(
        list(table_2_1.field_set.all().values_list("id", flat=True))
    )

    perms = perm_manager.get_permissions_object(viewer_plus, group=group_1)

    assert perms[UpdateDatabaseRowOperationType.type]["default"] is False
    assert perms[UpdateDatabaseRowOperationType.type]["exceptions"] == [table_1_1.id]

    assert perms[UpdateFieldOperationType.type]["default"] is False
    assert sorted(perms[UpdateFieldOperationType.type]["exceptions"]) == sorted(
        list(table_1_1.field_set.all().values_list("id", flat=True))
    )

    perms = perm_manager.get_permissions_object(builder_less, group=group_1)

    assert perms[UpdateDatabaseRowOperationType.type]["default"] is True
    assert perms[UpdateDatabaseRowOperationType.type]["exceptions"] == [table_1_1.id]


@pytest.mark.django_db(transaction=True)
def test_get_permissions_object_with_teams(
    data_fixture, enterprise_data_fixture, synced_roles
):
    enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()

    group_1 = data_fixture.create_group(
        user=user,
    )
    database_1 = data_fixture.create_database_application(group=group_1, order=1)

    table_1_1, _, _ = data_fixture.build_table(
        columns=[("number", "number"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_1,
        order=1,
    )

    table_1_2, _, _ = data_fixture.build_table(
        columns=[("number", "number"), ("text", "text")],
        rows=[[1, "test"]],
        database=database_1,
        order=2,
    )

    team1 = enterprise_data_fixture.create_team(group=group_1, members=[user])
    team2 = enterprise_data_fixture.create_team(group=group_1, members=[user])

    role_builder = Role.objects.get(uid="BUILDER")
    role_viewer = Role.objects.get(uid="VIEWER")
    role_no_access = Role.objects.get(uid="NO_ACCESS")
    low_priority_role = Role.objects.get(uid="NO_ROLE_LOW_PRIORITY")

    perm_manager = RolePermissionManagerType()

    RoleAssignmentHandler().assign_role(user, group_1, role=low_priority_role)

    perms = perm_manager.get_permissions_object(user, group=group_1)

    assert all([not perm["default"] for perm in perms])
    assert all([not perm["exceptions"] for perm in perms])

    # The user role should take the precedence
    RoleAssignmentHandler().assign_role(user, group_1, role=role_builder)
    RoleAssignmentHandler().assign_role(team1, group_1, role=role_viewer)
    RoleAssignmentHandler().assign_role(team2, group_1, role=role_viewer)
    perms = perm_manager.get_permissions_object(user, group=group_1)

    assert perms[UpdateApplicationOperationType.type]["default"] is True
    assert perms[UpdateApplicationOperationType.type]["exceptions"] == []

    # Now the user role is low_priority the team role should work
    RoleAssignmentHandler().assign_role(user, group_1, role=low_priority_role)
    perms = perm_manager.get_permissions_object(user, group=group_1)

    assert perms[UpdateApplicationOperationType.type]["default"] is False
    assert perms[UpdateApplicationOperationType.type]["exceptions"] == []

    # Prevent from accessing the table at team level
    RoleAssignmentHandler().assign_role(
        team1, group_1, role=role_no_access, scope=table_1_1
    )
    perms = perm_manager.get_permissions_object(user, group=group_1)

    assert perms[ReadDatabaseTableOperationType.type]["default"] is True
    assert perms[ReadDatabaseTableOperationType.type]["exceptions"] == [table_1_1.id]

    # And now user level table role should override the team role
    RoleAssignmentHandler().assign_role(
        user, group_1, role=role_builder, scope=table_1_1
    )
    perms = perm_manager.get_permissions_object(user, group=group_1)

    assert perms[ReadDatabaseTableOperationType.type]["default"] is True
    assert perms[ReadDatabaseTableOperationType.type]["exceptions"] == []

    # User is now BUILDER at database level. Team most precise role should be used
    RoleAssignmentHandler().assign_role(user, group_1, role=None, scope=table_1_1)
    RoleAssignmentHandler().assign_role(
        user, group_1, role=role_builder, scope=database_1.application_ptr
    )
    perms = perm_manager.get_permissions_object(user, group=group_1)

    assert perms[ReadDatabaseTableOperationType.type]["default"] is True
    assert perms[ReadDatabaseTableOperationType.type]["exceptions"] == [table_1_1.id]

    RoleAssignmentHandler().assign_role(
        team2, group_1, role=role_builder, scope=table_1_1
    )
    perms = perm_manager.get_permissions_object(user, group=group_1)

    assert perms[ReadDatabaseTableOperationType.type]["default"] is True
    assert perms[ReadDatabaseTableOperationType.type]["exceptions"] == []


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
    application_2_queryset = Application.objects.filter(group=group_2)

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
    # -> should be able to see application_2 because it's parent of table_2_1
    builder_application_queryset = perm_manager.filter_queryset(
        builder,
        ListApplicationsGroupOperationType.type,
        application_2_queryset,
        group=group_2,
        context=group_2,
    )

    assert list(builder_application_queryset) == [database_2.application_ptr]

    # In this scenario the user is:
    # - Viewer at group_2 level
    # - builder at at table_2_1 level
    # -> should be able to see application_2 and application_3
    RoleAssignmentHandler().assign_role(builder, group_2, role=viewer_role)

    builder_application_queryset = perm_manager.filter_queryset(
        builder,
        ListApplicationsGroupOperationType.type,
        application_2_queryset,
        group=group_2,
        context=group_2,
    )

    assert list(builder_application_queryset) == [
        database_2.application_ptr,
        database_3.application_ptr,
    ]

    # In this scenario the user is:
    # - Viewer at group_2 level
    # - no_access at application_2 level
    # - builder at at table_2_1 level
    # -> should still be able to see application_2 and application_3
    RoleAssignmentHandler().assign_role(
        builder, group_2, role=role_no_access, scope=database_2.application_ptr
    )

    builder_application_queryset = perm_manager.filter_queryset(
        builder,
        ListApplicationsGroupOperationType.type,
        application_2_queryset,
        group=group_2,
        context=group_2,
    )

    assert list(builder_application_queryset) == [
        database_2.application_ptr,
        database_3.application_ptr,
    ]

    # In this scenario the user is:
    # - Viewer at group_2 level
    # - no_access at application_2 level
    # -> should be able to see application_3 only
    RoleAssignmentHandler().assign_role(builder, group_2, scope=table_2_1)

    builder_application_queryset = perm_manager.filter_queryset(
        builder,
        ListApplicationsGroupOperationType.type,
        application_2_queryset,
        group=group_2,
        context=group_2,
    )

    assert list(builder_application_queryset) == [
        database_3.application_ptr,
    ]


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
