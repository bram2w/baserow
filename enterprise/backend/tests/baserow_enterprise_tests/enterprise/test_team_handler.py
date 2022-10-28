from unittest.mock import patch

from django.contrib.auth.models import User

import pytest

from baserow_enterprise.exceptions import (
    TeamSubjectBadRequest,
    TeamSubjectDoesNotExist,
    TeamSubjectTypeUnsupported,
)
from baserow_enterprise.teams.handler import TeamHandler


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise):
    pass


@pytest.mark.django_db
def test_create_team(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    team = TeamHandler().create_team(user, "Engineering", group)
    assert team.name == "Engineering"


@pytest.mark.django_db
def test_list_teams_in_group(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    sales = enterprise_data_fixture.create_team(group=group)
    engineering = enterprise_data_fixture.create_team(group=group)
    sales_subj = enterprise_data_fixture.create_subject(team=sales, subject=user)
    teams_qs = TeamHandler().list_teams_in_group(user, group.id).order_by("id")
    assert teams_qs[0].id == sales.id
    assert teams_qs[0].subject_count == 1
    assert teams_qs[0].subject_sample == [
        {
            "subject_id": sales_subj.subject_id,
            "subject_type": sales_subj.subject_type_natural_key,
        }
    ]
    assert teams_qs[1].id == engineering.id
    assert teams_qs[1].subject_count == 0
    assert teams_qs[1].subject_sample == []


@pytest.mark.django_db
def test_update_team_name(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    team = enterprise_data_fixture.create_team(name="Engineering", group=group)
    team = TeamHandler().update_team(user, team, "Sales")
    assert team.name == "Sales"


@pytest.mark.django_db
def test_delete_team(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    data_fixture.create_user_group(group=group, user=user, permissions="ADMIN")
    team = enterprise_data_fixture.create_team(name="Engineering", group=group)
    TeamHandler().delete_team(user, team)


@patch(
    "baserow_enterprise.teams.handler.TeamHandler.is_supported_subject_type",
    return_value=False,
)
def test_create_subject_unsupported_type(
    is_supported_subject_type, enterprise_data_fixture
):
    team = enterprise_data_fixture.create_team()
    with pytest.raises(TeamSubjectTypeUnsupported):
        TeamHandler().create_subject(User(), {"pk": 123}, "foo_bar", team)


@pytest.mark.django_db
def test_create_subject_unknown_subject(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    team = enterprise_data_fixture.create_team()
    assert not User.objects.filter(pk=123).exists()
    with pytest.raises(TeamSubjectDoesNotExist):
        TeamHandler().create_subject(user, {"pk": 123}, "auth_user", team)


@pytest.mark.django_db
def test_create_subject_with_unsupported_lookup(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    team = enterprise_data_fixture.create_team()
    with pytest.raises(TeamSubjectBadRequest):
        TeamHandler().create_subject(user, {"username": "baserow"}, "auth_user", team)


@pytest.mark.django_db
def test_create_subject_by_id(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    team = enterprise_data_fixture.create_team(group=group)
    subject = TeamHandler().create_subject(user, {"pk": user.id}, "auth_user", team)
    assert subject.team_id == team.id
    assert subject.subject_id == user.id
    assert isinstance(user, subject.subject_type.model_class())


@pytest.mark.django_db
def test_create_subject_by_email(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    team = enterprise_data_fixture.create_team(group=group)
    subject = TeamHandler().create_subject(
        user, {"email": user.email}, "auth_user", team
    )
    assert subject.team_id == team.id
    assert subject.subject_id == user.id
    assert isinstance(user, subject.subject_type.model_class())


@pytest.mark.django_db
def test_list_subjects_in_team(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    sales = enterprise_data_fixture.create_team(group=group)
    engineering = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=engineering)
    sales_subject_1 = enterprise_data_fixture.create_subject(team=sales)
    sales_subject_2 = enterprise_data_fixture.create_subject(team=sales)
    qs = TeamHandler().list_subjects_in_team(sales.id)
    assert qs.count() == 2
    assert sales_subject_1 in qs
    assert sales_subject_2 in qs
