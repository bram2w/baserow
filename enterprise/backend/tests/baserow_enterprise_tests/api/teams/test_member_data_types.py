import pytest

from baserow.api.groups.users.serializers import GroupUserSerializer
from baserow_enterprise.api.member_data_types import EnterpriseMemberTeamsDataType


@pytest.mark.django_db
def test_teams_member_datatype_groupuser_without_subjects(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    serializer = GroupUserSerializer(group.groupuser_set.all(), many=True)
    serialized_data = EnterpriseMemberTeamsDataType().annotate_serialized_data(
        group, serializer.data
    )
    assert serialized_data[0]["teams"] == []


@pytest.mark.django_db
def test_teams_member_datatype_groupuser_with_subject(
    data_fixture, enterprise_data_fixture
):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)
    serializer = GroupUserSerializer(group.groupuser_set.all(), many=True)
    serialized_data = EnterpriseMemberTeamsDataType().annotate_serialized_data(
        group, serializer.data
    )
    assert serialized_data[0]["teams"] == [{"id": team.id, "name": team.name}]


@pytest.mark.django_db
def test_teams_member_datatype_groupuser_with_subjects_across_groups(
    data_fixture, enterprise_data_fixture
):
    user = data_fixture.create_user()
    group_a = data_fixture.create_group(user=user)
    team_group_a = enterprise_data_fixture.create_team(group=group_a)
    enterprise_data_fixture.create_subject(team=team_group_a, subject=user)
    group_b = data_fixture.create_group(user=user)
    team_group_b = enterprise_data_fixture.create_team(group=group_b)
    enterprise_data_fixture.create_subject(team=team_group_b, subject=user)
    serializer = GroupUserSerializer(group_a.groupuser_set.all(), many=True)
    serialized_data = EnterpriseMemberTeamsDataType().annotate_serialized_data(
        group_a, serializer.data
    )
    assert serialized_data[0]["teams"] == [
        {"id": team_group_a.id, "name": team_group_a.name}
    ]
