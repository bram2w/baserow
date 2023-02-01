from typing import NamedTuple

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

    class FakeTeam(NamedTuple):
        id: int

    fake_team = FakeTeam(99999)

    assert TeamSubjectType().is_in_group(team_not_in_group, group) is False
    assert TeamSubjectType().is_in_group(team_in_group, group) is True
    assert TeamSubjectType().is_in_group(fake_team, group) is False
    assert TeamSubjectType().is_in_group(trashed_team, group) is False

    assert TeamSubjectType().are_in_group(
        [
            team_not_in_group,
            team_in_group,
            fake_team,
            trashed_team,
        ],
        group,
    ) == [False, True, False, False]


@pytest.mark.django_db
def test_team_subject_get_users_included_in_subject(enterprise_data_fixture):
    user_1 = enterprise_data_fixture.create_user()
    user_2 = enterprise_data_fixture.create_user()
    group = enterprise_data_fixture.create_group(user=user_1, members=[user_2])
    team = enterprise_data_fixture.create_team(group=group)

    TeamHandler().create_subject(user_1, {"id": user_1.id}, "auth.User", team)
    TeamHandler().create_subject(user_1, {"id": user_2.id}, "auth.User", team)

    associated_users = TeamSubjectType().get_users_included_in_subject(team)

    assert user_1 in associated_users
    assert user_2 in associated_users
