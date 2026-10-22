import pytest

from baserow.core.jobs.handler import JobHandler
from baserow.core.models import Template, TemplateCategory
from baserow.core.user_templates.job_types import CreateUserTemplateJobType
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import RoleAssignment


@pytest.mark.import_export_workspace
@pytest.mark.django_db(transaction=True)
def test_create_user_template_doesnt_copy_role_assignments(
    enterprise_data_fixture, enable_enterprise, synced_roles, use_tmp_media_root
):
    user = enterprise_data_fixture.create_user()
    member = enterprise_data_fixture.create_user()
    workspace = enterprise_data_fixture.create_workspace(user=user, members=[member])
    database = enterprise_data_fixture.create_database_application(workspace=workspace)
    table = enterprise_data_fixture.create_database_table(database=database)
    admin = RoleAssignmentHandler().get_role_by_uid("ADMIN")
    viewer = RoleAssignmentHandler().get_role_by_uid("VIEWER")
    RoleAssignmentHandler().assign_role(user, workspace, role=admin, scope=workspace)
    RoleAssignmentHandler().assign_role(member, workspace, role=admin, scope=database)
    RoleAssignmentHandler().assign_role(member, workspace, role=viewer, scope=table)
    assignment_count = RoleAssignment.objects.count()

    JobHandler().create_and_start_job(
        user,
        CreateUserTemplateJobType.type,
        sync=True,
        workspace_id=workspace.id,
        application_ids=[database.id],
        name="My template",
        icon="iconoir-view-grid",
        category_ids=[TemplateCategory.objects.create(name="Cat").id],
    )

    # The members of the source workspace aren't members of the template.
    template_workspace = Template.objects.get().workspace
    assert not RoleAssignment.objects.filter(workspace=template_workspace).exists()
    assert RoleAssignment.objects.count() == assignment_count
