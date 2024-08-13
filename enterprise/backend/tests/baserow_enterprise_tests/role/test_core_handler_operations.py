import pytest
from pytest_unordered import unordered

from baserow.core.exceptions import PermissionDenied
from baserow.core.handler import CoreHandler
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role


@pytest.fixture(autouse=True)
def enable_enterprise_and_synced_roles_for_all_tests_here(
    enable_enterprise, synced_roles
):
    pass


@pytest.mark.django_db()
def test_viewer_and_up_can_reoder_applications_in_workspace(data_fixture):
    admin = data_fixture.create_user()
    viewer = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin, members=[viewer])
    database_1 = data_fixture.create_database_application(workspace=workspace)
    database_2 = data_fixture.create_database_application(workspace=workspace)

    admin_role = Role.objects.get(uid="ADMIN")
    viewer_role = Role.objects.get(uid="VIEWER")

    RoleAssignmentHandler().assign_role(admin, workspace, role=admin_role)
    RoleAssignmentHandler().assign_role(viewer, workspace, role=viewer_role)

    with pytest.raises(PermissionDenied):
        CoreHandler().order_applications(
            viewer, workspace, [database_2.id, database_1.id]
        )

    # Let's a assign an admin role at workspace level but a lower level to the single
    # database application.
    RoleAssignmentHandler().assign_role(viewer, workspace, role=admin_role)
    RoleAssignmentHandler().assign_role(
        viewer, workspace, role=viewer_role, scope=database_1.application_ptr
    )

    # Now it should be possible to reorder the applications.
    order = CoreHandler().order_applications(
        viewer, workspace, [database_2.id, database_1.id]
    )

    assert order == unordered([database_2.id, database_1.id])
