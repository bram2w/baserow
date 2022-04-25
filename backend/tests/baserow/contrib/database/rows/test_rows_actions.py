from decimal import Decimal
import pytest

from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import (
    action_type_registry,
)
from baserow.contrib.database.action.scopes import (
    TableActionScopeType,
)
from baserow.contrib.database.rows.actions import (
    CreateRowActionType,
    DeleteRowActionType,
    MoveRowActionType,
)
from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
def test_can_undo_creating_row(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(name="Car", user=user)
    name_field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )
    speed_field = data_fixture.create_number_field(
        table=table, name="Max speed", number_negative=True
    )
    price_field = data_fixture.create_number_field(
        table=table,
        name="Price",
        number_decimal_places=2,
        number_negative=False,
    )
    model = table.get_model()

    row = action_type_registry.get_by_type(CreateRowActionType).do(
        user,
        table,
        values={
            name_field.id: "Tesla",
            speed_field.id: 240,
            f"field_{price_field.id}": 59999.99,
            9999: "Must not be added",
        },
    )

    assert model.objects.all().count() == 1
    assert getattr(row, f"field_{name_field.id}") == "Tesla"
    assert getattr(row, f"field_{speed_field.id}") == 240
    assert getattr(row, f"field_{price_field.id}") == 59999.99
    assert not getattr(row, "field_9999", None)

    ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert model.objects.all().count() == 0


@pytest.mark.django_db
def test_can_undo_redo_creating_row(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(name="Car", user=user)
    name_field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )
    speed_field = data_fixture.create_number_field(
        table=table, name="Max speed", number_negative=True
    )
    price_field = data_fixture.create_number_field(
        table=table,
        name="Price",
        number_decimal_places=2,
        number_negative=False,
    )
    model = table.get_model()

    row = action_type_registry.get_by_type(CreateRowActionType).do(
        user,
        table,
        values={
            name_field.id: "Tesla",
            speed_field.id: 240,
            f"field_{price_field.id}": 59999.99,
            9999: "Must not be added",
        },
    )

    assert model.objects.all().count() == 1
    assert getattr(row, f"field_{name_field.id}") == "Tesla"
    assert getattr(row, f"field_{speed_field.id}") == 240
    assert getattr(row, f"field_{price_field.id}") == 59999.99
    assert not getattr(row, "field_9999", None)

    ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert model.objects.all().count() == 0

    ActionHandler.redo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert model.objects.all().count() == 1


@pytest.mark.django_db
def test_can_undo_deleting_row(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(name="Car", user=user)
    name_field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )
    speed_field = data_fixture.create_number_field(
        table=table, name="Max speed", number_negative=True
    )
    price_field = data_fixture.create_number_field(
        table=table,
        name="Price",
        number_decimal_places=2,
        number_negative=False,
    )
    model = table.get_model()

    row = RowHandler().create_row(
        user,
        table,
        values={
            name_field.id: "Tesla",
            speed_field.id: 240,
            f"field_{price_field.id}": 59999.99,
            9999: "Must not be added",
        },
    )

    assert model.objects.all().count() == 1

    action_type_registry.get_by_type(DeleteRowActionType).do(user, table, row.id)

    assert model.objects.all().count() == 0

    ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert model.objects.all().count() == 1
    assert getattr(row, f"field_{name_field.id}") == "Tesla"
    assert getattr(row, f"field_{speed_field.id}") == 240
    assert getattr(row, f"field_{price_field.id}") == 59999.99
    assert not getattr(row, "field_9999", None)


@pytest.mark.django_db
def test_can_undo_redo_deleting_row(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(name="Car", user=user)
    name_field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )
    speed_field = data_fixture.create_number_field(
        table=table, name="Max speed", number_negative=True
    )
    price_field = data_fixture.create_number_field(
        table=table,
        name="Price",
        number_decimal_places=2,
        number_negative=False,
    )
    model = table.get_model()

    row = RowHandler().create_row(
        user,
        table,
        values={
            name_field.id: "Tesla",
            speed_field.id: 240,
            f"field_{price_field.id}": 59999.99,
            9999: "Must not be added",
        },
    )

    assert model.objects.all().count() == 1

    action_type_registry.get_by_type(DeleteRowActionType).do(user, table, row.id)

    assert model.objects.all().count() == 0

    ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert model.objects.all().count() == 1
    assert getattr(row, f"field_{name_field.id}") == "Tesla"
    assert getattr(row, f"field_{speed_field.id}") == 240
    assert getattr(row, f"field_{price_field.id}") == 59999.99
    assert not getattr(row, "field_9999", None)

    ActionHandler.redo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert model.objects.all().count() == 0


@pytest.mark.django_db
def test_can_undo_moving_row(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(name="Car", user=user)

    handler = RowHandler()
    row_1 = handler.create_row(user=user, table=table)
    row_2 = handler.create_row(user=user, table=table)
    row_3 = handler.create_row(user=user, table=table)

    def refresh_rows_from_db():
        row_1.refresh_from_db()
        row_2.refresh_from_db()
        row_3.refresh_from_db()

    assert row_1.order == Decimal("1.00000000000000000000")
    assert row_2.order == Decimal("2.00000000000000000000")
    assert row_3.order == Decimal("3.00000000000000000000")

    # move row_1 to the end
    action_type_registry.get_by_type(MoveRowActionType).do(user, table, row_1.id)

    refresh_rows_from_db()
    assert row_1.order == Decimal("4.00000000000000000000")
    assert row_2.order == Decimal("2.00000000000000000000")
    assert row_3.order == Decimal("3.00000000000000000000")

    ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    refresh_rows_from_db()
    assert row_1.order < row_2.order < row_3.order


@pytest.mark.django_db
def test_can_undo_redo_moving_row(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(name="Car", user=user)

    handler = RowHandler()
    row_1 = handler.create_row(user=user, table=table)
    row_2 = handler.create_row(user=user, table=table)
    row_3 = handler.create_row(user=user, table=table)

    def refresh_rows_from_db():
        row_1.refresh_from_db()
        row_2.refresh_from_db()
        row_3.refresh_from_db()

    assert row_1.order == Decimal("1.00000000000000000000")
    assert row_2.order == Decimal("2.00000000000000000000")
    assert row_3.order == Decimal("3.00000000000000000000")

    # move row_1 to the end
    action_type_registry.get_by_type(MoveRowActionType).do(user, table, row_1.id)

    refresh_rows_from_db()
    assert row_1.order == Decimal("4.00000000000000000000")
    assert row_2.order == Decimal("2.00000000000000000000")
    assert row_3.order == Decimal("3.00000000000000000000")

    ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    refresh_rows_from_db()
    assert row_1.order < row_2.order < row_3.order

    ActionHandler.redo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    refresh_rows_from_db()
    assert row_2.order < row_3.order < row_1.order


@pytest.mark.django_db
def test_undo_moving_row_does_nothing_if_row_is_at_same_original_position(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(name="Car", user=user)

    handler = RowHandler()
    row_1 = handler.create_row(user=user, table=table)
    row_2 = handler.create_row(user=user, table=table)
    row_3 = handler.create_row(user=user, table=table)

    def refresh_rows_from_db():
        row_1.refresh_from_db()
        row_2.refresh_from_db()
        row_3.refresh_from_db()

    assert row_1.order == Decimal("1.00000000000000000000")
    assert row_2.order == Decimal("2.00000000000000000000")
    assert row_3.order == Decimal("3.00000000000000000000")

    # move row_1 to the end
    action_type_registry.get_by_type(MoveRowActionType).do(
        user, table, row_1.id, before=row_2
    )

    refresh_rows_from_db()
    assert row_1.order < row_2.order < row_3.order
    order = [row_1.order, row_2.order, row_3.order]

    ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    refresh_rows_from_db()
    assert order == [row_1.order, row_2.order, row_3.order]
