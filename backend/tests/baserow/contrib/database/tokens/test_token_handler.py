import string

from django.http import HttpRequest

import pytest
from pytest_unordered import unordered
from rest_framework.request import Request

from baserow.contrib.database.exceptions import DatabaseDoesNotBelongToGroup
from baserow.contrib.database.table.exceptions import TableDoesNotBelongToGroup
from baserow.contrib.database.tokens.exceptions import (
    MaximumUniqueTokenTriesError,
    NoPermissionToTable,
    TokenDoesNotBelongToUser,
    TokenDoesNotExist,
)
from baserow.contrib.database.tokens.handler import TokenHandler
from baserow.contrib.database.tokens.models import Token, TokenPermission
from baserow.core.exceptions import UserNotInWorkspace


@pytest.mark.django_db
def test_get_by_key(data_fixture):
    user = data_fixture.create_user()
    data_fixture.create_user()
    workspace_1 = data_fixture.create_workspace(user=user)
    workspace_2 = data_fixture.create_workspace()
    token = data_fixture.create_token(user=user, workspace=workspace_1)
    data_fixture.create_token(user=user, workspace=workspace_2)

    handler = TokenHandler()

    with pytest.raises(TokenDoesNotExist):
        handler.get_by_key(key="abc")

    token_tmp = handler.get_by_key(key=token.key)
    assert token_tmp.id == token.id
    assert token.workspace_id == workspace_1.id
    assert isinstance(token_tmp, Token)


@pytest.mark.django_db
def test_get_token(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    workspace_1 = data_fixture.create_workspace(user=user)
    workspace_2 = data_fixture.create_workspace()
    token = data_fixture.create_token(user=user, workspace=workspace_1)
    token_2 = data_fixture.create_token(user=user, workspace=workspace_2)

    handler = TokenHandler()

    with pytest.raises(TokenDoesNotExist):
        handler.get_token(user=user, token_id=99999)

    with pytest.raises(TokenDoesNotExist):
        handler.get_token(user=user_2, token_id=token.id)

    with pytest.raises(UserNotInWorkspace):
        handler.get_token(user=user, token_id=token_2.id)

    token_tmp = handler.get_token(user, token.id)
    assert token_tmp.id == token.id
    assert token.workspace_id == workspace_1.id
    assert isinstance(token_tmp, Token)

    # If the error is raised we know for sure that the query has resolved.
    with pytest.raises(AttributeError):
        handler.get_token(
            user=user,
            token_id=token.id,
            base_queryset=Token.objects.prefetch_related("UNKNOWN"),
        )


@pytest.mark.django_db
def test_generate_token(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    handler = TokenHandler()

    assert len(handler.generate_unique_key(32)) == 32
    assert len(handler.generate_unique_key(10)) == 10
    assert handler.generate_unique_key(32) != handler.generate_unique_key(32)

    key = handler.generate_unique_key(32)
    assert not Token.objects.filter(key=key).exists()

    for char in string.ascii_letters + string.digits:
        data_fixture.create_token(key=char, user=user, workspace=workspace)

    with pytest.raises(MaximumUniqueTokenTriesError):
        handler.generate_unique_key(1, 3)


@pytest.mark.django_db
def test_create_token(data_fixture):
    user = data_fixture.create_user()
    workspace_1 = data_fixture.create_workspace(user=user)
    workspace_2 = data_fixture.create_workspace()

    handler = TokenHandler()

    with pytest.raises(UserNotInWorkspace):
        handler.create_token(user=user, workspace=workspace_2, name="Test")

    token = handler.create_token(user=user, workspace=workspace_1, name="Test")
    assert token.user_id == user.id
    assert token.workspace_id == workspace_1.id
    assert token.name == "Test"
    assert len(token.key) == 32

    assert Token.objects.all().count() == 1

    permissions = TokenPermission.objects.all()
    assert permissions.count() == 4

    permissions_types = []
    for perm in permissions:
        assert perm.token_id == token.id
        assert perm.database_id is None
        assert perm.table_id is None
        permissions_types.append(perm.type)

    assert permissions_types == unordered(["create", "read", "update", "delete"])


@pytest.mark.django_db
def test_rotate_token_key(data_fixture):
    user = data_fixture.create_user()
    token_1 = data_fixture.create_token(user=user)
    token_2 = data_fixture.create_token()

    handler = TokenHandler()

    with pytest.raises(TokenDoesNotBelongToUser):
        handler.rotate_token_key(user=user, token=token_2)

    old_key = token_1.key
    new_token = handler.rotate_token_key(user=user, token=token_1)
    assert len(new_token.key) == 32
    assert old_key != new_token.key


@pytest.mark.django_db
def test_update_token(data_fixture):
    user = data_fixture.create_user()
    token_1 = data_fixture.create_token(user=user)
    token_2 = data_fixture.create_token()

    handler = TokenHandler()

    with pytest.raises(TokenDoesNotBelongToUser):
        handler.update_token(user=user, token=token_2, name="New")

    token_1 = handler.update_token(user=user, token=token_1, name="New")
    assert token_1.name == "New"

    token_1 = Token.objects.get(pk=token_1.id)
    assert token_1.name == "New"


@pytest.mark.django_db
def test_update_token_permission(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database_1 = data_fixture.create_database_application(workspace=workspace)
    database_2 = data_fixture.create_database_application(workspace=workspace)
    other_database = data_fixture.create_database_application()
    table_1 = data_fixture.create_database_table(
        database=database_1, create_table=False
    )
    table_2 = data_fixture.create_database_table(
        database=database_2, create_table=False
    )
    other_table = data_fixture.create_database_table(create_table=False)
    token_1 = data_fixture.create_token(user=user, workspace=workspace)
    token_2 = data_fixture.create_token()

    handler = TokenHandler()

    with pytest.raises(TokenDoesNotBelongToUser):
        handler.update_token_permissions(user=user, token=token_2)

    with pytest.raises(DatabaseDoesNotBelongToGroup):
        handler.update_token_permissions(
            user=user, token=token_1, create=[other_database]
        )

    with pytest.raises(TableDoesNotBelongToGroup):
        handler.update_token_permissions(user=user, token=token_1, create=[other_table])

    handler.update_token_permissions(user, token=token_1)
    assert TokenPermission.objects.all().count() == 0

    handler.update_token_permissions(
        user, token=token_1, create=True, read=True, update=True, delete=True
    )
    assert TokenPermission.objects.all().count() == 4
    TokenPermission.objects.get(
        token=token_1, type="create", database__isnull=True, table__isnull=True
    )
    TokenPermission.objects.get(
        token=token_1, type="read", database__isnull=True, table__isnull=True
    )
    TokenPermission.objects.get(
        token=token_1, type="update", database__isnull=True, table__isnull=True
    )
    TokenPermission.objects.get(
        token=token_1, type="delete", database__isnull=True, table__isnull=True
    )

    handler.update_token_permissions(
        user,
        token=token_1,
        create=[database_1],
        read=[database_2, table_2],
        update=[table_1],
        delete=True,
    )
    assert TokenPermission.objects.all().count() == 5
    permission_2_1 = TokenPermission.objects.get(
        token=token_1, type="create", database_id=database_1.id, table__isnull=True
    )
    permission_2_2 = TokenPermission.objects.get(
        token=token_1, type="read", database_id=database_2.id, table__isnull=True
    )
    TokenPermission.objects.get(
        token=token_1, type="read", database__isnull=True, table_id=table_2.id
    )
    permission_2_4 = TokenPermission.objects.get(
        token=token_1, type="update", database__isnull=True, table_id=table_1.id
    )
    TokenPermission.objects.get(
        token=token_1, type="delete", database__isnull=True, table__isnull=True
    )

    handler.update_token_permissions(
        user,
        token=token_1,
        create=[database_1, table_2],
        read=[database_2],
        update=[table_1],
        delete=False,
    )
    assert TokenPermission.objects.all().count() == 4
    permission_3_1 = TokenPermission.objects.get(
        token=token_1, type="create", database_id=database_1.id, table__isnull=True
    )
    TokenPermission.objects.get(
        token=token_1, type="create", database__isnull=True, table_id=table_2.id
    )
    permission_3_3 = TokenPermission.objects.get(
        token=token_1, type="read", database_id=database_2.id, table__isnull=True
    )
    permission_3_4 = TokenPermission.objects.get(
        token=token_1, type="update", database__isnull=True, table_id=table_1.id
    )

    # Check if the same permissions have not been reinserted.
    assert permission_3_1.id == permission_2_1.id
    assert permission_3_3.id == permission_2_2.id
    assert permission_3_4.id == permission_2_4.id


@pytest.mark.django_db
def test_has_table_permission(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    user_3 = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    workspace_2 = data_fixture.create_workspace(user=user_2)
    workspace_3 = data_fixture.create_workspace(users=[user, user_3])
    database_1 = data_fixture.create_database_application(workspace=workspace)
    database_2 = data_fixture.create_database_application(workspace=workspace)
    database_3 = data_fixture.create_database_application(workspace=workspace_2)
    database_4 = data_fixture.create_database_application(workspace=workspace_3)
    table_1 = data_fixture.create_database_table(database=database_1)
    table_2 = data_fixture.create_database_table(database=database_1)
    table_3 = data_fixture.create_database_table(database=database_2)
    table_4 = data_fixture.create_database_table(database=database_3)
    table_5 = data_fixture.create_database_table(database=database_4)

    handler = TokenHandler()

    token_other_workspace = data_fixture.create_token(user=user)
    token = data_fixture.create_token(user=user, workspace=workspace)
    token_user_3 = data_fixture.create_token(user=user_3, workspace=workspace_3)
    token_workspace_3 = data_fixture.create_token(user=user, workspace=workspace_3)

    # Has access to all tables within the workspace.
    handler.update_token_permissions(
        user=user, token=token, create=True, read=True, update=True, delete=True
    )
    handler.update_token_permissions(
        user=user,
        token=token_other_workspace,
        create=True,
        read=True,
        update=True,
        delete=True,
    )
    handler.update_token_permissions(
        user=user_3,
        token=token_user_3,
        create=True,
        read=True,
        update=True,
        delete=True,
    )
    handler.update_token_permissions(
        user=user,
        token=token_workspace_3,
        create=True,
        read=True,
        update=True,
        delete=True,
    )

    assert not handler.has_table_permission(token_other_workspace, "create", table_1)
    assert not handler.has_table_permission(token_other_workspace, "read", table_1)
    assert not handler.has_table_permission(token_other_workspace, "update", table_1)
    assert not handler.has_table_permission(token_other_workspace, "delete", table_1)
    assert not handler.has_table_permission(token_other_workspace, "create", table_2)
    assert not handler.has_table_permission(token_other_workspace, "read", table_2)
    assert not handler.has_table_permission(token_other_workspace, "update", table_2)
    assert not handler.has_table_permission(token_other_workspace, "delete", table_2)
    assert not handler.has_table_permission(token_other_workspace, "create", table_3)
    assert not handler.has_table_permission(token_other_workspace, "read", table_3)
    assert not handler.has_table_permission(token_other_workspace, "update", table_3)
    assert not handler.has_table_permission(token_other_workspace, "delete", table_3)
    assert not handler.has_table_permission(token_other_workspace, "create", table_4)
    assert not handler.has_table_permission(token_other_workspace, "read", table_4)
    assert not handler.has_table_permission(token_other_workspace, "update", table_4)
    assert not handler.has_table_permission(token_other_workspace, "delete", table_4)
    assert not handler.has_table_permission(token_other_workspace, "create", table_5)
    assert not handler.has_table_permission(token_other_workspace, "read", table_5)
    assert not handler.has_table_permission(token_other_workspace, "update", table_5)
    assert not handler.has_table_permission(token_other_workspace, "delete", table_5)

    assert not handler.has_table_permission(token_workspace_3, "create", table_1)
    assert not handler.has_table_permission(token_workspace_3, "read", table_1)
    assert not handler.has_table_permission(token_workspace_3, "update", table_1)
    assert not handler.has_table_permission(token_workspace_3, "delete", table_1)
    assert not handler.has_table_permission(token_workspace_3, "create", table_2)
    assert not handler.has_table_permission(token_workspace_3, "read", table_2)
    assert not handler.has_table_permission(token_workspace_3, "update", table_2)
    assert not handler.has_table_permission(token_workspace_3, "delete", table_2)
    assert not handler.has_table_permission(token_workspace_3, "create", table_3)
    assert not handler.has_table_permission(token_workspace_3, "read", table_3)
    assert not handler.has_table_permission(token_workspace_3, "update", table_3)
    assert not handler.has_table_permission(token_workspace_3, "delete", table_3)
    assert not handler.has_table_permission(token_workspace_3, "create", table_4)
    assert not handler.has_table_permission(token_workspace_3, "read", table_4)
    assert not handler.has_table_permission(token_workspace_3, "update", table_4)
    assert not handler.has_table_permission(token_workspace_3, "delete", table_4)
    assert handler.has_table_permission(token_workspace_3, "create", table_5)
    assert handler.has_table_permission(token_workspace_3, "read", table_5)
    assert handler.has_table_permission(token_workspace_3, "update", table_5)
    assert handler.has_table_permission(token_workspace_3, "delete", table_5)

    assert not handler.has_table_permission(token_user_3, "create", table_1)
    assert not handler.has_table_permission(token_user_3, "read", table_1)
    assert not handler.has_table_permission(token_user_3, "update", table_1)
    assert not handler.has_table_permission(token_user_3, "delete", table_1)
    assert not handler.has_table_permission(token_user_3, "create", table_2)
    assert not handler.has_table_permission(token_user_3, "read", table_2)
    assert not handler.has_table_permission(token_user_3, "update", table_2)
    assert not handler.has_table_permission(token_user_3, "delete", table_2)
    assert not handler.has_table_permission(token_user_3, "create", table_3)
    assert not handler.has_table_permission(token_user_3, "read", table_3)
    assert not handler.has_table_permission(token_user_3, "update", table_3)
    assert not handler.has_table_permission(token_user_3, "delete", table_3)
    assert not handler.has_table_permission(token_user_3, "create", table_4)
    assert not handler.has_table_permission(token_user_3, "read", table_4)
    assert not handler.has_table_permission(token_user_3, "update", table_4)
    assert not handler.has_table_permission(token_user_3, "delete", table_4)
    assert handler.has_table_permission(token_user_3, "create", table_5)
    assert handler.has_table_permission(token_user_3, "read", table_5)
    assert handler.has_table_permission(token_user_3, "update", table_5)
    assert handler.has_table_permission(token_user_3, "delete", table_5)

    assert not handler.has_table_permission(
        token=token, type_name="not_existing", table=table_1
    )
    assert handler.has_table_permission(token, "create", table_1)
    assert handler.has_table_permission(token, "read", table_1)
    assert handler.has_table_permission(token, "update", table_1)
    assert handler.has_table_permission(token, "delete", table_1)
    assert handler.has_table_permission(token, "create", table_2)
    assert handler.has_table_permission(token, "read", table_2)
    assert handler.has_table_permission(token, "update", table_2)
    assert handler.has_table_permission(token, "delete", table_2)
    assert handler.has_table_permission(token, "create", table_3)
    assert handler.has_table_permission(token, "read", table_3)
    assert handler.has_table_permission(token, "update", table_3)
    assert handler.has_table_permission(token, "delete", table_3)
    assert not handler.has_table_permission(token, "create", table_4)
    assert not handler.has_table_permission(token, "read", table_4)
    assert not handler.has_table_permission(token, "update", table_4)
    assert not handler.has_table_permission(token, "delete", table_4)
    assert not handler.has_table_permission(token, "create", table_5)
    assert not handler.has_table_permission(token, "read", table_5)
    assert not handler.has_table_permission(token, "update", table_5)
    assert not handler.has_table_permission(token, "delete", table_5)

    handler.update_token_permissions(
        user=user, token=token, create=False, read=True, update=False, delete=False
    )

    assert not handler.has_table_permission(token, "create", table_1)
    assert handler.has_table_permission(token, "read", table_1)
    assert not handler.has_table_permission(token, "update", table_1)
    assert not handler.has_table_permission(token, "delete", table_1)
    assert not handler.has_table_permission(token, "create", table_2)
    assert handler.has_table_permission(token, "read", table_2)
    assert not handler.has_table_permission(token, "update", table_2)
    assert not handler.has_table_permission(token, "delete", table_2)
    assert not handler.has_table_permission(token, "create", table_3)
    assert handler.has_table_permission(token, "read", table_3)
    assert not handler.has_table_permission(token, "update", table_3)
    assert not handler.has_table_permission(token, "delete", table_3)
    assert not handler.has_table_permission(token, "create", table_4)
    assert not handler.has_table_permission(token, "read", table_4)
    assert not handler.has_table_permission(token, "update", table_4)
    assert not handler.has_table_permission(token, "delete", table_4)
    assert not handler.has_table_permission(token, "create", table_5)
    assert not handler.has_table_permission(token, "read", table_5)
    assert not handler.has_table_permission(token, "update", table_5)
    assert not handler.has_table_permission(token, "delete", table_5)

    handler.update_token_permissions(
        user=user,
        token=token,
        create=[database_1],
        read=False,
        update=False,
        delete=False,
    )

    assert handler.has_table_permission(token, "create", table_1)
    assert not handler.has_table_permission(token, "read", table_1)
    assert not handler.has_table_permission(token, "update", table_1)
    assert not handler.has_table_permission(token, "delete", table_1)
    assert handler.has_table_permission(token, "create", table_2)
    assert not handler.has_table_permission(token, "read", table_2)
    assert not handler.has_table_permission(token, "update", table_2)
    assert not handler.has_table_permission(token, "delete", table_2)
    assert not handler.has_table_permission(token, "create", table_3)
    assert not handler.has_table_permission(token, "read", table_3)
    assert not handler.has_table_permission(token, "update", table_3)
    assert not handler.has_table_permission(token, "delete", table_3)
    assert not handler.has_table_permission(token, "create", table_4)
    assert not handler.has_table_permission(token, "read", table_4)
    assert not handler.has_table_permission(token, "update", table_4)
    assert not handler.has_table_permission(token, "delete", table_4)
    assert not handler.has_table_permission(token, "create", table_5)
    assert not handler.has_table_permission(token, "read", table_5)
    assert not handler.has_table_permission(token, "update", table_5)
    assert not handler.has_table_permission(token, "delete", table_5)

    handler.update_token_permissions(
        user=user, token=token, create=False, read=False, update=[table_3], delete=False
    )

    assert not handler.has_table_permission(token, "create", table_1)
    assert not handler.has_table_permission(token, "read", table_1)
    assert not handler.has_table_permission(token, "update", table_1)
    assert not handler.has_table_permission(token, "delete", table_1)
    assert not handler.has_table_permission(token, "create", table_2)
    assert not handler.has_table_permission(token, "read", table_2)
    assert not handler.has_table_permission(token, "update", table_2)
    assert not handler.has_table_permission(token, "delete", table_2)
    assert not handler.has_table_permission(token, "create", table_3)
    assert not handler.has_table_permission(token, "read", table_3)
    assert handler.has_table_permission(token, "update", table_3)
    assert not handler.has_table_permission(token, "delete", table_3)
    assert not handler.has_table_permission(token, "create", table_4)
    assert not handler.has_table_permission(token, "read", table_4)
    assert not handler.has_table_permission(token, "update", table_4)
    assert not handler.has_table_permission(token, "delete", table_4)
    assert not handler.has_table_permission(token, "create", table_5)
    assert not handler.has_table_permission(token, "read", table_5)
    assert not handler.has_table_permission(token, "update", table_5)
    assert not handler.has_table_permission(token, "delete", table_5)

    handler.update_token_permissions(
        user=user,
        token=token,
        create=True,
        read=[database_2],
        update=[table_3],
        delete=False,
    )

    assert handler.has_table_permission(token, "create", table_1)
    assert not handler.has_table_permission(token, "read", table_1)
    assert not handler.has_table_permission(token, "update", table_1)
    assert not handler.has_table_permission(token, "delete", table_1)
    assert handler.has_table_permission(token, "create", table_2)
    assert not handler.has_table_permission(token, "read", table_2)
    assert not handler.has_table_permission(token, "update", table_2)
    assert not handler.has_table_permission(token, "delete", table_2)
    assert handler.has_table_permission(token, "create", table_3)
    assert handler.has_table_permission(token, "read", table_3)
    assert handler.has_table_permission(token, "update", table_3)
    assert not handler.has_table_permission(token, "delete", table_3)
    assert not handler.has_table_permission(token, "create", table_4)
    assert not handler.has_table_permission(token, "read", table_4)
    assert not handler.has_table_permission(token, "update", table_4)
    assert not handler.has_table_permission(token, "delete", table_4)
    assert not handler.has_table_permission(token, "create", table_5)
    assert not handler.has_table_permission(token, "read", table_5)
    assert not handler.has_table_permission(token, "update", table_5)
    assert not handler.has_table_permission(token, "delete", table_5)

    handler.update_token_permissions(
        user=user,
        token=token,
        create=False,
        read=[database_1],
        update=False,
        delete=True,
    )

    assert not handler.has_table_permission(token, "create", table_1)
    assert handler.has_table_permission(token, "read", table_1)
    assert not handler.has_table_permission(token, "update", table_1)
    assert handler.has_table_permission(token, "delete", table_1)
    assert not handler.has_table_permission(token, "create", table_2)
    assert handler.has_table_permission(token, "read", table_2)
    assert not handler.has_table_permission(token, "update", table_2)
    assert handler.has_table_permission(token, "delete", table_2)
    assert not handler.has_table_permission(token, "create", table_3)
    assert not handler.has_table_permission(token, "read", table_3)
    assert not handler.has_table_permission(token, "update", table_3)
    assert handler.has_table_permission(token, "delete", table_3)
    assert not handler.has_table_permission(token, "create", table_4)
    assert not handler.has_table_permission(token, "read", table_4)
    assert not handler.has_table_permission(token, "update", table_4)
    assert not handler.has_table_permission(token, "delete", table_4)
    assert not handler.has_table_permission(token, "create", table_5)
    assert not handler.has_table_permission(token, "read", table_5)
    assert not handler.has_table_permission(token, "update", table_5)
    assert not handler.has_table_permission(token, "delete", table_5)

    # Test giving a list of permission
    assert handler.has_table_permission(token, ["create", "read", "update"], table_1)
    assert not handler.has_table_permission(token, ["create", "update"], table_1)


@pytest.mark.django_db
def test_check_table_permissions(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table_1 = data_fixture.create_database_table(database=database)
    table_2 = data_fixture.create_database_table()

    handler = TokenHandler()
    token = data_fixture.create_token(user=user, workspace=workspace)
    request = Request(HttpRequest())
    request.user_token = token

    handler.update_token_permissions(
        user=user, token=token, create=True, read=True, update=True, delete=False
    )

    with pytest.raises(ValueError):
        handler.check_table_permissions(None, "create", table_1, False)

    handler.check_table_permissions(Request(HttpRequest()), "create", table_1, False)

    with pytest.raises(NoPermissionToTable):
        handler.check_table_permissions(Request(HttpRequest()), "create", table_1, True)

    handler.check_table_permissions(token, "create", table_1, False)
    handler.check_table_permissions(token, "create", table_1, True)
    handler.check_table_permissions(token, "read", table_1, False)
    handler.check_table_permissions(token, "read", table_1, True)
    handler.check_table_permissions(token, "update", table_1, False)
    handler.check_table_permissions(token, "update", table_1, True)

    with pytest.raises(NoPermissionToTable):
        handler.check_table_permissions(token, "delete", table_1, False)

    with pytest.raises(NoPermissionToTable):
        handler.check_table_permissions(token, "delete", table_1, True)

    handler.check_table_permissions(request, "create", table_1, False)
    handler.check_table_permissions(request, "create", table_1, True)
    handler.check_table_permissions(request, "read", table_1, False)
    handler.check_table_permissions(request, "read", table_1, True)
    handler.check_table_permissions(request, "update", table_1, False)
    handler.check_table_permissions(request, "update", table_1, True)

    with pytest.raises(NoPermissionToTable):
        handler.check_table_permissions(request, "delete", table_1, False)

    with pytest.raises(NoPermissionToTable):
        handler.check_table_permissions(request, "delete", table_1, True)

    with pytest.raises(NoPermissionToTable):
        handler.check_table_permissions(token, "create", table_2, False)

    with pytest.raises(NoPermissionToTable):
        handler.check_table_permissions(token, "create", table_2, True)

    with pytest.raises(NoPermissionToTable):
        handler.check_table_permissions(request, "create", table_2, False)

    with pytest.raises(NoPermissionToTable):
        handler.check_table_permissions(request, "create", table_2, True)


@pytest.mark.django_db
def test_delete_token(data_fixture):
    user = data_fixture.create_user()
    token_1 = data_fixture.create_token(user=user)
    token_2 = data_fixture.create_token()

    handler = TokenHandler()

    with pytest.raises(TokenDoesNotBelongToUser):
        handler.delete_token(user=user, token=token_2)

    handler.update_token_permissions(
        user, token_1, create=True, read=True, update=True, delete=True
    )
    handler.delete_token(user=user, token=token_1)

    assert Token.objects.all().count() == 1
    assert Token.objects.all().first().id == token_2.id
