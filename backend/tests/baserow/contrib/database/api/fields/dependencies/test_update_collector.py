from unittest.mock import patch

import pytest
from django.db.models import Value

from baserow.contrib.database.fields.dependencies.update_collector import (
    CachingFieldUpdateCollector,
)
from baserow.contrib.database.fields.handler import FieldHandler


@pytest.mark.django_db
def test_can_add_fields_with_update_statements_in_same_starting_table(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    model = field.table.get_model(attribute_names=True)
    row = model.objects.create(field="starting value")

    update_collector = CachingFieldUpdateCollector(field.table)
    update_collector.add_field_with_pending_update_statement(field, Value("other"))
    updated_fields = (
        update_collector.apply_updates_returning_updated_fields_in_start_table()
    )

    assert updated_fields == [field]
    row.refresh_from_db()
    assert row.field == "other"


@pytest.mark.django_db
def test_can_add_fields_in_same_starting_table_with_row_filter(
    api_client, data_fixture, django_assert_num_queries
):
    field = data_fixture.create_text_field(name="field")
    model = field.table.get_model(attribute_names=True)
    row_a = model.objects.create(field="a")
    row_b = model.objects.create(field="b")

    update_collector = CachingFieldUpdateCollector(
        field.table, starting_row_id=row_a.id
    )
    update_collector.add_field_with_pending_update_statement(field, Value("other"))
    updated_fields = (
        update_collector.apply_updates_returning_updated_fields_in_start_table()
    )

    assert updated_fields == [field]
    row_a.refresh_from_db()
    row_b.refresh_from_db()
    assert row_a.field == "other"
    assert row_b.field == "b"


@pytest.mark.django_db
@patch("baserow.contrib.database.fields.signals.field_updated.send")
def test_can_only_trigger_update_for_rows_joined_to_a_starting_row_across_a_m2m(
    send_mock, api_client, data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    first_table = data_fixture.create_database_table(database=database)
    second_table = data_fixture.create_database_table(database=database)
    first_table_primary_field = data_fixture.create_text_field(
        name="primary", primary=True, table=first_table
    )
    data_fixture.create_text_field(name="primary", primary=True, table=second_table)
    link_row_field = FieldHandler().create_field(
        user=user,
        table=first_table,
        type_name="link_row",
        link_row_table=second_table,
        name="link",
    )
    first_table_model = first_table.get_model(attribute_names=True)
    second_table_model = second_table.get_model(attribute_names=True)

    second_table_a_row = second_table_model.objects.create(primary="a")
    second_table_b_row = second_table_model.objects.create(primary="b")

    first_table_1_row = first_table_model.objects.create(primary="1")
    first_table_2_row = first_table_model.objects.create(primary="2")

    first_table_1_row.link.add(second_table_a_row.id)
    first_table_1_row.link.add(second_table_b_row.id)
    first_table_1_row.save()

    first_table_2_row.link.add(second_table_b_row.id)
    first_table_2_row.save()

    update_collector = CachingFieldUpdateCollector(
        second_table, starting_row_id=second_table_a_row.id
    )
    update_collector.add_field_with_pending_update_statement(
        first_table_primary_field,
        Value("other"),
        via_path_to_starting_table=[link_row_field],
    )
    # Cache the models so we are only asserting about the update queries
    update_collector.cache_model(first_table.get_model())
    update_collector.cache_model(second_table.get_model())
    # Only one field was updated so only one update statement is expected
    with django_assert_num_queries(1):
        updated_fields = (
            update_collector.apply_updates_returning_updated_fields_in_start_table()
        )

    # No field in the starting table (second_table) was updated
    assert updated_fields == []
    first_table_1_row.refresh_from_db()
    first_table_2_row.refresh_from_db()
    assert first_table_1_row.primary == "other"
    assert first_table_2_row.primary == "2"

    send_mock.assert_not_called()
    update_collector.send_additional_field_updated_signals()
    send_mock.assert_called_once()
    assert send_mock.call_args[1]["field"].id == first_table_primary_field.id
    assert send_mock.call_args[1]["user"] is None
    assert send_mock.call_args[1]["related_fields"] == []


@pytest.mark.django_db
@patch("baserow.contrib.database.fields.signals.field_updated.send")
def test_can_trigger_update_for_rows_joined_to_a_starting_row_across_a_m2m_and_back(
    send_mock, api_client, data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    first_table = data_fixture.create_database_table(database=database)
    second_table = data_fixture.create_database_table(database=database)
    first_table_primary_field = data_fixture.create_text_field(
        name="primary", primary=True, table=first_table
    )
    second_table_primary_field = data_fixture.create_text_field(
        name="primary", primary=True, table=second_table
    )
    link_row_field = FieldHandler().create_field(
        user=user,
        table=first_table,
        type_name="link_row",
        link_row_table=second_table,
        name="link",
    )
    first_table_model = first_table.get_model(attribute_names=True)
    second_table_model = second_table.get_model(attribute_names=True)

    second_table_a_row = second_table_model.objects.create(primary="a")
    second_table_b_row = second_table_model.objects.create(primary="b")
    second_table_unlinked_row = second_table_model.objects.create(primary="unlinked")

    first_table_1_row = first_table_model.objects.create(primary="1")
    first_table_2_row = first_table_model.objects.create(primary="2")

    first_table_1_row.link.add(second_table_a_row.id)
    first_table_1_row.link.add(second_table_b_row.id)
    first_table_1_row.save()

    first_table_2_row.link.add(second_table_b_row.id)
    first_table_2_row.save()

    update_collector = CachingFieldUpdateCollector(
        second_table, starting_row_id=second_table_a_row.id
    )
    update_collector.add_field_with_pending_update_statement(
        first_table_primary_field,
        Value("other"),
        via_path_to_starting_table=[link_row_field],
    )
    update_collector.add_field_with_pending_update_statement(
        second_table_primary_field,
        Value("other"),
        via_path_to_starting_table=[
            link_row_field,
            link_row_field.link_row_related_field,
        ],
    )
    # Cache the models so we are only asserting about the update queries
    update_collector.cache_model(first_table.get_model())
    update_collector.cache_model(second_table.get_model())
    # Two fields were updated with an update statement for each table
    with django_assert_num_queries(2):
        updated_fields = (
            update_collector.apply_updates_returning_updated_fields_in_start_table()
        )

    assert updated_fields == [second_table_primary_field]
    first_table_1_row.refresh_from_db()
    first_table_2_row.refresh_from_db()
    second_table_a_row.refresh_from_db()
    second_table_b_row.refresh_from_db()
    second_table_unlinked_row.refresh_from_db()
    assert first_table_1_row.primary == "other"
    assert first_table_2_row.primary == "2"
    assert second_table_a_row.primary == "other"
    assert second_table_b_row.primary == "other"
    assert second_table_unlinked_row.primary == "unlinked"

    send_mock.assert_not_called()
    update_collector.send_additional_field_updated_signals()
    send_mock.assert_called_once()
    assert send_mock.call_args[1]["field"].id == first_table_primary_field.id
    assert send_mock.call_args[1]["user"] is None
    assert send_mock.call_args[1]["related_fields"] == []


@pytest.mark.django_db
@patch("baserow.contrib.database.fields.signals.field_updated.send")
def test_update_statements_at_the_same_path_node_are_grouped_into_one(
    send_mock, api_client, data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    first_table = data_fixture.create_database_table(database=database)
    second_table = data_fixture.create_database_table(database=database)
    first_table_primary_field = data_fixture.create_text_field(
        name="primary", primary=True, table=first_table
    )
    first_table_other_field = data_fixture.create_text_field(
        name="other", table=first_table
    )
    second_table_primary_field = data_fixture.create_text_field(
        name="primary", primary=True, table=second_table
    )
    link_row_field = FieldHandler().create_field(
        user=user,
        table=first_table,
        type_name="link_row",
        link_row_table=second_table,
        name="link",
    )
    first_table_model = first_table.get_model(attribute_names=True)
    second_table_model = second_table.get_model(attribute_names=True)

    second_table_a_row = second_table_model.objects.create(primary="a")
    second_table_b_row = second_table_model.objects.create(primary="b")
    second_table_unlinked_row = second_table_model.objects.create(primary="unlinked")

    first_table_1_row = first_table_model.objects.create(primary="1", other="x")
    first_table_2_row = first_table_model.objects.create(primary="2", other="y")

    first_table_1_row.link.add(second_table_a_row.id)
    first_table_1_row.link.add(second_table_b_row.id)
    first_table_1_row.save()

    first_table_2_row.link.add(second_table_b_row.id)
    first_table_2_row.save()

    update_collector = CachingFieldUpdateCollector(
        second_table, starting_row_id=second_table_a_row.id
    )
    update_collector.add_field_with_pending_update_statement(
        first_table_primary_field,
        Value("other"),
        via_path_to_starting_table=[link_row_field],
    )
    update_collector.add_field_with_pending_update_statement(
        first_table_other_field,
        Value("updated"),
        via_path_to_starting_table=[link_row_field],
    )
    update_collector.add_field_with_pending_update_statement(
        second_table_primary_field,
        Value("other"),
        via_path_to_starting_table=[
            link_row_field,
            link_row_field.link_row_related_field,
        ],
    )
    # Cache the models so we are only asserting about the update queries
    update_collector.cache_model(first_table.get_model())
    update_collector.cache_model(second_table.get_model())
    # Three fields were updated but two are in the same path node (same table) and so
    # only one update per table expected
    with django_assert_num_queries(2):
        updated_fields = (
            update_collector.apply_updates_returning_updated_fields_in_start_table()
        )

    assert updated_fields == [second_table_primary_field]
    first_table_1_row.refresh_from_db()
    first_table_2_row.refresh_from_db()
    second_table_a_row.refresh_from_db()
    second_table_b_row.refresh_from_db()
    second_table_unlinked_row.refresh_from_db()
    assert first_table_1_row.primary == "other"
    assert first_table_1_row.other == "updated"
    assert first_table_2_row.primary == "2"
    assert first_table_2_row.other == "y"
    assert second_table_a_row.primary == "other"
    assert second_table_b_row.primary == "other"
    assert second_table_unlinked_row.primary == "unlinked"

    send_mock.assert_not_called()
    update_collector.send_additional_field_updated_signals()
    send_mock.assert_called_once()
    assert send_mock.call_args[1]["field"].id == first_table_primary_field.id
    assert send_mock.call_args[1]["user"] is None
    assert send_mock.call_args[1]["related_fields"] == [first_table_other_field]
