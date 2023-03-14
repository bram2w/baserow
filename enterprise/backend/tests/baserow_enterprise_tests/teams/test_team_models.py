import pytest

from baserow.core.trash.handler import TrashHandler
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role
from baserow_enterprise.teams.handler import TeamHandler
from baserow_enterprise.teams.models import Team, TeamSubject


@pytest.fixture(autouse=True)
def enable_enterprise_and_roles_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.mark.django_db
def test_team_default_role_annotated(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    role = Role.objects.get(uid="BUILDER")
    team_id = TeamHandler().create_team(user, "Sales", workspace, default_role=role).id
    team = TeamHandler().get_team(user, team_id)
    assert team.default_role_uid == "BUILDER"
    assert hasattr(team, "_annotated_default_role_uid")


@pytest.mark.django_db
def test_team_default_role_not_annotated(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    team = Team.objects.create(name="Sales", workspace=workspace)
    role = Role.objects.get(uid="BUILDER")
    RoleAssignmentHandler().assign_role(team, workspace, role)
    assert team.default_role_uid == "BUILDER"
    assert not hasattr(team, "_annotated_default_role_uid")


def test_teamsubject_parent_team_trashable_model_mixin(
    data_fixture, enterprise_data_fixture
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    team = enterprise_data_fixture.create_team(workspace=workspace)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    assert TeamSubject.objects.filter(team=team).count() == 1

    TrashHandler.trash(user, team.workspace, None, team)

    assert TeamSubject.objects.filter(team=team).count() == 0
    assert TeamSubject.objects_and_trash.filter(team=team).count() == 1
