import pytest

from baserow_enterprise.teams.handler import TeamHandler
from baserow_enterprise.teams.subjects import TeamSubjectType


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise):
    pass


@pytest.mark.django_db
def test_team_subject_type_is_in_group(enterprise_data_fixture):
    group = enterprise_data_fixture.create_group()
    team_not_in_group = enterprise_data_fixture.create_team()
    team_in_group = enterprise_data_fixture.create_team(group=group)
    trashed_team = enterprise_data_fixture.create_team(group=group, trashed=True)

    assert TeamSubjectType().is_in_group(team_not_in_group.id, group) is False
    assert TeamSubjectType().is_in_group(team_in_group.id, group) is True
    assert TeamSubjectType().is_in_group(9999, group) is False
    assert TeamSubjectType().is_in_group(trashed_team.id, group) is False


@pytest.mark.django_db
def test_team_subject_get_associated_users(enterprise_data_fixture):
    user_1 = enterprise_data_fixture.create_user()
    user_2 = enterprise_data_fixture.create_user()
    group = enterprise_data_fixture.create_group(user=user_1, members=[user_2])
    team = enterprise_data_fixture.create_team(group=group)

    TeamHandler().create_subject(user_1, {"id": user_1.id}, "auth.User", team)
    TeamHandler().create_subject(user_1, {"id": user_2.id}, "auth.User", team)

    associated_users = TeamSubjectType().get_associated_users(team)

    assert user_1 in associated_users
    assert user_2 in associated_users
