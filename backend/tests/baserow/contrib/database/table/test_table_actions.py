import pytest

from baserow.core.action.scopes import (
    ApplicationActionScopeType,
)
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import (
    action_type_registry,
)
from baserow.contrib.database.table.actions import (
    CreateTableActionType,
    DeleteTableActionType,
    OrderTableActionType,
    UpdateTableActionType,
)
from baserow.contrib.database.table.models import Table


@pytest.mark.django_db
def test_can_undo_creating_table(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    database = data_fixture.create_database_application(user=user)

    table = action_type_registry.get_by_type(CreateTableActionType).do(
        user, database, fill_example=True, name="test"
    )

    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )

    assert Table.objects.filter(pk=table.id).count() == 0


@pytest.mark.django_db
def test_can_undo_redo_creating_table(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    database = data_fixture.create_database_application(user=user)

    table = action_type_registry.get_by_type(CreateTableActionType).do(
        user, database, fill_example=True, name="test"
    )

    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )

    assert Table.objects.filter(pk=table.id).count() == 0

    ActionHandler.redo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )

    assert Table.objects.filter(pk=table.id).count() == 1


@pytest.mark.django_db
def test_can_undo_deleting_table(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database, user=user)

    action_type_registry.get_by_type(DeleteTableActionType).do(user, table)

    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )

    assert Table.objects.filter(pk=table.id).count() == 1


@pytest.mark.django_db
def test_can_undo_redo_deleting_table(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database, user=user)

    action_type_registry.get_by_type(DeleteTableActionType).do(user, table)

    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )

    assert Table.objects.filter(pk=table.id).count() == 1

    ActionHandler.redo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )

    assert Table.objects.filter(pk=table.id).count() == 0


@pytest.mark.django_db
def test_can_undo_ordering_tables(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    database = data_fixture.create_database_application(user=user)
    table_1 = data_fixture.create_database_table(database=database, user=user)
    table_2 = data_fixture.create_database_table(database=database, user=user)
    table_3 = data_fixture.create_database_table(database=database, user=user)

    def get_tables_order():
        return [t.id for t in database.table_set.order_by("order")]

    original_order = get_tables_order()
    new_order = [table_2.id, table_3.id, table_1.id]

    assert original_order != new_order

    action_type_registry.get_by_type(OrderTableActionType).do(
        user, database, order=new_order
    )
    assert get_tables_order() == new_order

    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )
    assert get_tables_order() == original_order


@pytest.mark.django_db
def test_can_undo_redo_ordering_tables(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    database = data_fixture.create_database_application(user=user)
    table_1 = data_fixture.create_database_table(database=database, user=user)
    table_2 = data_fixture.create_database_table(database=database, user=user)
    table_3 = data_fixture.create_database_table(database=database, user=user)

    def get_tables_order():
        return [t.id for t in database.table_set.all()]

    original_order = get_tables_order()
    new_order = [table_2.id, table_3.id, table_1.id]

    assert original_order != new_order

    action_type_registry.get_by_type(OrderTableActionType).do(
        user, database, order=new_order
    )
    assert get_tables_order() == new_order

    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )
    assert get_tables_order() == original_order

    ActionHandler.redo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )
    assert get_tables_order() == new_order


@pytest.mark.django_db
def test_can_undo_updating_table(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    database = data_fixture.create_database_application(user=user)

    original_table_name, new_table_name = "original-table-name", "new-table-name"
    table = data_fixture.create_database_table(
        database=database, user=user, name=original_table_name
    )

    table = action_type_registry.get_by_type(UpdateTableActionType).do(
        user, table, name=new_table_name
    )
    assert table.name == new_table_name

    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )

    table.refresh_from_db()
    assert table.name == original_table_name


@pytest.mark.django_db
def test_can_undo_redo_updating_table(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    database = data_fixture.create_database_application(user=user)

    original_table_name, new_table_name = "original-table-name", "new-table-name"
    table = data_fixture.create_database_table(
        database=database, user=user, name=original_table_name
    )

    table = action_type_registry.get_by_type(UpdateTableActionType).do(
        user, table, name=new_table_name
    )
    assert table.name == new_table_name

    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )

    table.refresh_from_db()
    assert table.name == original_table_name

    ActionHandler.redo(
        user, [ApplicationActionScopeType.value(application_id=database.id)], session_id
    )

    table.refresh_from_db()
    assert table.name == new_table_name
