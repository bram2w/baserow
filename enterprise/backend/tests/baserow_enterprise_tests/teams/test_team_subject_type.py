import pytest

from baserow_enterprise.teams.subjects import TeamSubjectType


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
