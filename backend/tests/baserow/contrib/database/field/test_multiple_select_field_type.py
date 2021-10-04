from datetime import date
import pytest

from io import BytesIO


from faker import Faker
from baserow.contrib.database.views.handler import ViewHandler

from baserow.core.handler import CoreHandler
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import (
    EmailField,
    NumberField,
    SelectOption,
    MultipleSelectField,
    SingleSelectField,
)
from baserow.contrib.database.fields.field_types import (
    MultipleSelectFieldType,
)
from django.apps.registry import apps
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.field_converters import (
    MultipleSelectConversionConfig,
)
from baserow.contrib.database.fields.exceptions import (
    AllProvidedMultipleSelectValuesMustBeSelectOption,
    AllProvidedMultipleSelectValuesMustBeIntegers,
)
from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
def test_call_apps_registry_pending_operations(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)

    field_handler = FieldHandler()
    field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_select",
        name="Test",
    )
    table.get_model()
    # Make sure that there are no pending operations in the app registry. Because a
    # Django ManyToManyField registers pending operations every time a table model is
    # generated, which can causes a memory leak if they are not triggered.
    assert len(apps._pending_operations) == 0


@pytest.mark.django_db
def test_multi_select_field_type(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    select_options_initial = [{"value": "Option 1", "color": "blue"}]
    field = field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_select",
        name="Multiple Select",
        select_options=select_options_initial,
    )
    field_id = f"field_{field.id}"

    assert MultipleSelectField.objects.all().first().id == field.id
    assert SelectOption.objects.all().count() == 1

    select_options = field.select_options.all()
    assert len(select_options) == 1
    assert select_options[0].order == 0
    assert select_options[0].field_id == field.id
    assert select_options[0].value == "Option 1"
    assert select_options[0].color == "blue"

    select_options = field.select_options.all()
    row = row_handler.create_row(
        user=user, table=table, values={field_id: [select_options[0].id]}
    )
    assert row.id
    row_multi_select_field_list = getattr(row, f"field_{field.id}").all()
    assert len(row_multi_select_field_list) == 1
    assert row_multi_select_field_list[0].id == select_options[0].id
    assert row_multi_select_field_list[0].value == select_options[0].value
    assert row_multi_select_field_list[0].color == select_options[0].color
    assert row_multi_select_field_list[0].field_id == select_options[0].field_id

    field_handler.update_field(
        user=user,
        field=field,
        table=table,
        select_options=[
            {"value": "Option 1", "color": "blue"},
            {"value": "Option 2", "color": "green"},
        ],
    )

    select_options = field.select_options.all()
    assert len(select_options) == 2
    assert SelectOption.objects.all().count() == 2

    row_2 = row_handler.create_row(
        user=user,
        table=table,
        values={field_id: [select_options[0].id, select_options[1].id]},
    )

    assert row_2.id
    row_multi_select_field_list = getattr(row_2, f"field_{field.id}").all()
    assert len(row_multi_select_field_list) == 2
    assert row_multi_select_field_list[0].id == select_options[0].id
    assert row_multi_select_field_list[0].value == select_options[0].value
    assert row_multi_select_field_list[0].color == select_options[0].color
    assert row_multi_select_field_list[0].field_id == select_options[0].field_id
    assert row_multi_select_field_list[1].id == select_options[1].id
    assert row_multi_select_field_list[1].value == select_options[1].value
    assert row_multi_select_field_list[1].color == select_options[1].color
    assert row_multi_select_field_list[1].field_id == select_options[1].field_id


@pytest.mark.django_db
def test_multiple_select_field_type_rows(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)
    other_select_option_single_select_field = data_fixture.create_select_option()

    field_handler = FieldHandler()
    row_handler = RowHandler()

    other_multiple_field = field_handler.create_field(
        user=user,
        table=table,
        name="Other Multiple Select",
        type_name="multiple_select",
        select_options=[
            {"value": "Option 3", "color": "blue"},
        ],
    )
    other_multiple_field_select_options = other_multiple_field.select_options.all()

    field = field_handler.create_field(
        user=user,
        table=table,
        name="Multiple Select",
        type_name="multiple_select",
        select_options=[
            {"value": "Option 1", "color": "red"},
            {"value": "Option 2", "color": "blue"},
        ],
    )

    with pytest.raises(AllProvidedMultipleSelectValuesMustBeSelectOption):
        row_handler.create_row(
            user=user, table=table, values={f"field_{field.id}": [999999]}
        )

    with pytest.raises(AllProvidedMultipleSelectValuesMustBeSelectOption):
        row_handler.create_row(
            user=user,
            table=table,
            values={f"field_{field.id}": [other_select_option_single_select_field.id]},
        )

    with pytest.raises(AllProvidedMultipleSelectValuesMustBeSelectOption):
        row_handler.create_row(
            user=user,
            table=table,
            values={f"field_{field.id}": [other_multiple_field_select_options[0].id]},
        )

    select_options = field.select_options.all()

    with pytest.raises(AllProvidedMultipleSelectValuesMustBeSelectOption):
        row = row_handler.create_row(
            user=user,
            table=table,
            values={f"field_{field.id}": [select_options[0].id, 9999]},
        )

    with pytest.raises(AllProvidedMultipleSelectValuesMustBeIntegers):
        row = row_handler.create_row(
            user=user,
            table=table,
            values={f"field_{field.id}": [select_options[0].id, "wrong_type"]},
        )

    with pytest.raises(AllProvidedMultipleSelectValuesMustBeIntegers):
        row = row_handler.create_row(
            user=user,
            table=table,
            values={f"field_{field.id}": ["wrong_type"]},
        )

    row = row_handler.create_row(
        user=user, table=table, values={f"field_{field.id}": [select_options[0].id]}
    )

    row_field = getattr(row, f"field_{field.id}").all()
    assert len(row_field) == 1
    assert row_field[0].id == select_options[0].id
    assert row_field[0].value == select_options[0].value
    assert row_field[0].color == select_options[0].color

    field = field_handler.update_field(
        user=user,
        field=field,
        select_options=[
            {"value": "Option 3", "color": "orange"},
            {"value": "Option 4", "color": "purple"},
        ],
    )

    select_options = field.select_options.all()
    assert len(select_options) == 2
    row_2 = row_handler.create_row(
        user=user, table=table, values={f"field_{field.id}": [select_options[0].id]}
    )
    row_2_field = getattr(row_2, f"field_{field.id}").all()
    assert len(row_2_field) == 1
    assert getattr(row_2_field[0], "id") == select_options[0].id
    assert getattr(row_2_field[0], "value") == select_options[0].value
    assert getattr(row_2_field[0], "color") == select_options[0].color

    row_3 = row_handler.create_row(
        user=user, table=table, values={f"field_{field.id}": [select_options[1].id]}
    )
    row_3_field = getattr(row_3, f"field_{field.id}").all()
    assert len(row_3_field) == 1
    assert getattr(row_3_field[0], "id") == select_options[1].id
    assert getattr(row_3_field[0], "value") == select_options[1].value

    row_4 = row_handler.create_row(
        user=user, table=table, values={f"field_{field.id}": [select_options[0].id]}
    )
    row_4_field = getattr(row_4, f"field_{field.id}").all()
    assert len(row_4_field) == 1
    assert getattr(row_4_field[0], "id") == select_options[0].id
    assert getattr(row_4_field[0], "value") == select_options[0].value

    row_5 = row_handler.create_row(user=user, table=table)
    row_5_field = getattr(row_5, f"field_{field.id}").all()
    assert len(row_5_field) == 0

    model = table.get_model()

    with django_assert_num_queries(3):
        rows = list(model.objects.all().enhance_by_fields())

    assert len(getattr(rows[0], f"field_{field.id}").all()) == 0
    assert getattr(rows[1], f"field_{field.id}").all()[0].id == select_options[0].id
    assert getattr(rows[2], f"field_{field.id}").all()[0].id == select_options[1].id
    assert getattr(rows[3], f"field_{field.id}").all()[0].id == select_options[0].id

    row.refresh_from_db()
    assert len(getattr(row, f"field_{field.id}").all()) == 0

    row_4 = row_handler.update_row(
        user=user, table=table, row_id=row_4.id, values={f"field_{field.id}": []}
    )
    assert len(getattr(row_4, f"field_{field.id}").all()) == 0


@pytest.mark.django_db
def test_multiple_select_field_type_sorting(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)
    grid_view = data_fixture.create_grid_view(table=table)

    field_handler = FieldHandler()
    view_handler = ViewHandler()

    field = field_handler.create_field(
        user=user,
        table=table,
        name="Multiple Select",
        type_name="multiple_select",
    )
    option_a = data_fixture.create_select_option(field=field, value="A", color="red")
    option_b = data_fixture.create_select_option(field=field, value="B", color="blue")
    option_c = data_fixture.create_select_option(field=field, value="C", color="green")

    values_1 = [option_c.id, option_a.id, option_b.id]
    values_2 = [option_b.id, option_a.id]
    values_3 = [option_a.id, option_c.id, option_b.id]
    values_4 = []
    row_1 = data_fixture.create_row_for_many_to_many_field(
        table=table, field=field, values=values_1, user=user
    )
    row_2 = data_fixture.create_row_for_many_to_many_field(
        table, field, values_2, user=user
    )
    row_3 = data_fixture.create_row_for_many_to_many_field(
        table, field, values_3, user=user
    )
    row_4 = data_fixture.create_row_for_many_to_many_field(
        table, field, values_4, user=user
    )

    sort = data_fixture.create_view_sort(view=grid_view, field=field, order="ASC")
    model = table.get_model()
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_4.id, row_3.id, row_2.id, row_1.id]
    sort.order = "DESC"
    sort.save()
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_1.id, row_2.id, row_3.id, row_4.id]

    option_a.value = "Z"
    option_a.save()
    sort.order = "ASC"
    sort.save()
    model = table.get_model()
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_4.id, row_2.id, row_1.id, row_3.id]


@pytest.mark.django_db
def test_multiple_select_field_type_deleting_select_option(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)

    field_handler = FieldHandler()

    field = field_handler.create_field(
        user=user,
        table=table,
        name="Multiple Select",
        type_name="multiple_select",
    )
    field_id = f"field_{field.id}"
    option_a = data_fixture.create_select_option(field=field, value="A", color="red")
    option_b = data_fixture.create_select_option(field=field, value="B", color="blue")
    option_c = data_fixture.create_select_option(field=field, value="C", color="green")

    select_options = field.select_options.all()
    select_option_ids_before = [x.id for x in select_options]

    assert len(select_options) == 3

    values_1 = [option_c.id, option_a.id, option_b.id]
    values_2 = [option_b.id, option_a.id]
    values_3 = [option_a.id, option_c.id, option_b.id]
    values_4 = []
    row_1 = data_fixture.create_row_for_many_to_many_field(
        table=table, field=field, values=values_1, user=user
    )
    row_2 = data_fixture.create_row_for_many_to_many_field(
        table, field, values_2, user=user
    )
    row_3 = data_fixture.create_row_for_many_to_many_field(
        table, field, values_3, user=user
    )
    row_4 = data_fixture.create_row_for_many_to_many_field(
        table, field, values_4, user=user
    )

    assert len(getattr(row_1, field_id).all()) == len(values_1)
    assert len(getattr(row_2, field_id).all()) == len(values_2)
    assert len(getattr(row_3, field_id).all()) == len(values_3)
    assert len(getattr(row_4, field_id).all()) == len(values_4)

    updated_select_options = [
        {"id": option.id, "value": option.value, "color": option.color}
        for option in select_options
        if not option.value == "A"
    ]
    field_handler.update_field_select_options(
        user=user, field=field, select_options=updated_select_options
    )
    select_options = field.select_options.all()
    select_option_ids_after = [x.id for x in select_options]
    assert len(select_options) == 2
    assert any(
        option_id in select_option_ids_after for option_id in select_option_ids_before
    )

    row_1.refresh_from_db()
    row_2.refresh_from_db()
    row_3.refresh_from_db()
    row_4.refresh_from_db()

    row_1_field = getattr(row_1, field_id).all()
    row_2_field = getattr(row_2, field_id).all()
    row_3_field = getattr(row_3, field_id).all()
    row_4_field = getattr(row_4, field_id).all()

    assert len(row_1_field) == 2
    assert any([x.id in [option_b.id, option_c.id] for x in row_1_field])

    assert len(row_2_field) == 1
    assert any([x.id in [option_b.id] for x in row_1_field])

    assert len(row_3_field) == 2
    assert any([x.id in [option_b.id, option_c.id] for x in row_1_field])

    assert len(row_4_field) == 0


@pytest.mark.django_db
def test_multi_select_enhance_queryset(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    example_table = data_fixture.create_database_table(
        name="Example", database=database
    )
    field_handler = FieldHandler()
    row_handler = RowHandler()

    multiselect_row_field = field_handler.create_field(
        user=user,
        table=example_table,
        name="Multiple Select",
        type_name="multiple_select",
        select_options=[
            {"value": "Option 1", "color": "blue"},
            {"value": "Option 2", "color": "blue"},
            {"value": "Option 3", "color": "red"},
        ],
    )
    select_options = multiselect_row_field.select_options.all()

    row_handler.create_row(
        user=user,
        table=example_table,
        values={
            f"field_{multiselect_row_field.id}": [
                select_options[0].id,
                select_options[1].id,
            ],
        },
    )

    row_handler.create_row(
        user=user,
        table=example_table,
        values={
            f"field_{multiselect_row_field.id}": [
                select_options[0].id,
            ],
        },
    )

    row_handler.create_row(
        user=user,
        table=example_table,
        values={
            f"field_{multiselect_row_field.id}": [
                select_options[0].id,
                select_options[1].id,
                select_options[2].id,
            ],
        },
    )

    model = example_table.get_model()
    rows = list(model.objects.all().enhance_by_fields())

    with django_assert_num_queries(0):
        for row in rows:
            list(getattr(row, f"field_{multiselect_row_field.id}").all())


@pytest.mark.django_db
def test_multiple_select_field_type_random_value(data_fixture):
    """
    Verify that the random_value function of the single select field type correctly
    returns one option of a given select_options list. If the select_options list is
    empty or the passed field type is not of single select field type by any chance
    it should return None.
    """

    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)
    field_handler = FieldHandler()
    cache = {}
    fake = Faker()

    field = field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_select",
        name="Multiple select",
        select_options=[
            {"value": "Option 1", "color": "blue"},
            {"value": "Option 2", "color": "red"},
            {"value": "Option 3", "color": "white"},
            {"value": "Option 4", "color": "green"},
        ],
    )

    select_options = field.select_options.all()
    random_choice = MultipleSelectFieldType().random_value(field, fake, cache)
    assert type(random_choice) is list
    assert set([x.id for x in select_options]).issuperset(set(random_choice)) is True

    random_choice = MultipleSelectFieldType().random_value(field, fake, cache)
    assert type(random_choice) is list
    assert set([x.id for x in select_options]).issuperset(set(random_choice)) is True

    email_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="email",
        name="E-Mail",
    )
    random_choice_2 = MultipleSelectFieldType().random_value(email_field, fake, cache)
    assert random_choice_2 is None


@pytest.mark.django_db
def test_import_export_multiple_select_field(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field_handler = FieldHandler()
    field = field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_select",
        name="Multi select",
        select_options=[
            {"value": "Option 1", "color": "blue"},
            {"value": "Option 2", "color": "red"},
            {"value": "Option 3", "color": "white"},
            {"value": "Option 4", "color": "green"},
        ],
    )
    select_option = field.select_options.all().first()
    field_type = field_type_registry.get_by_model(field)
    field_serialized = field_type.export_serialized(field)
    id_mapping = {}
    field_imported = field_type.import_serialized(table, field_serialized, id_mapping)

    assert field_imported.select_options.all().count() == 4
    imported_select_option = field_imported.select_options.all().first()
    assert imported_select_option.id != select_option.id
    assert imported_select_option.value == select_option.value
    assert imported_select_option.color == select_option.color
    assert imported_select_option.order == select_option.order


@pytest.mark.django_db
def test_get_set_export_serialized_value_multiple_select_field(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    imported_group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()
    core_handler = CoreHandler()

    multiselect_row_field = field_handler.create_field(
        user=user,
        table=table,
        name="Multiple Select",
        type_name="multiple_select",
        select_options=[
            {"value": "Option 1", "color": "blue"},
            {"value": "Option 2", "color": "blue"},
            {"value": "Option 3", "color": "red"},
        ],
    )
    select_options = multiselect_row_field.select_options.all()

    row_handler.create_row(
        user=user,
        table=table,
        values={},
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{multiselect_row_field.id}": [
                select_options[0].id,
                select_options[1].id,
            ],
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{multiselect_row_field.id}": [
                select_options[1].id,
                select_options[2].id,
            ],
        },
    )
    assert len(SelectOption.objects.all()) == 3

    exported_applications = core_handler.export_group_applications(group, BytesIO())
    imported_applications, id_mapping = core_handler.import_applications_to_group(
        imported_group, exported_applications, BytesIO(), None
    )
    imported_database = imported_applications[0]
    imported_table = imported_database.table_set.all()[0]
    imported_field = imported_table.field_set.all().first().specific

    assert imported_table.id != table.id
    assert imported_field.id != multiselect_row_field.id
    assert len(SelectOption.objects.all()) == 6

    imported_model = imported_table.get_model()
    all = imported_model.objects.all()
    assert len(all) == 3
    imported_row_1 = all[0]
    imported_row_1_field = getattr(imported_row_1, f"field_{imported_field.id}").all()
    imported_row_2 = all[1]
    imported_row_2_field = getattr(imported_row_2, f"field_{imported_field.id}").all()
    imported_row_3 = all[2]
    imported_row_3_field = getattr(imported_row_3, f"field_{imported_field.id}").all()

    assert len(imported_row_1_field) == 0

    assert len(imported_row_2_field) == 2
    assert imported_row_2_field[0].id != select_options[0].id
    assert imported_row_2_field[0].value == select_options[0].value
    assert imported_row_2_field[0].color == select_options[0].color
    assert imported_row_2_field[1].id != select_options[1].id
    assert imported_row_2_field[1].value == select_options[1].value
    assert imported_row_2_field[1].color == select_options[1].color

    assert len(imported_row_3_field) == 2
    assert imported_row_3_field[0].id != select_options[1].id
    assert imported_row_3_field[0].value == select_options[1].value
    assert imported_row_3_field[0].color == select_options[1].color
    assert imported_row_3_field[1].id != select_options[2].id
    assert imported_row_3_field[1].value == select_options[2].value
    assert imported_row_3_field[1].color == select_options[2].color


@pytest.mark.django_db
def test_conversion_single_select_to_multiple_select_field(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field = field_handler.create_field(
        user=user,
        table=table,
        name="Single Select",
        type_name="single_select",
        select_options=[
            {"value": "Option 1", "color": "blue"},
            {"value": "Option 2", "color": "blue"},
            {"value": "Option 3", "color": "red"},
        ],
    )

    select_options = field.select_options.all()
    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": select_options[0].id,
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": select_options[1].id,
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": select_options[2].id,
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": select_options[2].id,
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": select_options[2].id,
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": select_options[2].id,
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": None,
        },
    )

    assert SingleSelectField.objects.all().first().id == field.id

    field_handler.update_field(user=user, field=field, new_type_name="multiple_select")

    field_type = field_type_registry.get_by_model(field)
    select_options = field.select_options.all()
    model = table.get_model()
    assert field_type.type == "multiple_select"
    assert len(select_options) == 3
    assert MultipleSelectField.objects.all().first().id == field.id
    assert SingleSelectField.objects.all().count() == 0

    rows = list(model.objects.all().enhance_by_fields())
    # Check first row
    row_multi_select_field_list_0 = getattr(rows[0], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_0) == 1
    assert row_multi_select_field_list_0[0].id == select_options[0].id
    assert row_multi_select_field_list_0[0].value == select_options[0].value

    # Check second row
    row_multi_select_field_list_1 = getattr(rows[1], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_1) == 1
    assert row_multi_select_field_list_1[0].id == select_options[1].id
    assert row_multi_select_field_list_1[0].value == select_options[1].value

    # Check empty row
    row_multi_select_field_list_7 = getattr(rows[6], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_7) == 0


@pytest.mark.django_db
def test_conversion_multiple_select_to_single_select_field(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()

    field = field_handler.create_field(
        user=user,
        table=table,
        name="Multi Select",
        type_name="multiple_select",
        select_options=[
            {"value": "Option 1", "color": "blue"},
            {"value": "Option 2", "color": "blue"},
            {"value": "Option 3", "color": "red"},
        ],
    )

    select_options = field.select_options.all()
    # Row1
    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[select_options[0].id, select_options[1].id],
        user=user,
    )

    # Row2
    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[select_options[1].id, select_options[2].id],
        user=user,
    )

    # Row3
    data_fixture.create_row_for_many_to_many_field(
        table=table, field=field, values=[select_options[2].id], user=user
    )

    # Row4
    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[select_options[1].id, select_options[2].id],
        user=user,
    )

    # Row5
    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[select_options[2].id, select_options[1].id],
        user=user,
    )

    # Row6
    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[select_options[0].id, select_options[1].id, select_options[2].id],
        user=user,
    )

    assert MultipleSelectField.objects.all().first().id == field.id

    field = field_handler.update_field(
        user=user, field=field, new_type_name="single_select"
    )

    field_type = field_type_registry.get_by_model(field)
    select_options = field.select_options.all()
    model = table.get_model()
    assert field_type.type == "single_select"
    assert len(select_options) == 3
    assert SingleSelectField.objects.all().first().id == field.id
    assert MultipleSelectField.objects.all().count() == 0

    # Check first row
    rows = list(model.objects.all().enhance_by_fields())
    row_single_select_field_list_0 = getattr(rows[0], f"field_{field.id}")
    assert row_single_select_field_list_0.id == select_options[0].id
    assert row_single_select_field_list_0.value == select_options[0].value

    # Check second row
    row_single_select_field_list_1 = getattr(rows[1], f"field_{field.id}")
    assert row_single_select_field_list_1.id == select_options[1].id
    assert row_single_select_field_list_1.value == select_options[1].value

    # Check third row
    row_single_select_field_list_2 = getattr(rows[2], f"field_{field.id}")
    assert row_single_select_field_list_2.id == select_options[2].id
    assert row_single_select_field_list_2.value == select_options[2].value

    # Check fourth row
    row_single_select_field_list_3 = getattr(rows[3], f"field_{field.id}")
    assert row_single_select_field_list_3.id == select_options[1].id
    assert row_single_select_field_list_3.value == select_options[1].value

    # Check fifth row
    row_single_select_field_list_4 = getattr(rows[4], f"field_{field.id}")
    assert row_single_select_field_list_4.id == select_options[2].id
    assert row_single_select_field_list_4.value == select_options[2].value

    # Check sixth row
    row_single_select_field_list_5 = getattr(rows[5], f"field_{field.id}")
    assert row_single_select_field_list_5.id == select_options[0].id
    assert row_single_select_field_list_5.value == select_options[0].value


@pytest.mark.django_db
def test_converting_multiple_select_field_value(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    multiple_select_field = data_fixture.create_multiple_select_field(table=table)
    option_1 = data_fixture.create_select_option(
        field=multiple_select_field, value="Option 1"
    )
    option_2 = data_fixture.create_select_option(
        field=multiple_select_field, value="Option 2"
    )

    assert len(SelectOption.objects.all()) == 2

    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{multiple_select_field.id}": [option_1.id, option_2.id]},
    )

    text_field = field_handler.update_field(
        user=user, field=multiple_select_field, new_type_name="text"
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{text_field.id}": "Option 3"},
    )

    # empty row
    row_handler.create_row(
        user=user,
        table=table,
    )

    # create row with additional whitespace
    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{text_field.id}": "Option 3, "},
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{text_field.id}": "Option 3,Option 2"},
    )

    assert len(SelectOption.objects.all()) == 0
    model = table.get_model()
    rows = model.objects.all()

    assert getattr(rows[0], f"field_{text_field.id}") == ", ".join(
        [option_1.value, option_2.value]
    )

    # converting back to text field should split by comma and
    # create the necessary select_options
    multiple_select_field = field_handler.update_field(
        user=user, field=text_field, new_type_name="multiple_select"
    )
    model = table.get_model()
    rows = model.objects.all()
    assert len(SelectOption.objects.all()) == 3
    cell_1 = getattr(rows[0], f"field_{multiple_select_field.id}")
    cell_2 = getattr(rows[1], f"field_{multiple_select_field.id}")
    cell_3 = getattr(rows[2], f"field_{multiple_select_field.id}")
    cell_4 = getattr(rows[3], f"field_{multiple_select_field.id}")
    cell_5 = getattr(rows[4], f"field_{multiple_select_field.id}")
    assert len(cell_1.all()) == 2
    assert len(cell_2.all()) == 1
    assert len(cell_3.all()) == 0
    assert len(cell_4.all()) == 1
    assert len(cell_5.all()) == 2


@pytest.mark.django_db
def test_conversion_number_to_multiple_select_field(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field = field_handler.create_field(
        user=user,
        table=table,
        name="Number",
        type_name="number",
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": 1,
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": 2,
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": 3,
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": 4,
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": 5,
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": 6,
        },
    )

    assert NumberField.objects.all().first().id == field.id

    field_handler.update_field(user=user, field=field, new_type_name="multiple_select")

    field_type = field_type_registry.get_by_model(field)
    select_options = field.select_options.all()
    model = table.get_model()
    assert field_type.type == "multiple_select"
    assert len(select_options) == 6
    assert MultipleSelectField.objects.all().first().id == field.id

    rows = list(model.objects.all().enhance_by_fields())
    # Check first row
    row_multi_select_field_list_0 = getattr(rows[0], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_0) == 1
    assert row_multi_select_field_list_0[0].value == "1"

    # Check second row
    row_multi_select_field_list_1 = getattr(rows[1], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_1) == 1
    assert row_multi_select_field_list_1[0].value == "2"

    # Check third row
    row_multi_select_field_list_2 = getattr(rows[2], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_2) == 1
    assert row_multi_select_field_list_2[0].value == "3"

    # Check fourth row
    row_multi_select_field_list_3 = getattr(rows[3], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_3) == 1
    assert row_multi_select_field_list_3[0].value == "4"

    # Check fifth row
    row_multi_select_field_list_4 = getattr(rows[4], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_4) == 1
    assert row_multi_select_field_list_4[0].value == "5"

    # Check third row
    row_multi_select_field_list_5 = getattr(rows[5], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_5) == 1
    assert row_multi_select_field_list_5[0].value == "6"


@pytest.mark.django_db
def test_conversion_email_to_multiple_select_field(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field = field_handler.create_field(
        user=user,
        table=table,
        name="Email",
        type_name="email",
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": "myname1@mail.de",
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": "myname2@mail.de",
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": "myname3@mail.de",
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": "myname4@mail.de",
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": "myname5@mail.de",
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": "myname6@mail.de",
        },
    )

    assert EmailField.objects.all().first().id == field.id

    field_handler.update_field(user=user, field=field, new_type_name="multiple_select")

    field_type = field_type_registry.get_by_model(field)
    select_options = field.select_options.all()
    model = table.get_model()
    assert field_type.type == "multiple_select"
    assert len(select_options) == 6
    assert MultipleSelectField.objects.all().first().id == field.id

    rows = list(model.objects.all().enhance_by_fields())
    # Check first row
    row_multi_select_field_list_0 = getattr(rows[0], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_0) == 1
    assert row_multi_select_field_list_0[0].value == "myname1@mail.de"

    # Check second row
    row_multi_select_field_list_1 = getattr(rows[1], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_1) == 1
    assert row_multi_select_field_list_1[0].value == "myname2@mail.de"

    # Check third row
    row_multi_select_field_list_2 = getattr(rows[2], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_2) == 1
    assert row_multi_select_field_list_2[0].value == "myname3@mail.de"

    # Check fourth row
    row_multi_select_field_list_3 = getattr(rows[3], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_3) == 1
    assert row_multi_select_field_list_3[0].value == "myname4@mail.de"

    # Check fifth row
    row_multi_select_field_list_4 = getattr(rows[4], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_4) == 1
    assert row_multi_select_field_list_4[0].value == "myname5@mail.de"

    # Check sixth row
    row_multi_select_field_list_5 = getattr(rows[5], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_5) == 1
    assert row_multi_select_field_list_5[0].value == "myname6@mail.de"


@pytest.mark.django_db
def test_conversion_date_to_multiple_select_field(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()

    date_field_eu = field_handler.create_field(
        user=user, table=table, type_name="date", date_format="EU", name="date_field_eu"
    )
    date_field_us = field_handler.create_field(
        user=user, table=table, type_name="date", date_format="US", name="date_field_us"
    )
    date_field_iso = field_handler.create_field(
        user=user,
        table=table,
        type_name="date",
        date_format="ISO",
        name="date_field_iso",
    )
    date_field_eu_12 = field_handler.create_field(
        user=user,
        table=table,
        type_name="date",
        date_format="EU",
        date_include_time=True,
        date_time_format="12",
        name="date_field_eu_12",
    )
    date_field_us_12 = field_handler.create_field(
        user=user,
        table=table,
        type_name="date",
        date_format="US",
        date_include_time=True,
        date_time_format="12",
        name="date_field_us_12",
    )
    date_field_iso_12 = field_handler.create_field(
        user=user,
        table=table,
        type_name="date",
        date_format="ISO",
        date_include_time=True,
        date_time_format="12",
        name="date_field_iso_12",
    )
    date_field_eu_24 = field_handler.create_field(
        user=user,
        table=table,
        type_name="date",
        date_format="EU",
        date_include_time=True,
        date_time_format="24",
        name="date_field_eu_24",
    )
    date_field_us_24 = field_handler.create_field(
        user=user,
        table=table,
        type_name="date",
        date_format="US",
        date_include_time=True,
        date_time_format="24",
        name="date_field_us_24",
    )
    date_field_iso_24 = field_handler.create_field(
        user=user,
        table=table,
        type_name="date",
        date_format="ISO",
        date_include_time=True,
        date_time_format="24",
        name="date_field_iso_24",
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{date_field_eu.id}": "2021-08-31",
            f"field_{date_field_us.id}": "2021-08-31",
            f"field_{date_field_iso.id}": "2021-08-31",
            f"field_{date_field_eu_12.id}": "2021-08-31 11:00:00",
            f"field_{date_field_us_12.id}": "2021-08-31 11:00:00",
            f"field_{date_field_iso_12.id}": "2021-08-31 11:00:00",
            f"field_{date_field_eu_24.id}": "2021-08-31 11:00:00",
            f"field_{date_field_us_24.id}": "2021-08-31 11:00:00",
            f"field_{date_field_iso_24.id}": "2021-08-31 11:00:00",
        },
    )

    all_fields = [
        date_field_eu,
        date_field_us,
        date_field_iso,
        date_field_eu_12,
        date_field_us_12,
        date_field_iso_12,
        date_field_eu_24,
        date_field_us_24,
        date_field_iso_24,
    ]

    all_results = [
        "31/08/2021",
        "08/31/2021",
        "2021-08-31",
        "31/08/2021 11:00AM",
        "08/31/2021 11:00AM",
        "2021-08-31 11:00AM",
        "31/08/2021 11:00",
        "08/31/2021 11:00",
        "2021-08-31 11:00",
    ]

    for field in all_fields:
        field_handler.update_field(
            user=user, field=field, new_type_name="multiple_select"
        )

        field_type = field_type_registry.get_by_model(field)
        select_options = field.select_options.all()
        assert field_type.type == "multiple_select"
        assert len(select_options) == 1

    model = table.get_model()
    rows = list(model.objects.all().enhance_by_fields())

    for index, field in enumerate(all_fields):
        cell = getattr(rows[0], f"field_{field.id}").all()
        assert len(cell) == 1
        assert cell[0].value == all_results[index]

    # convert multiple_select field back into date
    # if there is another select_option added then
    # we expect to not have any value in that cell
    new_select_option = data_fixture.create_select_option(
        field=date_field_eu, value="01/09/2021", color="green"
    )
    select_options = date_field_eu.select_options.all()

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{date_field_eu.id}": [getattr(x, "id") for x in select_options],
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{date_field_eu.id}": [new_select_option.id],
        },
    )

    date_field_eu = field_handler.update_field(
        user=user,
        field=date_field_eu,
        new_type_name="date",
        date_format="EU",
        name="date_field_eu",
    )

    model = table.get_model()
    rows = list(model.objects.all().enhance_by_fields())

    field_cell_row_0 = getattr(rows[0], f"field_{date_field_eu.id}")
    field_cell_row_1 = getattr(rows[1], f"field_{date_field_eu.id}")
    field_cell_row_2 = getattr(rows[2], f"field_{date_field_eu.id}")
    assert field_cell_row_0 == date(2021, 8, 31)
    assert field_cell_row_1 == date(2021, 8, 31)
    assert field_cell_row_2 == date(2021, 9, 1)


@pytest.mark.django_db
def test_convert_long_text_to_multiple_select(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    field = field_handler.create_field(
        user=user, table=table, type_name="long_text", name="Text"
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{field.id}": "This is a description, with several, commas."},
    )

    multiple_select_field = field_handler.update_field(
        user=user, field=field, new_type_name="multiple_select"
    )

    assert len(SelectOption.objects.all()) == 3
    model = table.get_model()
    rows = model.objects.all()

    cell = getattr(rows[0], f"field_{multiple_select_field.id}").all()
    assert len(cell) == 3
    assert cell[0].value == "This is a description"
    assert cell[1].value == "with several"
    assert cell[2].value == "commas."


@pytest.mark.django_db
def test_multiple_select_with_single_select_present(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    single_select_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="single_select",
        name="Single",
        select_options=[
            {"value": "Option 1", "color": "red"},
            {"value": "Option 2", "color": "blue"},
        ],
    )

    field_handler.create_field(
        user=user, table=table, type_name="multiple_select", name="Multi"
    )

    single_options = single_select_field.select_options.all()
    first_select_option = single_options[0]

    assert type(first_select_option) == SelectOption

    row = row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{single_select_field.id}": single_options[0]},
    )

    field_cell = getattr(row, f"field_{single_select_field.id}")
    assert field_cell.id == first_select_option.id
    assert field_cell.value == first_select_option.value
    assert field_cell.color == first_select_option.color


@pytest.mark.django_db
def test_convert_multiple_select_to_text(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()

    field = field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_select",
        name="Multi",
        select_options=[
            {"value": "Option 1", "color": "blue"},
            {"value": "Option 2", "color": "orange"},
        ],
    )
    options = field.select_options.all()
    assert len(SelectOption.objects.all()) == 2

    data_fixture.create_row_for_many_to_many_field(
        table=table, field=field, user=user, values=[options[0].id, options[1].id]
    )

    data_fixture.create_row_for_many_to_many_field(
        table=table, field=field, user=user, values=[options[1].id, options[0].id]
    )

    field = field_handler.update_field(user=user, field=field, new_type_name="text")
    assert len(SelectOption.objects.all()) == 0

    model = table.get_model()
    rows = model.objects.all()
    row_1 = rows[0]
    row_2 = rows[1]

    cell_1 = getattr(row_1, f"field_{field.id}")
    cell_2 = getattr(row_2, f"field_{field.id}")
    assert cell_1 == "Option 1, Option 2"
    assert cell_2 == "Option 2, Option 1"


@pytest.mark.django_db
def test_convert_multiple_select_to_text_with_comma_and_quotes(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    field = field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_select",
        name="Multi",
        select_options=[
            {"value": "Option 1", "color": "blue"},
            {"value": "Option 2", "color": "orange"},
            {"value": "Option 3,", "color": "red"},
        ],
    )
    options = field.select_options.all()
    assert len(SelectOption.objects.all()) == 3

    data_fixture.create_row_for_many_to_many_field(
        table=table, field=field, user=user, values=[options[0].id, options[1].id]
    )

    data_fixture.create_row_for_many_to_many_field(
        table=table, field=field, user=user, values=[options[2].id, options[1].id]
    )

    data_fixture.create_row_for_many_to_many_field(
        table=table, field=field, user=user, values=[options[2].id]
    )

    field = field_handler.update_field(user=user, field=field, new_type_name="text")
    assert len(SelectOption.objects.all()) == 0

    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{field.id}": 'Option 1, "Option 3,", Option 4'},
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{field.id}": '"Option 3,"'},
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{field.id}": '"Option 3,",'},
    )

    model = table.get_model()
    rows = model.objects.all()
    row_1 = rows[0]
    row_2 = rows[1]
    row_3 = rows[2]
    row_4 = rows[3]
    row_5 = rows[4]
    row_6 = rows[5]

    cell_1 = getattr(row_1, f"field_{field.id}")
    cell_2 = getattr(row_2, f"field_{field.id}")
    cell_3 = getattr(row_3, f"field_{field.id}")
    cell_4 = getattr(row_4, f"field_{field.id}")
    cell_5 = getattr(row_5, f"field_{field.id}")
    cell_6 = getattr(row_6, f"field_{field.id}")

    assert cell_1 == "Option 1, Option 2"
    # we want to make sure that the converted select option containing a "comma"
    # is correctly quoted
    assert cell_2 == '"Option 3,", Option 2'
    assert cell_3 == '"Option 3,"'
    assert cell_4 == 'Option 1, "Option 3,", Option 4'
    assert cell_5 == '"Option 3,"'
    assert cell_6 == '"Option 3,",'

    # converting back to multiple select should create 'Option 3,' without quotes
    field = field_handler.update_field(
        user=user, field=field, new_type_name="multiple_select"
    )
    assert len(SelectOption.objects.all()) == 4

    model = table.get_model()
    rows = model.objects.all()
    row_1 = rows[0]
    row_2 = rows[1]
    row_3 = rows[2]
    row_4 = rows[3]
    row_5 = rows[4]
    row_6 = rows[5]
    cell_1 = getattr(row_1, f"field_{field.id}").all()
    cell_2 = getattr(row_2, f"field_{field.id}").all()
    cell_3 = getattr(row_3, f"field_{field.id}").all()
    cell_4 = getattr(row_4, f"field_{field.id}").all()
    cell_5 = getattr(row_5, f"field_{field.id}").all()
    cell_6 = getattr(row_6, f"field_{field.id}").all()

    assert len(cell_1) == 2
    assert cell_1[0].value == "Option 1"
    assert cell_1[1].value == "Option 2"

    assert len(cell_2) == 2
    assert cell_2[0].value == "Option 3,"
    assert cell_2[1].value == "Option 2"

    assert len(cell_3) == 1
    assert cell_3[0].value == "Option 3,"

    assert len(cell_4) == 3
    assert cell_4[0].value == "Option 1"
    assert cell_4[1].value == "Option 3,"
    assert cell_4[2].value == "Option 4"

    assert len(cell_5) == 1
    assert cell_5[0].value == "Option 3,"

    assert len(cell_6) == 1
    assert cell_6[0].value == "Option 3,"


@pytest.mark.django_db
def test_conversion_to_multiple_select_field_with_select_options(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field = field_handler.create_field(
        user=user,
        table=table,
        name="Text",
        type_name="text",
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": "Option 1",
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": "Option 2",
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": "Option 3",
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": None,
        },
    )

    field_handler.update_field(
        user=user,
        field=field,
        new_type_name="multiple_select",
        select_options=[
            {"value": "Option 1", "color": "blue"},
            {"value": "Option 3", "color": "green"},
        ],
    )

    field_type = field_type_registry.get_by_model(field)
    select_options = field.select_options.all()
    assert field_type.type == "multiple_select"
    assert len(select_options) == 2
    model = table.get_model()

    rows = list(model.objects.all().enhance_by_fields())
    # Check first row
    row_multi_select_field_list_0 = getattr(rows[0], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_0) == 1
    assert row_multi_select_field_list_0[0].value == "Option 1"

    # Check second row
    row_multi_select_field_list_1 = getattr(rows[1], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_1) == 0

    # Check third row
    row_multi_select_field_list_2 = getattr(rows[2], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_2) == 1
    assert row_multi_select_field_list_2[0].value == "Option 3"

    # Check fourth row
    row_multi_select_field_list_3 = getattr(rows[3], f"field_{field.id}").all()
    assert len(row_multi_select_field_list_3) == 0


@pytest.mark.django_db
def test_conversion_to_multiple_select_with_more_than_threshold_options_in_extraction(
    data_fixture,
):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_1 = field_handler.create_field(
        user=user,
        table=table,
        name="Text",
        type_name="long_text",
    )

    field_2 = field_handler.create_field(
        user=user,
        table=table,
        name="Text 2",
        type_name="long_text",
    )

    conversion_config = MultipleSelectConversionConfig()
    long_text_string_items = []
    for i in range(conversion_config.new_select_options_threshold):
        option_string = f"Option {i}"
        long_text_string_items.append(option_string)

    long_text_string = ",".join(long_text_string_items)

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field_1.id}": long_text_string,
            f"field_{field_2.id}": f"{long_text_string}, Option X",
        },
    )

    field_handler.update_field(
        user=user,
        field=field_1,
        new_type_name="multiple_select",
    )

    field_type = field_type_registry.get_by_model(field_1)
    select_options = field_1.select_options.all()
    assert field_type.type == "multiple_select"
    assert len(select_options) == conversion_config.new_select_options_threshold

    field_handler.update_field(
        user=user,
        field=field_2,
        new_type_name="multiple_select",
    )

    field_type = field_type_registry.get_by_model(field_2)
    select_options = field_2.select_options.all()
    assert field_type.type == "multiple_select"
    assert len(select_options) == 0

    model = table.get_model()

    rows = list(model.objects.all().enhance_by_fields())
    # Check first row
    row_multi_select_field_list_0 = getattr(rows[0], f"field_{field_2.id}").all()
    assert len(row_multi_select_field_list_0) == 0


@pytest.mark.django_db
def test_conversion_to_multiple_select_with_more_than_threshold_options_provided(
    data_fixture,
):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_1 = field_handler.create_field(
        user=user,
        table=table,
        name="Text",
        type_name="long_text",
    )

    field_2 = field_handler.create_field(
        user=user,
        table=table,
        name="Text 2",
        type_name="long_text",
    )

    conversion_config = MultipleSelectConversionConfig()
    provided_select_options = []
    for i in range(conversion_config.new_select_options_threshold):
        option = {"value": f"Option {i}", "color": "blue"}
        provided_select_options.append(option)

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field_1.id}": "Option 1",
            f"field_{field_2.id}": "Option X",
        },
    )

    field_handler.update_field(
        user=user,
        field=field_1,
        new_type_name="multiple_select",
        select_options=provided_select_options,
    )

    field_type = field_type_registry.get_by_model(field_1)
    select_options = field_1.select_options.all()
    assert field_type.type == "multiple_select"
    assert len(select_options) == conversion_config.new_select_options_threshold

    provided_select_options.append({"value": "Option X", "color": "green"})
    field_handler.update_field(
        user=user,
        field=field_2,
        new_type_name="multiple_select",
        select_options=provided_select_options,
    )

    field_type = field_type_registry.get_by_model(field_2)
    select_options = field_2.select_options.all()
    assert field_type.type == "multiple_select"
    assert len(select_options) == conversion_config.new_select_options_threshold + 1

    model = table.get_model()

    rows = list(model.objects.all().enhance_by_fields())
    # Check first row
    row_multi_select_field_1 = getattr(rows[0], f"field_{field_1.id}").all()
    row_multi_select_field_2 = getattr(rows[0], f"field_{field_2.id}").all()
    assert len(row_multi_select_field_1) == 1
    assert row_multi_select_field_1[0].value == "Option 1"
    assert len(row_multi_select_field_2) == 1
    assert row_multi_select_field_2[0].value == "Option X"


@pytest.mark.django_db
def test_conversion_to_multiple_select_with_option_value_too_large(
    data_fixture,
):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_1 = field_handler.create_field(
        user=user,
        table=table,
        name="Text",
        type_name="long_text",
    )

    conversion_config = MultipleSelectConversionConfig()

    too_long_string_for_select_option = "X" * 300
    not_too_long_string = "This is not too long."
    row_1 = row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field_1.id}": too_long_string_for_select_option,
        },
    )

    row_2 = row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field_1.id}": not_too_long_string,
        },
    )

    field_handler.update_field(
        user=user,
        field=field_1,
        new_type_name="multiple_select",
    )

    field_type = field_type_registry.get_by_model(field_1)
    select_options = field_1.select_options.all()
    assert field_type.type == "multiple_select"
    assert len(select_options) == 2

    model = table.get_model()
    rows = model.objects.all()
    row_1 = rows[0]
    row_2 = rows[1]
    cell_1 = getattr(row_1, f"field_{field_1.id}").all()
    cell_2 = getattr(row_2, f"field_{field_1.id}").all()

    assert len(cell_1) == 1
    assert len(cell_1[0].value) == conversion_config.allowed_select_options_length

    assert len(cell_2) == 1
    assert cell_2[0].value == not_too_long_string


@pytest.mark.django_db
def test_conversion_to_multiple_select_with_same_option_value_on_same_row(
    data_fixture,
):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_1 = field_handler.create_field(
        user=user,
        table=table,
        name="Text",
        type_name="long_text",
    )

    row_1 = row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field_1.id}": "test,test",
        },
    )

    row_2 = row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field_1.id}": "test, test",
        },
    )

    field_handler.update_field(
        user=user,
        field=field_1,
        new_type_name="multiple_select",
    )

    field_type = field_type_registry.get_by_model(field_1)
    select_options = field_1.select_options.all()
    id_of_only_select_option = select_options[0].id
    assert field_type.type == "multiple_select"
    assert len(select_options) == 1

    model = table.get_model()
    rows = model.objects.all()
    row_1 = rows[0]
    row_2 = rows[1]
    cell_1 = getattr(row_1, f"field_{field_1.id}").all()
    cell_2 = getattr(row_2, f"field_{field_1.id}").all()

    assert len(cell_1) == 1
    assert cell_1[0].id == id_of_only_select_option

    assert len(cell_2) == 1
    assert cell_2[0].id == id_of_only_select_option
