import pytest

from baserow.contrib.database.tokens.actions import (
    CreateDbTokenActionType,
    DeleteDbTokenActionType,
    RotateDbTokenKeyActionType,
    UpdateDbTokenNameActionType,
    UpdateDbTokenPermissionsActionType,
)
from baserow.contrib.database.tokens.handler import TokenHandler
from baserow.contrib.database.tokens.models import Token, TokenPermission
from baserow.core.action.registries import action_type_registry


@pytest.mark.django_db
def test_create_db_token_action_type(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    token = action_type_registry.get(CreateDbTokenActionType.type).do(
        user, workspace, "token"
    )
    assert token.name == "token"
    assert token.workspace_id == workspace.id
    assert token.key is not None


@pytest.mark.django_db
def test_delete_db_token_action_type(data_fixture):
    user = data_fixture.create_user()
    token = data_fixture.create_token(user=user)

    assert Token.objects.count() == 1
    action_type_registry.get(DeleteDbTokenActionType.type).do(user, token)
    assert Token.objects.count() == 0


@pytest.mark.django_db
def test_rotate_db_token_key_action_type(data_fixture):
    user = data_fixture.create_user()
    token = data_fixture.create_token(user=user)

    original_key = token.key
    action_type_registry.get(RotateDbTokenKeyActionType.type).do(user, token)
    assert token.key != original_key


@pytest.mark.django_db
def test_update_db_token_name_action_type(data_fixture):
    user = data_fixture.create_user()
    token = data_fixture.create_token(user=user, name="old name")

    assert token.name == "old name"
    action_type_registry.get(UpdateDbTokenNameActionType.type).do(
        user, token, "new name"
    )
    assert token.name == "new name"


@pytest.mark.django_db
def test_update_db_token_permissions_action_type(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    token = TokenHandler().create_token(user, workspace, "token")

    assert TokenPermission.objects.filter(token=token, type="create").count() == 1
    action_type_registry.get(UpdateDbTokenPermissionsActionType.type).do(
        user, token, create=False
    )
    assert TokenPermission.objects.filter(token=token, type="create").count() == 0
