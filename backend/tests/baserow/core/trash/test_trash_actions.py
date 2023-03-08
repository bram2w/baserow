import pytest

from baserow.core.action.registries import action_type_registry
from baserow.core.models import Group, TrashEntry
from baserow.core.trash.actions import EmptyTrashActionType, RestoreFromTrashActionType
from baserow.core.trash.handler import TrashHandler


@pytest.mark.django_db
def test_empty_aplication_level_trash_action_type(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    application = data_fixture.create_database_application(group=group)
    TrashHandler.trash(user, group, application, application)

    assert TrashEntry.objects.filter(should_be_permanently_deleted=True).count() == 0
    action_type_registry.get(EmptyTrashActionType.type).do(
        user, group.id, application.id
    )
    assert TrashEntry.objects.filter(should_be_permanently_deleted=True).count() == 1


@pytest.mark.django_db
def test_empty_group_level_trash_action_type(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    application = data_fixture.create_database_application(group=group)
    TrashHandler.trash(user, group, application, application)

    assert TrashEntry.objects.filter(should_be_permanently_deleted=True).count() == 0
    action_type_registry.get(EmptyTrashActionType.type).do(user, group.id)
    assert TrashEntry.objects.filter(should_be_permanently_deleted=True).count() == 1


@pytest.mark.django_db
def test_restore_item_action_type(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)

    TrashHandler.trash(user, group, None, group)

    assert Group.objects.count() == 0
    action_type_registry.get(RestoreFromTrashActionType.type).do(
        user, "group", group.id
    )
    assert Group.objects.count() == 1
