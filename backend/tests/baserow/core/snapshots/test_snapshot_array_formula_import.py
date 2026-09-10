import pytest

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler
from baserow.core.snapshots.handler import SnapshotHandler
from baserow.core.utils import Progress


@pytest.mark.django_db(transaction=True)
def test_snapshot_with_explicit_array_primary_dependency(data_fixture):
    """
    When the formula explicitly references the linked table's primary via
    lookup('LinkField', 'PrimaryField'), the dependency graph is complete
    and the snapshot import produces correct values.
    """

    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    parent_table = data_fixture.create_database_table(
        database=database, name="Parents", order=0
    )
    child_table = data_fixture.create_database_table(
        database=database, name="Children", order=1
    )
    detail_table = data_fixture.create_database_table(
        database=database, name="Details", order=2
    )
    data_fixture.create_text_field(table=parent_table, name="Name", primary=True)
    child_primary = data_fixture.create_text_field(
        table=child_table, name="ChildId", primary=True
    )
    detail_name = data_fixture.create_text_field(
        table=detail_table, name="Label", primary=True
    )
    is_active = data_fixture.create_boolean_field(table=child_table, name="IsActive")

    fh = FieldHandler()
    parent_link = fh.create_field(
        user,
        parent_table,
        "link_row",
        name="LinkedChildren",
        link_row_table=child_table,
    )
    detail_link = fh.create_field(
        user, child_table, "link_row", name="Detail", link_row_table=detail_table
    )
    child_primary = fh.update_field(
        user,
        child_primary,
        new_type_name="formula",
        formula="concat('ID-', field('Detail'))",
    )

    consumer = fh.create_field(
        user,
        parent_table,
        "formula",
        name="ActiveChildren",
        formula=(
            "filter(lookup('LinkedChildren', 'ChildId'), "
            "lookup('LinkedChildren', 'IsActive'))"
        ),
    )
    assert child_primary.formula_type == "array"
    assert "array_agg_unnesting" in consumer.internal_formula

    rh = RowHandler()
    detail_row = rh.create_row(user, detail_table, values={detail_name.db_column: "D1"})
    child_row = rh.create_row(
        user,
        child_table,
        values={is_active.db_column: True, detail_link.db_column: [detail_row.id]},
    )
    rh.create_row(user, parent_table, values={parent_link.db_column: [child_row.id]})

    expected = list(
        parent_table.get_model().objects.values_list(consumer.db_column, flat=True)
    )
    assert expected[0] and expected[0][0]["value"] == "ID-D1"

    snapshot = data_fixture.create_snapshot(
        snapshot_from_application=database, created_by=user
    )
    SnapshotHandler().perform_create(snapshot, Progress(total=100))
    snapshot.refresh_from_db()

    imported_parent = snapshot.snapshot_to_application.specific.table_set.get(
        name="Parents"
    )
    imported_consumer = imported_parent.field_set.get(name="ActiveChildren")
    actual = list(
        imported_parent.get_model().objects.values_list(
            imported_consumer.db_column, flat=True
        )
    )
    assert actual == expected


@pytest.mark.django_db(transaction=True)
def test_snapshot_with_implicit_array_primary_dependency(data_fixture):
    """
    When the formula uses field('LinkField') (implicit primary reference),
    the import-time dependency graph must still resolve the linked table's
    primary so recalculation order is correct and values are preserved.
    Previously this crashed with DataError because the consumer formula ran
    before the producer's column was populated.
    """

    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    parent_table = data_fixture.create_database_table(
        database=database, name="Parents", order=0
    )
    child_table = data_fixture.create_database_table(
        database=database, name="Children", order=1
    )
    detail_table = data_fixture.create_database_table(
        database=database, name="Details", order=2
    )
    data_fixture.create_text_field(table=parent_table, name="Name", primary=True)
    child_primary = data_fixture.create_text_field(
        table=child_table, name="ChildId", primary=True
    )
    detail_name = data_fixture.create_text_field(
        table=detail_table, name="Label", primary=True
    )
    is_active = data_fixture.create_boolean_field(table=child_table, name="IsActive")

    fh = FieldHandler()
    parent_link = fh.create_field(
        user,
        parent_table,
        "link_row",
        name="LinkedChildren",
        link_row_table=child_table,
    )
    detail_link = fh.create_field(
        user, child_table, "link_row", name="Detail", link_row_table=detail_table
    )
    child_primary = fh.update_field(
        user,
        child_primary,
        new_type_name="formula",
        formula="concat('ID-', field('Detail'))",
    )

    consumer = fh.create_field(
        user,
        parent_table,
        "formula",
        name="ActiveChildren",
        formula=(
            "filter(field('LinkedChildren'), lookup('LinkedChildren', 'IsActive'))"
        ),
    )
    assert child_primary.formula_type == "array"
    assert "array_agg_unnesting" in consumer.internal_formula

    rh = RowHandler()
    detail_row = rh.create_row(user, detail_table, values={detail_name.db_column: "D1"})
    child_row = rh.create_row(
        user,
        child_table,
        values={is_active.db_column: True, detail_link.db_column: [detail_row.id]},
    )
    rh.create_row(user, parent_table, values={parent_link.db_column: [child_row.id]})

    expected = list(
        parent_table.get_model().objects.values_list(consumer.db_column, flat=True)
    )
    assert expected[0] and expected[0][0]["value"] == "ID-D1"

    snapshot = data_fixture.create_snapshot(
        snapshot_from_application=database, created_by=user
    )
    SnapshotHandler().perform_create(snapshot, Progress(total=100))
    snapshot.refresh_from_db()

    imported_parent = snapshot.snapshot_to_application.specific.table_set.get(
        name="Parents"
    )
    imported_consumer = imported_parent.field_set.get(name="ActiveChildren")
    actual = list(
        imported_parent.get_model().objects.values_list(
            imported_consumer.db_column, flat=True
        )
    )
    assert actual == expected
