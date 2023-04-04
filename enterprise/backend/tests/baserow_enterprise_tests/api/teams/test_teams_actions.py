from typing import cast

import pytest

from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow_enterprise.models import Team, TeamSubject
from baserow_enterprise.role.models import Role
from baserow_enterprise.scopes import TeamsActionScopeType
from baserow_enterprise.teams.actions import (
    CreateTeamActionType,
    CreateTeamSubjectActionType,
    DeleteTeamActionType,
    DeleteTeamSubjectActionType,
    UpdateTeamActionType,
)
from baserow_enterprise.teams.handler import TeamForUpdate, TeamHandler


@pytest.fixture(autouse=True)
def enable_enterprise_and_roles_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_creating_team(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)

    action_type_registry.get_by_type(CreateTeamActionType).do(user, "test", workspace)

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)

    assert Team.objects.filter(workspace=workspace).count() == 0


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_creating_team(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)

    team1 = action_type_registry.get_by_type(CreateTeamActionType).do(
        user, "test1", workspace
    )
    team2 = action_type_registry.get_by_type(CreateTeamActionType).do(
        user, "test2", workspace
    )

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)

    assert not Team.objects.filter(pk=team2.id).exists()
    assert Team.objects.filter(pk=team1.id).exists()

    ActionHandler.redo(user, [TeamsActionScopeType.value(workspace.id)], session_id)

    assert Team.objects.filter(pk=team2.id).exists()
    assert Team.objects.filter(pk=team1.id).exists()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_updating_team(data_fixture):
    session_id = "session-id"
    role_viewer = Role.objects.get(uid="VIEWER")
    role_builder = Role.objects.get(uid="BUILDER")
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)

    team = action_type_registry.get_by_type(CreateTeamActionType).do(
        user, "original name", workspace, default_role=role_viewer
    )

    team = action_type_registry.get_by_type(UpdateTeamActionType).do(
        user, cast(TeamForUpdate, team), "updated name", default_role=role_builder
    )

    assert team.name == "updated name"
    assert team.default_role_uid == "BUILDER"

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)

    team = TeamHandler().get_team(user, team.pk)
    assert team.name == "original name"
    assert team.default_role_uid == "VIEWER"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_updating_team(data_fixture):
    session_id = "session-id"
    role_viewer = Role.objects.get(uid="VIEWER")
    role_builder = Role.objects.get(uid="BUILDER")
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)

    team = action_type_registry.get_by_type(CreateTeamActionType).do(
        user, "original name", workspace, default_role=role_viewer
    )

    team = action_type_registry.get_by_type(UpdateTeamActionType).do(
        user, cast(TeamForUpdate, team), "updated name", default_role=role_builder
    )
    assert team.name == "updated name"
    assert team.default_role_uid == "BUILDER"

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    team = TeamHandler().get_team(user, team.pk)
    assert team.name == "original name"
    assert team.default_role_uid == "VIEWER"

    ActionHandler.redo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    team = TeamHandler().get_team(user, team.pk)
    assert team.name == "updated name"
    assert team.default_role_uid == "BUILDER"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_deleting_team(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)

    team = action_type_registry.get_by_type(CreateTeamActionType).do(
        user, "test", workspace
    )
    assert Team.objects.filter(pk=team.pk).exists()

    action_type_registry.get_by_type(DeleteTeamActionType).do(user, team)
    assert not Team.objects.filter(pk=team.pk).exists()

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    assert Team.objects.filter(pk=team.pk).exists()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_deleting_team(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=user)

    team = action_type_registry.get_by_type(CreateTeamActionType).do(
        user, "test", workspace
    )
    assert Team.objects.filter(pk=team.pk).exists()

    action_type_registry.get_by_type(DeleteTeamActionType).do(user, team)
    assert not Team.objects.filter(pk=team.pk).exists()

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    assert Team.objects.filter(pk=team.pk).exists()

    ActionHandler.redo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    assert not Team.objects.filter(pk=team.pk).exists()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_creating_subject_by_id(data_fixture, enterprise_data_fixture):
    session_id = "session-id"
    invitee = data_fixture.create_user()
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=invitee)
    team = enterprise_data_fixture.create_team(workspace=workspace)

    action_type_registry.get_by_type(CreateTeamSubjectActionType).do(
        user, {"id": invitee.id}, "auth.User", team
    )

    assert TeamSubject.objects.filter(team=team).exists()

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)

    assert not TeamSubject.objects.filter(team=team).exists()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_creating_subject_by_id(data_fixture, enterprise_data_fixture):
    session_id = "session-id"
    invitee = data_fixture.create_user()
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=invitee)
    team = enterprise_data_fixture.create_team(workspace=workspace)

    subject = action_type_registry.get_by_type(CreateTeamSubjectActionType).do(
        user, {"id": invitee.id}, "auth.User", team
    )
    assert TeamSubject.objects.filter(pk=subject.id).exists()

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    assert not TeamSubject.objects.filter(pk=subject.id).exists()

    ActionHandler.redo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    assert TeamSubject.objects.filter(pk=subject.id).exists()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_creating_subject_by_email(data_fixture, enterprise_data_fixture):
    session_id = "session-id"
    invitee = data_fixture.create_user()
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=invitee)
    team = enterprise_data_fixture.create_team(workspace=workspace)

    action_type_registry.get_by_type(CreateTeamSubjectActionType).do(
        user, {"email": invitee.email}, "auth.User", team
    )

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)

    assert not TeamSubject.objects.filter(team=team).exists()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_creating_subject_by_email(data_fixture, enterprise_data_fixture):
    session_id = "session-id"
    invitee = data_fixture.create_user()
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=invitee)
    team = enterprise_data_fixture.create_team(workspace=workspace)

    subject = action_type_registry.get_by_type(CreateTeamSubjectActionType).do(
        user, {"email": invitee.email}, "auth.User", team
    )
    assert TeamSubject.objects.filter(pk=subject.id).exists()

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    assert not TeamSubject.objects.filter(pk=subject.id).exists()

    ActionHandler.redo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    assert TeamSubject.objects.filter(pk=subject.id).exists()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_deleting_team_subject(data_fixture, enterprise_data_fixture):
    session_id = "session-id"
    invitee = data_fixture.create_user()
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=invitee)
    team = enterprise_data_fixture.create_team(workspace=workspace)

    subject = action_type_registry.get_by_type(CreateTeamSubjectActionType).do(
        user, {"id": invitee.id}, "auth.User", team
    )
    subject_id = subject.id
    assert TeamSubject.objects.filter(pk=subject_id).exists()

    action_type_registry.get_by_type(DeleteTeamSubjectActionType).do(user, subject)
    assert not TeamSubject.objects.filter(pk=subject_id).exists()

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    assert TeamSubject.objects.filter(pk=subject_id).exists()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_deleting_team_subject(data_fixture, enterprise_data_fixture):
    session_id = "session-id"
    invitee = data_fixture.create_user()
    user = data_fixture.create_user(session_id=session_id)
    workspace = data_fixture.create_workspace(user=invitee)
    team = enterprise_data_fixture.create_team(workspace=workspace)

    subject = action_type_registry.get_by_type(CreateTeamSubjectActionType).do(
        user, {"id": invitee.id}, "auth.User", team
    )
    subject_id = subject.id
    assert TeamSubject.objects.filter(pk=subject_id).exists()

    action_type_registry.get_by_type(DeleteTeamSubjectActionType).do(user, subject)
    assert not TeamSubject.objects.filter(pk=subject_id).exists()

    ActionHandler.undo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    assert TeamSubject.objects.filter(pk=subject_id).exists()

    ActionHandler.redo(user, [TeamsActionScopeType.value(workspace.id)], session_id)
    assert not TeamSubject.objects.filter(pk=subject_id).exists()
