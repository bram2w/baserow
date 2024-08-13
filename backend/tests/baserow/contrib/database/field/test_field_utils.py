from functools import partial

import pytest

from baserow.contrib.database.fields.utils import (
    DeferredFieldImporter,
    get_field_id_from_field_key,
)


def test_get_field_id_from_field_key_strict():
    assert get_field_id_from_field_key("not") is None
    assert get_field_id_from_field_key("field_1") == 1
    assert get_field_id_from_field_key("field_22") == 22
    assert get_field_id_from_field_key("is") is None
    assert get_field_id_from_field_key("1") == 1
    assert get_field_id_from_field_key(1) == 1
    assert get_field_id_from_field_key("f1") is None

    assert get_field_id_from_field_key("f1", False) == 1
    assert get_field_id_from_field_key("1", False) == 1
    assert get_field_id_from_field_key(1, False) == 1
    assert get_field_id_from_field_key("field_1", False) == 1
    assert get_field_id_from_field_key("field1", False) == 1


@pytest.mark.django_db
def test_deferred_field_import_in_the_same_table(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    deferred_field_importer = DeferredFieldImporter()

    imported_fields = []

    def import_field_callback(field_name):
        imported_fields.append(field_name)

    dependencies = [
        ("f1", {("text", None)}),
        ("f2", {("f1", None), ("text", None)}),
        ("text", set()),
        ("f4", {("f3", None), ("f2", None)}),
        ("f3", {("f2", None)}),
    ]

    for field_name, field_deps in dependencies:
        deferred_field_importer.add_deferred_field_import(
            table, field_name, field_deps, partial(import_field_callback, field_name)
        )

    deferred_field_importer.run_deferred_field_imports({table.id: {}})

    assert imported_fields == ["f1", "f2", "f3", "f4"]


@pytest.mark.django_db
def test_deferred_field_import_in_different_tables(data_fixture):
    user = data_fixture.create_user()
    table_a, table_b, link_a_to_b = data_fixture.create_two_linked_tables(user=user)
    link_b_to_a = link_a_to_b.link_row_related_field

    deferred_field_importer = DeferredFieldImporter()

    imported_fields = []

    def import_field_callback(field_name):
        imported_fields.append(field_name)

    table_a_deps = [
        ("fa1b", {("fb2", link_a_to_b.name)}),
        ("fa1", {("text", None)}),
        ("fa2", {("fa1", None), ("text", None)}),
        ("text", set()),
        ("fa4", {("fa3", None), ("fa2", None)}),
        ("fa3", {("fa2", None)}),
        ("fa2b", {("fa1b", None), ("text_b", link_a_to_b.name)}),
    ]

    table_b_deps = [
        ("text_b", set()),
        ("fb1", {("text_b", None)}),
        ("fb2", {("fb1", None), ("text_b", None)}),
        ("fb3a", {("fa2", link_b_to_a.name)}),
        ("fb4", {("fb3", None), ("fb2", None)}),
    ]

    for field_name, field_deps in table_a_deps:
        deferred_field_importer.add_deferred_field_import(
            table_a, field_name, field_deps, partial(import_field_callback, field_name)
        )

    for field_name, field_deps in table_b_deps:
        deferred_field_importer.add_deferred_field_import(
            table_b, field_name, field_deps, partial(import_field_callback, field_name)
        )

    deferred_field_importer.run_deferred_field_imports(
        {
            table_a.id: {link_a_to_b.name: link_a_to_b},
            table_b.id: {link_b_to_a.name: link_b_to_a},
        }
    )

    assert imported_fields == [
        "fa1",
        "fb1",
        "fa2",
        "fb2",
        "fa3",
        "fb3a",
        "fa1b",
        "fb4",
        "fa4",
        "fa2b",
    ]
