from django.contrib.contenttypes.models import ContentType

import pytest

from baserow.contrib.database.table.handler import TableHandler
from baserow.core.registries import ImportExportConfig
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role
from baserow_enterprise.structure_types import RoleAssignmentSerializationProcessorType


@pytest.fixture(autouse=True)
def enable_roles_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.mark.django_db(transaction=True)
def test_export_serialized_structure_on_database(enterprise_data_fixture):
    enterprise_structure = RoleAssignmentSerializationProcessorType()
    user = enterprise_data_fixture.create_user()
    workspace = enterprise_data_fixture.create_workspace(user=user)
    database = enterprise_data_fixture.create_database_application(workspace=workspace)
    application = database.application_ptr

    config = ImportExportConfig(include_permission_data=True)

    role = Role.objects.get(uid="ADMIN")
    RoleAssignmentHandler().assign_role(user, workspace, role, application)
    serialized_structure = enterprise_structure.export_serialized(
        workspace, application, config
    )

    content_types = ContentType.objects.get_for_models(user, application)
    assert serialized_structure == {
        "role_assignments": [
            {
                "subject_id": user.id,
                "subject_type_id": content_types[user].id,
                "role_id": role.id,
            }
        ]
    }


@pytest.mark.django_db(transaction=True)
def test_import_serialized_structure_on_database(enterprise_data_fixture):
    enterprise_structure = RoleAssignmentSerializationProcessorType()
    user = enterprise_data_fixture.create_user()
    workspace = enterprise_data_fixture.create_workspace(user=user)
    database = enterprise_data_fixture.create_database_application(workspace=workspace)
    application = database.application_ptr

    role = Role.objects.get(uid="ADMIN")
    RoleAssignmentHandler().assign_role(user, workspace, role, application)
    config = ImportExportConfig(include_permission_data=True)
    serialized_structure = enterprise_structure.export_serialized(
        workspace, application, config
    )

    new_database = enterprise_data_fixture.create_database_application(
        workspace=workspace
    )
    new_application = new_database.application_ptr

    enterprise_structure.import_serialized(
        workspace, new_application, serialized_structure, config
    )

    role_assignments = RoleAssignmentHandler().get_role_assignments(
        workspace, new_application
    )

    role_assignment = role_assignments[0]
    serialized_role_assignment = serialized_structure["role_assignments"][0]
    assert role_assignment.role_id == serialized_role_assignment["role_id"]
    assert role_assignment.subject_id == serialized_role_assignment["subject_id"]
    assert (
        role_assignment.subject_type.id == serialized_role_assignment["subject_type_id"]
    )


@pytest.mark.django_db(transaction=True)
def test_export_serialized_structure_on_table(enterprise_data_fixture):
    enterprise_structure = RoleAssignmentSerializationProcessorType()
    user = enterprise_data_fixture.create_user()
    workspace = enterprise_data_fixture.create_workspace(user=user)
    database = enterprise_data_fixture.create_database_application(workspace=workspace)

    config = ImportExportConfig(include_permission_data=True)

    role = Role.objects.get(uid="ADMIN")
    table, _ = TableHandler().create_table(user, database, name="Table")
    RoleAssignmentHandler().assign_role(user, workspace, role, table)

    serialized_structure = enterprise_structure.export_serialized(
        workspace, table, config
    )

    content_types = ContentType.objects.get_for_models(user, table)
    assert serialized_structure == {
        "role_assignments": [
            {
                "subject_id": user.id,
                "subject_type_id": content_types[user].id,
                "role_id": role.id,
            }
        ]
    }


@pytest.mark.django_db(transaction=True)
def test_import_serialized_structure_on_table(enterprise_data_fixture):
    enterprise_structure = RoleAssignmentSerializationProcessorType()
    user = enterprise_data_fixture.create_user()
    workspace = enterprise_data_fixture.create_workspace(user=user)
    database = enterprise_data_fixture.create_database_application(workspace=workspace)

    config = ImportExportConfig(include_permission_data=True)

    role = Role.objects.get(uid="ADMIN")
    table, _ = TableHandler().create_table(user, database, name="Table")
    RoleAssignmentHandler().assign_role(user, workspace, role, table)
    serialized_structure = enterprise_structure.export_serialized(
        workspace, table, config
    )

    new_table, _ = TableHandler().create_table(user, database, name="New table")
    enterprise_structure.import_serialized(
        workspace, new_table, serialized_structure, config
    )

    role_assignments = RoleAssignmentHandler().get_role_assignments(
        workspace, new_table
    )

    role_assignment = role_assignments[0]
    serialized_role_assignment = serialized_structure["role_assignments"][0]
    assert role_assignment.role_id == serialized_role_assignment["role_id"]
    assert role_assignment.subject_id == serialized_role_assignment["subject_id"]
    assert (
        role_assignment.subject_type.id == serialized_role_assignment["subject_type_id"]
    )
