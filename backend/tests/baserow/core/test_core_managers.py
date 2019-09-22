import pytest

from baserow.core.models import Group


@pytest.mark.django_db
def test_groups_of_user(data_fixture):
    user_1 = data_fixture.create_user()
    user_group_1 = data_fixture.create_user_group(user=user_1, order=1)
    user_group_2 = data_fixture.create_user_group(user=user_1, order=2)
    user_group_3 = data_fixture.create_user_group(user=user_1, order=0)

    user_2 = data_fixture.create_user()
    user_group_4 = data_fixture.create_user_group(user=user_2, order=0)

    groups_user_1 = Group.objects.of_user(user=user_1)
    assert len(groups_user_1) == 3

    assert groups_user_1[0].id == user_group_3.group.id
    assert groups_user_1[1].id == user_group_1.group.id
    assert groups_user_1[2].id == user_group_2.group.id

    groups_user_2 = Group.objects.of_user(user=user_2)
    assert len(groups_user_2) == 1
    assert groups_user_2[0].id == user_group_4.group.id
