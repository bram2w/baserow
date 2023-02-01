from datetime import datetime

import pytest
from freezegun import freeze_time
from pytz import timezone

from baserow.contrib.database.models import Database
from baserow.core.models import Group, GroupUser


@pytest.mark.django_db
def test_created_and_updated_on_mixin():
    with freeze_time("2020-01-01 12:00"):
        group = Group.objects.create(name="Group")

    assert group.created_on == datetime(2020, 1, 1, 12, 00, tzinfo=timezone("UTC"))
    assert group.updated_on == datetime(2020, 1, 1, 12, 00, tzinfo=timezone("UTC"))

    with freeze_time("2020-01-02 12:00"):
        group.name = "Group2"
        group.save()

    assert group.created_on == datetime(2020, 1, 1, 12, 00, tzinfo=timezone("UTC"))
    assert group.updated_on == datetime(2020, 1, 2, 12, 00, tzinfo=timezone("UTC"))


@pytest.mark.django_db
def test_group_user_get_next_order(data_fixture):
    user = data_fixture.create_user()

    assert GroupUser.get_last_order(user) == 1

    group_user_1 = data_fixture.create_user_group(order=0)
    group_user_2_1 = data_fixture.create_user_group(order=10)
    data_fixture.create_user_group(user=group_user_2_1.user, order=11)

    assert GroupUser.get_last_order(group_user_1.user) == 1
    assert GroupUser.get_last_order(group_user_2_1.user) == 12


@pytest.mark.django_db
def test_application_content_type_init(data_fixture):
    group = data_fixture.create_group()
    database = Database.objects.create(name="Test 1", order=0, group=group)

    assert database.content_type.app_label == "database"
    assert database.content_type.model == "database"


@pytest.mark.django_db
def test_core_models_hierarchy(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    app = data_fixture.create_database_application(group=group, name="Test 1")

    assert app.get_parent() == group
    assert app.get_root() == group

    assert group.get_parent() is None
    assert group.get_root() == group
