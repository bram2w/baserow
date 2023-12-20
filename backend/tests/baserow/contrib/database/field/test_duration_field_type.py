from datetime import timedelta

import pytest

from baserow.contrib.database.fields.actions import UpdateFieldActionType
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import DurationField
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.views.handler import ViewHandler
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid


@pytest.mark.field_duration
@pytest.mark.django_db
def test_create_duration_field(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    duration_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="duration",
        name="duration",
    )

    assert duration_field.pk is not None
    assert duration_field.duration_format == "h:mm"  # default format


@pytest.mark.field_duration
@pytest.mark.django_db
def test_create_duration_field_row(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    duration_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="duration",
        name="duration",
    )

    row_handler = RowHandler()
    model = table.get_model()
    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{duration_field.id}": timedelta(seconds=3660)},
        model=model,
    )
    model = table.get_model()
    rows = list(model.objects.all())

    assert len(rows) == 1
    assert getattr(rows[0], f"field_{duration_field.id}") == timedelta(seconds=3660)


@pytest.mark.field_duration
@pytest.mark.django_db
def test_create_duration_field_rows(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    duration_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="duration",
        name="duration",
    )

    row_handler = RowHandler()
    model = table.get_model()
    rows = row_handler.create_rows(
        user=user,
        table=table,
        rows_values=[
            {f"field_{duration_field.id}": timedelta(seconds=3660)},
            {f"field_{duration_field.id}": timedelta(seconds=3661)},
        ],
        model=model,
    )

    assert len(rows) == 2
    assert getattr(rows[0], f"field_{duration_field.id}") == timedelta(seconds=3660)
    assert getattr(rows[1], f"field_{duration_field.id}") == timedelta(seconds=3661)


@pytest.mark.field_duration
@pytest.mark.django_db
def test_update_duration_field_row(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    duration_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="duration",
        name="duration",
    )

    row_handler = RowHandler()
    model = table.get_model()

    row_1 = model.objects.create(
        **{f"field_{duration_field.id}": timedelta(seconds=3660)}
    )

    assert getattr(row_1, f"field_{duration_field.id}") == timedelta(seconds=3660)

    updated_row = row_handler.update_row(
        user=user,
        table=table,
        row=row_1,
        values={f"field_{duration_field.id}": timedelta(seconds=3661)},
        model=model,
    )

    assert getattr(updated_row, f"field_{duration_field.id}") == timedelta(seconds=3661)


@pytest.mark.field_duration
@pytest.mark.django_db
def test_update_duration_field_rows(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    duration_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="duration",
        name="duration",
    )

    row_handler = RowHandler()
    model = table.get_model()

    row_1 = model.objects.create(
        **{f"field_{duration_field.id}": timedelta(seconds=3660)}
    )
    row_2 = model.objects.create(
        **{f"field_{duration_field.id}": timedelta(seconds=7200)}
    )

    assert getattr(row_1, f"field_{duration_field.id}") == timedelta(seconds=3660)
    assert getattr(row_2, f"field_{duration_field.id}") == timedelta(seconds=7200)

    row_handler.update_rows(
        user=user,
        table=table,
        rows_values=[
            {"id": row_1.id, f"field_{duration_field.id}": timedelta(seconds=3661)},
            {"id": row_2.id, f"field_{duration_field.id}": timedelta(seconds=7201)},
        ],
        model=model,
    )
    row_1.refresh_from_db()
    row_2.refresh_from_db()
    assert getattr(row_1, f"field_{duration_field.id}") == timedelta(seconds=3661)
    assert getattr(row_2, f"field_{duration_field.id}") == timedelta(seconds=7201)


@pytest.mark.field_duration
@pytest.mark.django_db
def test_remove_duration_field(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    duration_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="duration",
        name="duration",
    )

    assert duration_field.pk is not None

    field_handler.delete_field(user=user, field=duration_field)

    assert DurationField.objects.count() == 0


@pytest.mark.parametrize(
    "user_input,duration_format,new_text_field_value",
    [
        (timedelta(seconds=3660), "h:mm", "1:01"),
        (timedelta(seconds=3665), "h:mm:ss", "1:01:05"),
        (timedelta(seconds=3665.5), "h:mm:ss.s", "1:01:05.5"),
        (timedelta(seconds=3665.55), "h:mm:ss.ss", "1:01:05.55"),
        (timedelta(seconds=3665.555), "h:mm:ss.sss", "1:01:05.555"),
    ],
)
@pytest.mark.django_db
@pytest.mark.field_duration
def test_convert_duration_field_to_text_field(
    data_fixture, user_input, duration_format, new_text_field_value
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_duration_field(
        user=user, table=table, duration_format=duration_format
    )
    row_handler = RowHandler()

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": user_input,
        },
    )

    FieldHandler().update_field(
        user=user,
        field=field,
        new_type_name="text",
    )

    model = table.get_model()

    row_1 = model.objects.first()
    updated_value = getattr(row_1, f"field_{field.id}")
    assert updated_value == new_text_field_value


@pytest.mark.parametrize(
    "duration_format,text_field_value,new_duration_field_value",
    [
        (
            "h:mm",
            "1:01",
            timedelta(seconds=3660),
        ),
        (
            "h:mm:ss",
            "1:01:05",
            timedelta(seconds=3665),
        ),
        (
            "h:mm:ss.s",
            "1:01:05.5",
            timedelta(seconds=3665.5),
        ),
        (
            "h:mm:ss.ss",
            "1:01:05.55",
            timedelta(seconds=3665.55),
        ),
        (
            "h:mm:ss.sss",
            "1:01:05.555",
            timedelta(seconds=3665.555),
        ),
    ],
)
@pytest.mark.django_db
@pytest.mark.field_duration
def test_convert_text_field_to_duration_field(
    data_fixture,
    duration_format,
    text_field_value,
    new_duration_field_value,
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
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
            f"field_{field.id}": text_field_value,
        },
    )

    field_handler.update_field(
        user=user,
        field=field,
        new_type_name="duration",
        duration_format=duration_format,
    )

    model = table.get_model()
    table_models = model.objects.all()
    assert table_models.count() == 1

    row_1 = table_models.first()
    updated_value = getattr(row_1, f"field_{field.id}")

    assert updated_value == new_duration_field_value


@pytest.mark.django_db
@pytest.mark.field_duration
@pytest.mark.parametrize(
    "expected,field_kwargs",
    [
        ([0, 0, 60, 120, 120], {"duration_format": "h:mm"}),
        ([1, 10, 51, 100, 122], {"duration_format": "h:mm:ss"}),
        ([1.2, 10.1, 50.7, 100.1, 122], {"duration_format": "h:mm:ss.s"}),
        ([1.20, 10.11, 50.68, 100.1, 122], {"duration_format": "h:mm:ss.ss"}),
        ([1.199, 10.11, 50.679, 100.1, 122], {"duration_format": "h:mm:ss.sss"}),
    ],
)
def test_alter_duration_format(expected, field_kwargs, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_duration_field(
        user=user, table=table, duration_format="h:mm:ss.sss"
    )

    original_values = [1.199, 10.11, 50.6789, 100.1, 122]

    RowHandler().create_rows(
        user,
        table,
        [{field.db_column: value} for value in original_values],
    )

    # Change the format and test if the values have been changed.
    handler = FieldHandler()
    field = handler.update_field(user=user, field=field, **field_kwargs)

    model = table.get_model()
    rows = model.objects.all()
    for index, row in enumerate(rows):
        assert getattr(row, f"field_{field.id}").total_seconds() == expected[index]


@pytest.mark.django_db
@pytest.mark.field_duration
@pytest.mark.undo_redo
@pytest.mark.parametrize(
    "expected,field_kwargs",
    [
        ([0, 0, 60, 120, 120], {"duration_format": "h:mm"}),
        ([1, 10, 51, 100, 122], {"duration_format": "h:mm:ss"}),
        ([1.2, 10.1, 50.7, 100.1, 122], {"duration_format": "h:mm:ss.s"}),
        ([1.20, 10.11, 50.68, 100.1, 122], {"duration_format": "h:mm:ss.ss"}),
        ([1.199, 10.11, 50.679, 100.1, 122], {"duration_format": "h:mm:ss.sss"}),
    ],
)
def test_alter_duration_format_can_be_undone(expected, field_kwargs, data_fixture):
    session_id = "session"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_duration_field(
        user=user, table=table, duration_format="h:mm:ss.sss"
    )

    original_values = [1.199, 10.11, 50.679, 100.1, 122]

    RowHandler().create_rows(
        user,
        table,
        [{field.db_column: value} for value in original_values],
    )

    # Change the format and test if the values have been changed.
    action_type_registry.get_by_type(UpdateFieldActionType).do(
        user, field, **field_kwargs
    )

    model = table.get_model()
    rows = model.objects.all()
    for index, row in enumerate(rows):
        assert getattr(row, f"field_{field.id}").total_seconds() == expected[index]

    actions = ActionHandler.undo(
        user, [UpdateFieldActionType.scope(table.id)], session_id
    )
    assert_undo_redo_actions_are_valid(actions, [UpdateFieldActionType])
    rows = model.objects.all()
    for index, row in enumerate(rows):
        assert (
            getattr(row, f"field_{field.id}").total_seconds() == original_values[index]
        )


@pytest.mark.field_duration
@pytest.mark.django_db
def test_duration_field_view_filters(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_duration_field(
        table=table, duration_format="h:mm:ss.sss"
    )

    model = table.get_model()
    rows = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {field.db_column: None},
            {field.db_column: "0:1.123"},
            {field.db_column: 1.123},
            {field.db_column: 60},  # 1min
            {field.db_column: "24:0:0"},  # 1day
            {field.db_column: 86400},  # 1day
            {field.db_column: 3601},  # 1hour 1sec
            {field.db_column: "1:0:0"},  # 1 hour
        ],
        model=model,
    )

    #
    view = data_fixture.create_grid_view(table=table)
    view_filter = data_fixture.create_view_filter(
        view=view, field=field, type="equal", value="0:0:1.123"
    )

    qs = ViewHandler().get_queryset(view, model=model)
    assert list(qs.values_list("id", flat=True)) == [rows[1].id, rows[2].id]

    view_filter.value = "1.123"  # it will be considered as a number of seconds
    view_filter.save(update_fields=["value"])

    qs = ViewHandler().get_queryset(view, model=model)
    assert list(qs.values_list("id", flat=True)) == [rows[1].id, rows[2].id]

    view_filter.type = "not_equal"
    view_filter.save(update_fields=["type"])

    qs = ViewHandler().get_queryset(view, model=model)
    assert list(qs.values_list("id", flat=True)) == [
        rows[0].id,
        rows[3].id,
        rows[4].id,
        rows[5].id,
        rows[6].id,
        rows[7].id,
    ]

    view_filter.type = "empty"
    view_filter.save(update_fields=["type"])

    qs = ViewHandler().get_queryset(view, model=model)
    assert list(qs.values_list("id", flat=True)) == [rows[0].id]

    view_filter.type = "not_empty"
    view_filter.save(update_fields=["type"])

    qs = ViewHandler().get_queryset(view, model=model)
    assert list(qs.values_list("id", flat=True)) == [
        rows[1].id,
        rows[2].id,
        rows[3].id,
        rows[4].id,
        rows[5].id,
        rows[6].id,
        rows[7].id,
    ]

    view_filter.type = "higher_than"
    view_filter.value = "3600"  # 1 hour
    view_filter.save()

    qs = ViewHandler().get_queryset(view, model=model)
    assert list(qs.values_list("id", flat=True)) == [
        rows[4].id,
        rows[5].id,
        rows[6].id,
    ]

    view_filter.type = "higher_than"
    view_filter.value = "1:00:00"
    view_filter.save()

    qs = ViewHandler().get_queryset(view, model=model)
    assert list(qs.values_list("id", flat=True)) == [
        rows[4].id,
        rows[5].id,
        rows[6].id,
    ]

    view_filter.type = "lower_than"
    view_filter.save(update_fields=["type"])

    qs = ViewHandler().get_queryset(view, model=model)
    assert list(qs.values_list("id", flat=True)) == [
        rows[1].id,
        rows[2].id,
        rows[3].id,
    ]


@pytest.mark.field_duration
@pytest.mark.django_db
def test_duration_field_view_aggregations(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_duration_field(table=table, duration_format="h:mm:ss")

    RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {field.db_column: 1},
            {field.db_column: 60},
            {field.db_column: 60},
            {field.db_column: "1:0:0"},
            {field.db_column: None},
        ],
    )

    view = data_fixture.create_grid_view(table=table)

    result = ViewHandler().get_field_aggregations(user, view, [(field, "max")])
    assert result[field.db_column] == timedelta(seconds=3600)

    result = ViewHandler().get_field_aggregations(user, view, [(field, "min")])
    assert result[field.db_column] == timedelta(seconds=1)

    result = ViewHandler().get_field_aggregations(user, view, [(field, "sum")])
    assert result[field.db_column] == timedelta(seconds=3721)

    result = ViewHandler().get_field_aggregations(user, view, [(field, "empty_count")])
    assert result[field.db_column] == 1

    result = ViewHandler().get_field_aggregations(user, view, [(field, "unique_count")])
    assert result[field.db_column] == 3
