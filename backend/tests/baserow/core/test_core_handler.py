import pytest

from baserow.core.handler import CoreHandler
from baserow.core.models import Group, GroupUser
from baserow.core.exceptions import UserNotIngroupError


@pytest.mark.django_db
def test_create_group(data_fixture):
    user = data_fixture.create_user()

    handler = CoreHandler()
    handler.create_group(user=user, name='Test group')

    group = Group.objects.all().first()
    user_group = GroupUser.objects.all().first()

    assert group.name == 'Test group'
    assert user_group.user == user
    assert user_group.group == group
    assert user_group.order == 1

    handler.create_group(user=user, name='Test group 2')

    assert Group.objects.all().count() == 2
    assert GroupUser.objects.all().count() == 2


@pytest.mark.django_db
def test_update_group(data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user_1)

    handler = CoreHandler()
    handler.update_group(user=user_1, group=group, name='New name')

    group.refresh_from_db()

    assert group.name == 'New name'

    with pytest.raises(UserNotIngroupError):
        handler.update_group(user=user_2, group=group, name='New name')


@pytest.mark.django_db
def test_delete_group(data_fixture):
    user = data_fixture.create_user()
    group_1 = data_fixture.create_group(user=user)
    group_2 = data_fixture.create_group(user=user)

    user_2 = data_fixture.create_user()
    group_3 = data_fixture.create_group(user=user_2)

    handler = CoreHandler()
    handler.delete_group(user, group_1)

    assert Group.objects.all().count() == 2
    assert GroupUser.objects.all().count() == 2

    with pytest.raises(UserNotIngroupError):
        handler.delete_group(user, group_3)

    handler.delete_group(user_2, group_3)

    assert Group.objects.all().count() == 1
    assert GroupUser.objects.all().count() == 1


@pytest.mark.django_db
def test_order_groups(data_fixture):
    user = data_fixture.create_user()
    ug_1 = data_fixture.create_user_group(user=user, order=1)
    ug_2 = data_fixture.create_user_group(user=user, order=2)
    ug_3 = data_fixture.create_user_group(user=user, order=3)

    assert [1, 2, 3] == [ug_1.order, ug_2.order, ug_3.order]

    handler = CoreHandler()
    handler.order_groups(user, [ug_3.id, ug_2.id, ug_1.id])

    ug_1.refresh_from_db()
    ug_2.refresh_from_db()
    ug_3.refresh_from_db()

    assert [1, 2, 3] == [ug_3.order, ug_2.order, ug_1.order]

    handler.order_groups(user, [ug_2.id, ug_1.id, ug_3.id])

    ug_1.refresh_from_db()
    ug_2.refresh_from_db()
    ug_3.refresh_from_db()

    assert [1, 2, 3] == [ug_2.order, ug_1.order, ug_3.order]
