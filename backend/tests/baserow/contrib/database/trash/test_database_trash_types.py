from unittest.mock import patch

import pytest
from django.db import connection

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import Field, TextField, LinkRowField
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.handler import ViewHandler
from baserow.core.models import TrashEntry
from baserow.core.trash.exceptions import (
    ParentIdMustBeProvidedException,
    ParentIdMustNotBeProvidedException,
)
from baserow.core.trash.handler import TrashHandler


@pytest.mark.django_db
def test_delete_row(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(name="Car", user=user)
    data_fixture.create_text_field(table=table, name="Name", text_default="Test")

    handler = RowHandler()
    model = table.get_model()
    row = handler.create_row(user=user, table=table)
    handler.create_row(user=user, table=table)

    TrashHandler.permanently_delete(row)
    assert model.objects.all().count() == 1


@pytest.mark.django_db
def test_perm_deleting_many_rows_at_once_only_looks_up_the_model_once(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(name="Car", user=user)
    data_fixture.create_text_field(table=table, name="Name", text_default="Test")

    handler = RowHandler()
    model = table.get_model()
    row_1 = handler.create_row(user=user, table=table)

    TrashHandler.trash(
        user, table.database.group, table.database, row_1, parent_id=table.id
    )
    assert model.objects.all().count() == 0
    assert model.trash.all().count() == 1
    assert TrashEntry.objects.count() == 1

    TrashEntry.objects.update(should_be_permanently_deleted=True)

    with django_assert_num_queries(9):
        TrashHandler.permanently_delete_marked_trash()

    row_2 = handler.create_row(user=user, table=table)
    row_3 = handler.create_row(user=user, table=table)
    TrashHandler.trash(
        user, table.database.group, table.database, row_2, parent_id=table.id
    )
    TrashHandler.trash(
        user, table.database.group, table.database, row_3, parent_id=table.id
    )

    assert model.objects.all().count() == 0
    assert model.trash.all().count() == 2
    assert TrashEntry.objects.count() == 2

    TrashEntry.objects.update(should_be_permanently_deleted=True)

    # We only want five more queries when deleting 2 rows instead of 1 compared to
    # above:
    # 1. A query to lookup the extra row we are deleting
    # 2. A query to delete said row
    # 3. A query to delete it's trash entry.
    # 4. Queries to open and close transactions for each deletion
    # If we weren't caching the table models an extra number of queries would be first
    # performed to lookup the table information which breaks this assertion.
    with django_assert_num_queries(14):
        TrashHandler.permanently_delete_marked_trash()


@pytest.mark.django_db
def test_can_delete_fields_and_rows_in_the_same_perm_delete_batch(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(name="Car", user=user)
    field = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )

    handler = RowHandler()
    model = table.get_model()
    row_1 = handler.create_row(user=user, table=table)
    row_2 = handler.create_row(user=user, table=table)

    TrashHandler.trash(
        user, table.database.group, table.database, row_1, parent_id=table.id
    )
    TrashHandler.trash(user, table.database.group, table.database, field)
    TrashHandler.trash(
        user, table.database.group, table.database, row_2, parent_id=table.id
    )
    assert model.objects.all().count() == 0
    assert model.trash.all().count() == 2
    assert TrashEntry.objects.count() == 3

    TrashEntry.objects.update(should_be_permanently_deleted=True)

    TrashHandler.permanently_delete_marked_trash()

    assert model.objects.all().count() == 0
    assert model.trash.all().count() == 0
    assert TrashEntry.objects.count() == 0

    field_2 = data_fixture.create_text_field(
        table=table, name="Name", text_default="Test"
    )
    row_3 = handler.create_row(user=user, table=table)

    TrashHandler.trash(user, table.database.group, table.database, field_2)
    TrashHandler.trash(
        user, table.database.group, table.database, row_3, parent_id=table.id
    )

    assert model.objects.all().count() == 0
    assert model.trash.all().count() == 1
    assert TrashEntry.objects.count() == 2

    TrashEntry.objects.update(should_be_permanently_deleted=True)
    TrashHandler.permanently_delete_marked_trash()

    assert model.objects.all().count() == 0
    assert model.trash.all().count() == 0
    assert TrashEntry.objects.count() == 0


@pytest.mark.django_db
def test_can_trash_row_with_blank_primary_single_select(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(name="Car", user=user)
    option_field = data_fixture.create_single_select_field(
        table=table, name="option_field", order=1, primary=True
    )
    data_fixture.create_select_option(field=option_field, value="A", color="blue")
    data_fixture.create_select_option(field=option_field, value="B", color="red")

    handler = RowHandler()
    model = table.get_model()
    row = handler.create_row(user=user, table=table)

    TrashHandler.trash(
        user, table.database.group, table.database, row, parent_id=table.id
    )
    assert TrashEntry.objects.count() == 1
    assert model.objects.count() == 0
    assert model.trash.count() == 1


@pytest.mark.django_db
def test_can_trash_row_with_blank_primary_file_field(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(name="Car", user=user)
    data_fixture.create_file_field(
        table=table, name="file_field", order=1, primary=True
    )

    handler = RowHandler()
    model = table.get_model()
    row = handler.create_row(user=user, table=table)

    TrashHandler.trash(
        user, table.database.group, table.database, row, parent_id=table.id
    )
    assert TrashEntry.objects.count() == 1
    assert model.objects.count() == 0
    assert model.trash.count() == 1


@pytest.mark.django_db
def test_delete_row_perm(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(name="Car", user=user)
    data_fixture.create_text_field(table=table, name="Name", text_default="Test")

    handler = RowHandler()
    row = handler.create_row(user=user, table=table)
    handler.create_row(user=user, table=table)

    TrashHandler.trash(
        user, table.database.group, table.database, row, parent_id=table.id
    )
    model = table.get_model()
    assert model.objects.all().count() == 1
    assert model.trash.all().count() == 1

    TrashHandler.permanently_delete(row)
    assert model.objects.all().count() == 1
    assert model.trash.all().count() == 0


@pytest.mark.django_db
def test_perm_delete_table(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)

    assert Table.objects.all().count() == 1
    assert f"database_table_{table.id}" in connection.introspection.table_names()

    TrashHandler.permanently_delete(table)

    assert Table.objects.all().count() == 0
    assert f"database_table_{table.id}" not in connection.introspection.table_names()


@pytest.mark.django_db
def test_perm_delete_field(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)

    assert Field.objects.all().count() == 1
    assert TextField.objects.all().count() == 1
    TrashHandler.permanently_delete(text_field)
    assert Field.objects.all().count() == 0
    assert Field.trash.all().count() == 0
    assert TextField.objects.all().count() == 0

    table_model = table.get_model()
    field_name = f"field_{text_field.id}"
    assert field_name not in [field.name for field in table_model._meta.get_fields()]
    assert f"trashed_{field_name}" not in [
        field.name for field in table_model._meta.get_fields()
    ]


@pytest.mark.django_db
def test_perm_delete_link_row_field(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )
    cars_table = data_fixture.create_database_table(name="Cars", database=database)
    data_fixture.create_database_table(name="Unrelated")

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "John"},
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "Jane"},
    )

    # Create a primary field and some example data for the cars table.
    cars_primary_field = field_handler.create_field(
        user=user, table=cars_table, type_name="text", name="Name", primary=True
    )
    row_handler.create_row(
        user=user, table=cars_table, values={f"field_{cars_primary_field.id}": "BMW"}
    )
    row_handler.create_row(
        user=user, table=cars_table, values={f"field_{cars_primary_field.id}": "Audi"}
    )

    link_field_1 = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Customer",
        link_row_table=customers_table,
    )
    TrashHandler.permanently_delete(link_field_1)
    assert LinkRowField.objects.all().count() == 0
    for t in connection.introspection.table_names():
        if "_relation_" in t:
            assert False


@pytest.mark.django_db
def test_trashing_a_table_with_link_fields_pointing_at_it_also_trashes_those_fields(
    data_fixture,
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )
    cars_table = data_fixture.create_database_table(name="Cars", database=database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "John"},
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "Jane"},
    )

    # Create a primary field and some example data for the cars table.
    cars_primary_field = field_handler.create_field(
        user=user, table=cars_table, type_name="text", name="Name", primary=True
    )
    row_handler.create_row(
        user=user, table=cars_table, values={f"field_{cars_primary_field.id}": "BMW"}
    )
    row_handler.create_row(
        user=user, table=cars_table, values={f"field_{cars_primary_field.id}": "Audi"}
    )

    link_field_1 = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Customer",
        link_row_table=customers_table,
    )
    TrashHandler.trash(user, database.group, database, customers_table)

    link_field_1.refresh_from_db()
    assert link_field_1.trashed


@pytest.mark.django_db
def test_trashed_row_entry_includes_the_rows_primary_key_value_as_an_extra_description(
    data_fixture,
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    row = row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "John"},
    )
    trash_entry = TrashHandler.trash(
        user, database.group, database, row, parent_id=customers_table.id
    )

    assert trash_entry.extra_description == "John"
    assert trash_entry.name == str(row.id)
    assert trash_entry.parent_name == "Customers"


@pytest.mark.django_db
def test_trashed_row_entry_extra_description_is_unnamed_when_no_value_pk(
    data_fixture,
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    row = row_handler.create_row(
        user=user,
        table=customers_table,
        values={},
    )
    trash_entry = TrashHandler.trash(
        user, database.group, database, row, parent_id=customers_table.id
    )

    assert trash_entry.extra_description == f"unnamed row {row.id}"
    assert trash_entry.name == str(row.id)
    assert trash_entry.parent_name == "Customers"


@pytest.mark.django_db
def test_restoring_a_trashed_link_field_restores_the_opposing_field_also(
    data_fixture,
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(database=database)
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "John"},
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "Jane"},
    )

    link_field_1 = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Customer",
        link_row_table=customers_table,
    )
    TrashHandler.trash(user, database.group, database, link_field_1)

    assert LinkRowField.trash.count() == 2

    TrashHandler.restore_item(user, "field", link_field_1.id)

    assert LinkRowField.objects.count() == 2


@pytest.mark.django_db
def test_trashing_a_row_hides_it_from_a_link_row_field_pointing_at_it(
    data_fixture,
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )
    cars_table = data_fixture.create_database_table(name="Cars", database=database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    john_row = row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "John"},
    )
    jane_row = row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "Jane"},
    )

    link_field_1 = field_handler.create_field(
        user=user,
        table=cars_table,
        type_name="link_row",
        name="customer",
        link_row_table=customers_table,
    )
    # Create a primary field and some example data for the cars table.
    cars_primary_field = field_handler.create_field(
        user=user, table=cars_table, type_name="text", name="Name", primary=True
    )
    linked_row_pointing_at_john = row_handler.create_row(
        user=user,
        table=cars_table,
        values={
            f"field_{cars_primary_field.id}": "BMW",
            f"field_{link_field_1.id}": [john_row.id],
        },
    )
    linked_row_pointing_at_jane = row_handler.create_row(
        user=user,
        table=cars_table,
        values={
            f"field_{cars_primary_field.id}": "Audi",
            f"field_{link_field_1.id}": [jane_row.id],
        },
    )

    cars_model = cars_table.get_model(attribute_names=True)
    assert list(cars_model.objects.values_list("customer", flat=True)) == [
        john_row.id,
        jane_row.id,
    ]
    row = RowHandler().get_row(user, cars_table, linked_row_pointing_at_john.id)
    assert list(
        getattr(row, f"field_{link_field_1.id}").values_list("id", flat=True)
    ) == [john_row.id]

    TrashHandler.trash(
        user, database.group, database, john_row, parent_id=customers_table.id
    )

    row = RowHandler().get_row(user, cars_table, linked_row_pointing_at_john.id)
    assert list(getattr(row, f"field_{link_field_1.id}").all()) == []
    row = RowHandler().get_row(user, cars_table, linked_row_pointing_at_jane.id)
    assert list(
        getattr(row, f"field_{link_field_1.id}").values_list("id", flat=True)
    ) == [jane_row.id]


@pytest.mark.django_db
def test_a_trashed_linked_row_pointing_at_a_trashed_row_is_restored_correctly(
    data_fixture,
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )
    cars_table = data_fixture.create_database_table(name="Cars", database=database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    john_row = row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "John"},
    )
    jane_row = row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "Jane"},
    )

    link_field_1 = field_handler.create_field(
        user=user,
        table=cars_table,
        type_name="link_row",
        name="customer",
        link_row_table=customers_table,
    )
    # Create a primary field and some example data for the cars table.
    cars_primary_field = field_handler.create_field(
        user=user, table=cars_table, type_name="text", name="Name", primary=True
    )
    linked_row_pointing_at_john = row_handler.create_row(
        user=user,
        table=cars_table,
        values={
            f"field_{cars_primary_field.id}": "BMW",
            f"field_{link_field_1.id}": [john_row.id],
        },
    )
    row_handler.create_row(
        user=user,
        table=cars_table,
        values={
            f"field_{cars_primary_field.id}": "Audi",
            f"field_{link_field_1.id}": [jane_row.id],
        },
    )

    TrashHandler.trash(
        user,
        database.group,
        database,
        linked_row_pointing_at_john,
        parent_id=cars_table.id,
    )
    TrashHandler.trash(
        user, database.group, database, john_row, parent_id=customers_table.id
    )
    TrashHandler.restore_item(
        user, "row", linked_row_pointing_at_john.id, parent_trash_item_id=cars_table.id
    )

    row = RowHandler().get_row(user, cars_table, linked_row_pointing_at_john.id)
    assert list(getattr(row, f"field_{link_field_1.id}").all()) == []

    TrashHandler.restore_item(
        user, "row", john_row.id, parent_trash_item_id=customers_table.id
    )

    row = RowHandler().get_row(user, cars_table, linked_row_pointing_at_john.id)
    assert list(
        getattr(row, f"field_{link_field_1.id}").values_list("id", flat=True)
    ) == [john_row.id]


@pytest.mark.django_db
def test_a_parent_id_must_be_provided_when_trashing_or_restoring_a_row(
    data_fixture,
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    john_row = row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "John"},
    )

    with pytest.raises(ParentIdMustBeProvidedException):
        TrashHandler.trash(
            user,
            database.group,
            database,
            john_row,
        )

    TrashHandler.trash(
        user, database.group, database, john_row, parent_id=customers_table.id
    )

    with pytest.raises(ParentIdMustBeProvidedException):
        TrashHandler.restore_item(user, "row", john_row.id)


@pytest.mark.django_db
def test_a_parent_id_must_not_be_provided_when_trashing_or_restoring_an_app(
    data_fixture,
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    with pytest.raises(ParentIdMustNotBeProvidedException):
        TrashHandler.trash(
            user, database.group, database, database, parent_id=database.group.id
        )

    TrashHandler.trash(user, database.group, database, database)

    with pytest.raises(ParentIdMustNotBeProvidedException):
        TrashHandler.restore_item(
            user, "application", database.id, parent_trash_item_id=database.group.id
        )


@pytest.mark.django_db
def test_trashing_a_field_with_a_filter_trashes_the_filter(
    data_fixture,
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    other_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Other"
    )
    grid_view = data_fixture.create_grid_view(user=user, table=customers_table)
    data_fixture.create_view_filter(
        view=grid_view, user=user, field=other_field, value="Steve"
    )

    row_handler.create_row(
        user=user,
        table=customers_table,
        values={
            f"field_{customers_primary_field.id}": "John",
            f"field_{other_field.id}": "Test",
        },
    )

    TrashHandler.trash(
        user,
        database.group,
        database,
        other_field,
    )

    model = customers_table.get_model()
    filtered_qs = ViewHandler().apply_filters(grid_view, model.objects.all())
    assert filtered_qs.count() == 1
    TrashHandler.restore_item(
        user,
        "field",
        other_field.id,
    )

    model = customers_table.get_model()
    filtered_qs = ViewHandler().apply_filters(grid_view, model.objects.all())
    assert filtered_qs.count() == 0


@pytest.mark.django_db
def test_trashing_a_field_with_a_sort_trashes_the_sort(
    data_fixture,
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    other_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Other"
    )
    grid_view = data_fixture.create_grid_view(user=user, table=customers_table)
    data_fixture.create_view_sort(
        view=grid_view, user=user, field=other_field, order="ASC"
    )

    row_handler.create_row(
        user=user,
        table=customers_table,
        values={
            f"field_{customers_primary_field.id}": "1",
            f"field_{other_field.id}": "2",
        },
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={
            f"field_{customers_primary_field.id}": "2",
            f"field_{other_field.id}": "1",
        },
    )

    TrashHandler.trash(
        user,
        database.group,
        database,
        other_field,
    )

    model = customers_table.get_model()
    filtered_qs = ViewHandler().apply_sorting(grid_view, model.objects.all())
    assert list(
        filtered_qs.values_list(f"field_{customers_primary_field.id}", flat=True)
    ) == ["1", "2"]

    TrashHandler.restore_item(
        user,
        "field",
        other_field.id,
    )

    model = customers_table.get_model()
    filtered_qs = ViewHandler().apply_sorting(grid_view, model.objects.all())
    assert list(
        filtered_qs.values_list(f"field_{customers_primary_field.id}", flat=True)
    ) == ["2", "1"]


@pytest.mark.django_db(transaction=True)
def test_can_perm_delete_tables(
    data_fixture,
):
    patcher = patch("baserow.core.models.TrashEntry.delete")
    trash_entry_delete = patcher.start()

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(name="Car", user=user)
    data_fixture.create_text_field(table=table, name="Name", text_default="Test")

    TrashHandler.trash(user, table.database.group, table.database, table)
    assert TrashEntry.objects.count() == 1
    assert f"database_table_{table.id}" in connection.introspection.table_names()

    TrashEntry.objects.update(should_be_permanently_deleted=True)

    trash_entry_delete.side_effect = RuntimeError("Force the outer transaction to fail")
    with pytest.raises(RuntimeError):
        TrashHandler.permanently_delete_marked_trash()

    assert Table.trash.filter(id=table.id).exists()
    assert TrashEntry.objects.count() == 1
    # The transaction rolled back and restored the Table, TrashEntry and underlying
    # table
    assert f"database_table_{table.id}" in connection.introspection.table_names()

    # Now make it so the deletion will work the second time, as long as it handles
    # the actual table no longer being there.
    patcher.stop()

    TrashHandler.permanently_delete_marked_trash()

    assert not Table.trash.filter(id=table.id).exists()
    assert TrashEntry.objects.count() == 0
    assert f"database_table_{table.id}" not in connection.introspection.table_names()


@pytest.mark.django_db
def test_a_restored_field_will_have_its_name_changed_to_ensure_it_is_unique(
    data_fixture,
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(database=database, name="Table")
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "John"},
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "Jane"},
    )

    link_field_1 = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Customer",
        link_row_table=customers_table,
    )
    TrashHandler.trash(user, database.group, database, link_field_1)
    TrashHandler.trash(user, database.group, database, customers_primary_field)

    assert LinkRowField.trash.count() == 2

    clashing_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name"
    )
    another_clashing_field = field_handler.create_field(
        user=user,
        table=customers_table,
        type_name="text",
        name="Name (Restored)",
    )
    link_field_2 = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Customer",
        link_row_table=customers_table,
    )

    TrashHandler.restore_item(user, "field", link_field_1.id)
    link_field_1.refresh_from_db()

    assert LinkRowField.objects.count() == 4
    assert link_field_2.name == "Customer"
    assert link_field_1.name == "Customer (Restored)"
    assert link_field_2.link_row_related_field.name == "Table"
    assert link_field_1.link_row_related_field.name == "Table (Restored)"

    TrashHandler.restore_item(user, "field", customers_primary_field.id)
    customers_primary_field.refresh_from_db()

    assert TextField.objects.count() == 3
    assert clashing_field.name == "Name"
    assert another_clashing_field.name == "Name (Restored)"
    assert customers_primary_field.name == "Name (Restored) 2"

    # Check that a normal trash and restore when there aren't any naming conflicts will
    # return the old names.
    TrashHandler.trash(user, database.group, database, link_field_1)
    TrashHandler.restore_item(user, "field", link_field_1.id)
    link_field_1.refresh_from_db()
    assert link_field_2.name == "Customer"
    assert link_field_1.name == "Customer (Restored)"


@pytest.mark.django_db
def test_perm_delete_related_link_row_field(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "John"},
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "Jane"},
    )

    link_field_1 = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Customer",
        link_row_table=customers_table,
    )

    TrashHandler.trash(
        user, database.group, database, link_field_1.link_row_related_field
    )
    assert TrashEntry.objects.count() == 1
    link_field_1.refresh_from_db()
    assert link_field_1.trashed
    assert link_field_1.link_row_related_field.trashed

    TrashEntry.objects.update(should_be_permanently_deleted=True)
    TrashHandler.permanently_delete_marked_trash()

    assert TrashEntry.objects.count() == 0
    assert LinkRowField.objects.all().count() == 0
    for t in connection.introspection.table_names():
        if "_relation_" in t:
            assert False


@pytest.mark.django_db
def test_perm_delete_table_and_related_link_row_field(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "John"},
    )
    row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "Jane"},
    )

    link_field_1 = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Customer",
        link_row_table=customers_table,
    )

    TrashHandler.trash(user, database.group, database, table)
    TrashHandler.trash(
        user, database.group, database, link_field_1.link_row_related_field
    )

    assert TrashEntry.objects.count() == 2

    TrashEntry.objects.update(should_be_permanently_deleted=True)
    TrashHandler.permanently_delete_marked_trash()

    assert LinkRowField.objects.all().count() == 0
    for t in connection.introspection.table_names():
        if "_relation_" in t:
            assert False

    assert TrashEntry.objects.count() == 0
    assert LinkRowField.objects_and_trash.all().count() == 0
    assert Table.objects_and_trash.all().count() == 1
