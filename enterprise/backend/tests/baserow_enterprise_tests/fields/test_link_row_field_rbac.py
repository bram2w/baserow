"""
This file tests the link row field in combination with RBAC enabled
"""
import pytest

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.core.exceptions import PermissionDenied
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role


@pytest.fixture(autouse=True)
def enable_enterprise_and_roles_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.mark.django_db
def test_link_row_field_linked_to_table_with_no_access_created(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table_with_access = data_fixture.create_database_table(user, database=database)
    table_with_no_access = data_fixture.create_database_table(user, database=database)
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    RoleAssignmentHandler().assign_role(
        user, group, role=no_access_role, scope=table_with_no_access
    )

    with pytest.raises(PermissionDenied):
        FieldHandler().create_field(
            user=user,
            table=table_with_access,
            type_name="link_row",
            name="link row",
            link_row_table=table_with_no_access,
        )

    with pytest.raises(PermissionDenied):
        FieldHandler().create_field(
            user=user,
            table=table_with_access,
            type_name="link_row",
            name="link row",
            link_row_table=table_with_no_access,
            has_related_field=False,
        )


@pytest.mark.django_db
def test_link_row_field_linked_to_table_with_no_access_updated(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table_with_access = data_fixture.create_database_table(user, database=database)
    table_with_no_access = data_fixture.create_database_table(user, database=database)
    table_unrelated = data_fixture.create_database_table(user, database=database)
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    RoleAssignmentHandler().assign_role(
        user, group, role=no_access_role, scope=table_with_no_access
    )

    link_row_field = FieldHandler().create_field(
        user=user,
        table=table_with_access,
        type_name="link_row",
        name="link row",
        link_row_table=table_unrelated,
    )

    with pytest.raises(PermissionDenied):
        FieldHandler().update_field(
            user=user,
            field=link_row_field.specific,
            link_row_table=table_with_no_access,
        )


@pytest.mark.django_db
def test_link_row_field_linked_to_table_with_no_access_deleted(data_fixture):
    user = data_fixture.create_user()
    user_with_access = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_with_access])
    database = data_fixture.create_database_application(group=group)
    table_with_access = data_fixture.create_database_table(user, database=database)
    table_with_no_access = data_fixture.create_database_table(user, database=database)
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    RoleAssignmentHandler().assign_role(
        user, group, role=no_access_role, scope=table_with_no_access
    )

    link_row_field = FieldHandler().create_field(
        user=user_with_access,
        table=table_with_access,
        type_name="link_row",
        name="link row",
        link_row_table=table_with_no_access,
    )

    with pytest.raises(PermissionDenied):
        FieldHandler().delete_field(
            user=user,
            field=link_row_field.specific,
        )


@pytest.mark.django_db
def test_link_row_field_linked_to_table_with_no_access_from_inaccessible_to_accessable_table(
    data_fixture,
):
    user = data_fixture.create_user()
    user_with_access = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_with_access])
    database = data_fixture.create_database_application(group=group)
    table_with_access = data_fixture.create_database_table(user, database=database)
    table_with_no_access = data_fixture.create_database_table(user, database=database)
    table_unrelated = data_fixture.create_database_table(user, database=database)
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    RoleAssignmentHandler().assign_role(
        user, group, role=no_access_role, scope=table_with_no_access
    )

    link_row_field = FieldHandler().create_field(
        user=user_with_access,
        table=table_with_access,
        type_name="link_row",
        name="link row",
        link_row_table=table_with_no_access,
    )

    with pytest.raises(PermissionDenied):
        FieldHandler().update_field(
            user=user,
            field=link_row_field.specific,
            link_row_table=table_unrelated,
        )
