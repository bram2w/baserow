import pytest

from baserow.core.models import GroupUser
from baserow.contrib.database.models import Database


@pytest.mark.django_db
def test_group_user_get_next_order(data_fixture):
    user = data_fixture.create_user()

    assert GroupUser.get_last_order(user) == 1

    group_user_1 = data_fixture.create_user_group(order=0)
    group_user_2_1 = data_fixture.create_user_group(order=10)
    group_user_2_2 = data_fixture.create_user_group(user=group_user_2_1.user, order=11)

    assert GroupUser.get_last_order(group_user_1.user) == 1
    assert GroupUser.get_last_order(group_user_2_1.user) == 12


@pytest.mark.django_db
def test_group_has_user(data_fixture):
    user = data_fixture.create_user()
    user_group = data_fixture.create_user_group()

    assert user_group.group.has_user(user_group.user)
    assert not user_group.group.has_user(user)


@pytest.mark.django_db
def test_application_content_type_init(data_fixture):
    group = data_fixture.create_group()
    database = Database.objects.create(name='Test 1', order=0, group=group)

    assert database.content_type.app_label == 'database'
    assert database.content_type.model == 'database'
