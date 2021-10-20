from unittest.mock import patch

import pytest
from django.db import connection
from django.test.utils import override_settings

from baserow.contrib.database.models import Database, Table
from baserow.core.exceptions import IsNotAdminError
from baserow.core.models import (
    Group,
    GroupUser,
)
from baserow_premium.admin.groups.exceptions import CannotDeleteATemplateGroupError
from baserow_premium.admin.groups.handler import GroupsAdminHandler
from baserow_premium.license.exceptions import NoPremiumLicenseError


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.core.signals.group_deleted.send")
def test_delete_group(send_mock, premium_data_fixture):
    staff_user_with_premium_license = premium_data_fixture.create_user(
        is_staff=True, has_active_premium_license=True
    )
    normal_user = premium_data_fixture.create_user(
        is_staff=False, has_active_premium_license=True
    )
    other_user = premium_data_fixture.create_user()
    group_1 = premium_data_fixture.create_group(user=other_user)
    database = premium_data_fixture.create_database_application(group=group_1)
    table = premium_data_fixture.create_database_table(database=database)

    handler = GroupsAdminHandler()

    with pytest.raises(IsNotAdminError):
        handler.delete_group(normal_user, group_1)

    handler.delete_group(staff_user_with_premium_license, group_1)

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["group"].id == group_1.id
    assert "user" not in send_mock.call_args[1]
    assert len(send_mock.call_args[1]["group_users"]) == 1
    assert send_mock.call_args[1]["group_users"][0].id == other_user.id

    assert Database.objects.all().count() == 0
    assert Table.objects.all().count() == 0
    assert f"database_table_{table.id}" not in connection.introspection.table_names()
    assert Group.objects.all().count() == 0
    assert GroupUser.objects.all().count() == 0


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.core.signals.group_deleted.send")
def test_cant_delete_template_group(send_mock, premium_data_fixture):
    staff_user = premium_data_fixture.create_user(
        is_staff=True, has_active_premium_license=True
    )
    group_1 = premium_data_fixture.create_group(user=staff_user)
    database = premium_data_fixture.create_database_application(group=group_1)
    premium_data_fixture.create_database_table(database=database)

    premium_data_fixture.create_template(group=group_1)

    handler = GroupsAdminHandler()

    with pytest.raises(CannotDeleteATemplateGroupError):
        handler.delete_group(staff_user, group_1)

    send_mock.assert_not_called()
    assert Group.objects.all().count() == 1


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.core.signals.group_deleted.send")
def test_delete_group_without_premium_license(send_mock, premium_data_fixture):
    staff_user = premium_data_fixture.create_user(is_staff=True)
    other_user = premium_data_fixture.create_user()
    group_1 = premium_data_fixture.create_group(user=other_user)

    handler = GroupsAdminHandler()

    with pytest.raises(NoPremiumLicenseError):
        handler.delete_group(staff_user, group_1)

    send_mock.assert_not_called()
    assert Group.objects.all().count() == 1
