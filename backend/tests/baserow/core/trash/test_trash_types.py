from django.db import connection

import pytest

from baserow.contrib.database.models import Database
from baserow.contrib.database.table.models import Table
from baserow.core.models import Workspace, WorkspaceUser
from baserow.core.trash.handler import TrashHandler
from baserow.core.trash.trash_types import WorkspaceTrashableItemType


@pytest.mark.django_db
def test_perm_delete_workspace(data_fixture):
    user = data_fixture.create_user()
    workspace_1 = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace_1)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_workspace(user=user)
    user_2 = data_fixture.create_user()
    workspace_3 = data_fixture.create_workspace(user=user_2)

    handler = WorkspaceTrashableItemType()
    handler.permanently_delete_item(workspace_1)

    assert Database.objects.all().count() == 0
    assert Table.objects.all().count() == 0
    assert f"database_table_{table.id}" not in connection.introspection.table_names()
    assert Workspace.objects.all().count() == 2
    assert WorkspaceUser.objects.all().count() == 2

    handler.permanently_delete_item(workspace_3)

    assert Workspace.objects.all().count() == 1
    assert WorkspaceUser.objects.all().count() == 1


@pytest.mark.django_db
def test_perm_delete_application(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)

    handler = TrashHandler()

    handler.permanently_delete(database)

    assert Database.objects.all().count() == 0
    assert Table.objects.all().count() == 0
    assert f"database_table_{table.id}" not in connection.introspection.table_names()
