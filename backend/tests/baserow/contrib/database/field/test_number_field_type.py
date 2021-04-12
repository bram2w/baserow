import pytest

from decimal import Decimal

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.registries import field_type_registry


@pytest.mark.django_db
@pytest.mark.parametrize(
    "expected,field_kwargs",
    [
        (
            [
                9223372036854775807,
                100,
                100,
                101,
                0,
                0,
                0,
                0,
                None,
                None,
                None,
                None,
                None,
            ],
            {"number_type": "INTEGER", "number_negative": False},
        ),
        (
            [
                9223372036854775807,
                100,
                100,
                101,
                -9223372036854775808,
                -100,
                -100,
                -101,
                None,
                None,
                None,
                None,
                None,
            ],
            {"number_type": "INTEGER", "number_negative": True},
        ),
        (
            [
                Decimal("9223372036854775807.0"),
                Decimal("100.0"),
                Decimal("100.2"),
                Decimal("100.6"),
                Decimal("0.0"),
                Decimal("0.0"),
                Decimal("0.0"),
                Decimal("0.0"),
                None,
                None,
                None,
                None,
                None,
            ],
            {
                "number_type": "DECIMAL",
                "number_negative": False,
                "number_decimal_places": 1,
            },
        ),
        (
            [
                Decimal("9223372036854775807.000"),
                Decimal("100.000"),
                Decimal("100.220"),
                Decimal("100.600"),
                Decimal("-9223372036854775808.0"),
                Decimal("-100.0"),
                Decimal("-100.220"),
                Decimal("-100.600"),
                None,
                None,
                None,
                None,
                None,
            ],
            {
                "number_type": "DECIMAL",
                "number_negative": True,
                "number_decimal_places": 3,
            },
        ),
    ],
)
def test_alter_number_field_column_type(expected, field_kwargs, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table, order=1)

    handler = FieldHandler()
    field = handler.update_field(user=user, field=field, name="Text field")

    model = table.get_model()
    model.objects.create(**{f"field_{field.id}": "9223372036854775807"})
    model.objects.create(**{f"field_{field.id}": "100"})
    model.objects.create(**{f"field_{field.id}": "100.22"})
    model.objects.create(**{f"field_{field.id}": "100.59999"})
    model.objects.create(**{f"field_{field.id}": "-9223372036854775808"})
    model.objects.create(**{f"field_{field.id}": "-100"})
    model.objects.create(**{f"field_{field.id}": "-100.22"})
    model.objects.create(**{f"field_{field.id}": "-100.5999"})
    model.objects.create(**{f"field_{field.id}": "100.59.99"})
    model.objects.create(**{f"field_{field.id}": "-100.59.99"})
    model.objects.create(**{f"field_{field.id}": "100TEST100.10"})
    model.objects.create(**{f"field_{field.id}": "!@#$%%^^&&^^%$$"})
    model.objects.create(**{f"field_{field.id}": "!@#$%%^^5.2&&^^%$$"})

    # Change the field type to a number and test if the values have been changed.
    field = handler.update_field(
        user=user, field=field, new_type_name="number", **field_kwargs
    )

    model = table.get_model()
    rows = model.objects.all()
    for index, row in enumerate(rows):
        assert getattr(row, f"field_{field.id}") == expected[index]


@pytest.mark.django_db
def test_alter_number_field_column_type_negative(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    number_field = data_fixture.create_number_field(
        table=table, order=1, number_negative=True
    )
    decimal_field = data_fixture.create_number_field(
        table=table,
        order=2,
        number_type="DECIMAL",
        number_negative=True,
        number_decimal_places=2,
    )

    model = table.get_model()
    model.objects.create(
        **{
            f"field_{number_field.id}": -10,
            f"field_{decimal_field.id}": Decimal("-10.10"),
        }
    )

    handler = FieldHandler()
    number_field = handler.update_field(
        user=user, field=number_field, number_negative=False
    )
    decimal_field = handler.update_field(
        user=user, field=decimal_field, number_negative=False
    )

    model = table.get_model()
    rows = model.objects.all()
    assert getattr(rows[0], f"field_{number_field.id}") == 0
    assert getattr(rows[0], f"field_{decimal_field.id}") == 0.00


@pytest.mark.django_db
def test_import_export_number_field(data_fixture):
    number_field = data_fixture.create_number_field(
        name="Number field",
        number_type="DECIMAL",
        number_negative=True,
        number_decimal_places=2,
    )
    number_field_type = field_type_registry.get_by_model(number_field)
    number_serialized = number_field_type.export_serialized(number_field)
    number_field_imported = number_field_type.import_serialized(
        number_field.table, number_serialized, {}
    )
    assert number_field.number_type == number_field_imported.number_type
    assert number_field.number_negative == number_field_imported.number_negative
    assert number_field.number_decimal_places == (
        number_field_imported.number_decimal_places
    )
