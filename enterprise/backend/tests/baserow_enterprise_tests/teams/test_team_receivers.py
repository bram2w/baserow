from unittest.mock import patch

from django.contrib.auth import get_user_model

import pytest

from baserow_enterprise.teams.models import TeamSubject
from baserow_enterprise.teams.receivers import (
    connect_to_post_delete_signals_to_cascade_deletion_to_team_subjects,
)

User = get_user_model()


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise):
    pass


@pytest.mark.django_db
def test_delete_user_cascades_to_teamsubject(enterprise_data_fixture):
    workspaceuser = enterprise_data_fixture.create_user_workspace()
    team = enterprise_data_fixture.create_team(workspace=workspaceuser.workspace)
    subject = enterprise_data_fixture.create_subject(
        team=team, subject=workspaceuser.user
    )
    workspaceuser.user.delete()
    assert TeamSubject.objects.filter(pk=subject.id).exists() is False


@pytest.mark.django_db
def test_delete_workspaceuser_cascades_to_teamsubject(enterprise_data_fixture):
    user = enterprise_data_fixture.create_user()

    workspace_a = enterprise_data_fixture.create_workspace()
    workspaceuser_a = enterprise_data_fixture.create_user_workspace(
        user=user, workspace=workspace_a
    )
    team_a = enterprise_data_fixture.create_team(workspace=workspaceuser_a.workspace)
    enterprise_data_fixture.create_subject(team=team_a, subject=workspaceuser_a.user)

    workspace_b = enterprise_data_fixture.create_workspace()
    workspaceuser_b = enterprise_data_fixture.create_user_workspace(
        user=user, workspace=workspace_b
    )
    team_b = enterprise_data_fixture.create_team(workspace=workspaceuser_b.workspace)
    enterprise_data_fixture.create_subject(team=team_b, subject=workspaceuser_b.user)

    workspaceuser_a.delete()

    assert TeamSubject.objects.filter(team=team_a, subject_id=user.id).exists() is False
    assert TeamSubject.objects.filter(team=team_b, subject_id=user.id).exists() is True


@pytest.mark.django_db
@patch("baserow_enterprise.teams.receivers.cascade_subject_delete")
def test_delete_team_does_not_call_receiver_cascade_subject_delete(
    mock_cascade_subject_delete, enterprise_data_fixture
):
    connect_to_post_delete_signals_to_cascade_deletion_to_team_subjects()
    team = enterprise_data_fixture.create_team()
    team.delete()
    mock_cascade_subject_delete.assert_not_called()
