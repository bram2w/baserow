from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.conf import settings
from django.db import models
from faker import Faker

from baserow.contrib.database.fields.exceptions import (
    FieldTypeDoesNotExist,
    PrimaryFieldAlreadyExists,
    CannotDeletePrimaryField,
    FieldDoesNotExist,
    IncompatiblePrimaryFieldTypeError,
    CannotChangeFieldType,
    MaxFieldLimitExceeded,
)
from baserow.contrib.database.fields.field_helpers import (
    construct_all_possible_field_kwargs,
)
from baserow.contrib.database.fields.field_types import TextFieldType, LongTextFieldType
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import (
    Field,
    TextField,
    NumberField,
    BooleanField,
    SelectOption,
    LongTextField,
)
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.handler import RowHandler
from baserow.core.exceptions import UserNotInGroup


# You must add --runslow to pytest to run this test, you can do this in intellij by
# editing the run config for this test and adding --runslow to additional args.
@pytest.mark.django_db
@pytest.mark.slow
def test_can_convert_between_all_fields(data_fixture):
    """
    A nuclear option test turned off by default to help verify changes made to
    field conversions work in every possible conversion scenario. This test checks
    is possible to convert from every possible field to every other possible field
    including converting to themselves. It only checks that the conversion does not
    raise any exceptions.
    """

    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database, user=user)
    link_table = data_fixture.create_database_table(database=database, user=user)
    handler = FieldHandler()
    row_handler = RowHandler()
    fake = Faker()

    model = table.get_model()
    cache = {}
    # Make a blank row to test empty field conversion also.
    model.objects.create(**{})
    second_row_with_values = model.objects.create(**{})

    # Some baserow field types have multiple different 'modes' which result in
    # different conversion behaviour or entirely different database columns being
    # created. Here the kwargs which control these modes are enumerated so we can then
    # generate every possible type of conversion.
    all_possible_kwargs_per_type = construct_all_possible_field_kwargs(link_table)

    i = 1
    for field_type_name, all_possible_kwargs in all_possible_kwargs_per_type.items():
        for kwargs in all_possible_kwargs:
            for inner_field_type_name in field_type_registry.get_types():
                for inner_kwargs in all_possible_kwargs_per_type[inner_field_type_name]:
                    field_type = field_type_registry.get(field_type_name)
                    field_name = f"field_{i}"
                    from_field = handler.create_field(
                        user=user,
                        table=table,
                        type_name=field_type_name,
                        name=field_name,
                        **kwargs,
                    )
                    random_value = field_type.random_value(from_field, fake, cache)
                    if isinstance(random_value, date):
                        # Faker produces subtypes of date / datetime which baserow
                        # does not want, instead just convert to str.
                        random_value = str(random_value)
                    row_handler.update_row(
                        user=user,
                        table=table,
                        row_id=second_row_with_values.id,
                        values={f"field_{from_field.id}": random_value},
                    )
                    handler.update_field(
                        user=user,
                        field=from_field,
                        new_type_name=inner_field_type_name,
                        **inner_kwargs,
                    )
                    i = i + 1


@pytest.mark.django_db
def test_get_field(data_fixture):
    user = data_fixture.create_user()
    data_fixture.create_user()
    text = data_fixture.create_text_field(user=user)

    handler = FieldHandler()

    with pytest.raises(FieldDoesNotExist):
        handler.get_field(field_id=99999)

    field = handler.get_field(field_id=text.id)

    assert text.id == field.id
    assert text.name == field.name
    assert isinstance(field, Field)

    field = handler.get_field(field_id=text.id, field_model=TextField)

    assert text.id == field.id
    assert text.name == field.name
    assert isinstance(field, TextField)

    # If the error is raised we know for sure that the query has resolved.
    with pytest.raises(AttributeError):
        handler.get_field(
            field_id=text.id, base_queryset=Field.objects.prefetch_related("UNKNOWN")
        )


@pytest.mark.django_db
@patch("baserow.contrib.database.fields.signals.field_created.send")
def test_create_field(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    handler = FieldHandler()
    field = handler.create_field(
        user=user,
        table=table,
        type_name="text",
        name="Test text field",
        text_default="Some default",
    )

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["field"].id == field.id
    assert send_mock.call_args[1]["user"].id == user.id

    assert Field.objects.all().count() == 1
    assert TextField.objects.all().count() == 1

    text_field = TextField.objects.all().first()
    assert text_field.name == "Test text field"
    assert text_field.order == 1
    assert text_field.table == table
    assert text_field.text_default == "Some default"
    assert not text_field.primary

    table_model = table.get_model()
    field_name = f"field_{text_field.id}"
    assert field_name in [field.name for field in table_model._meta.get_fields()]

    instance = table_model.objects.create(**{field_name: "Test 1"})
    assert getattr(instance, field_name) == "Test 1"

    instance_2 = table_model.objects.create()
    assert getattr(instance_2, field_name) == "Some default"

    with pytest.raises(ValueError):
        handler.create_field(
            user=user,
            table=table,
            type_name="number",
            name="Test number field",
            number_type="NOT_EXISTING",
        )

    with pytest.raises(ValueError):
        handler.create_field(
            user=user,
            table=table,
            type_name="number",
            name="Test number field",
            number_type="DECIMAL",
            number_decimal_places=9999,
        )

    handler.create_field(
        user=user,
        table=table,
        type_name="number",
        name="Test number field",
        number_type="INTEGER",
        number_decimal_places=2,
        number_negative=True,
    )

    number_field = NumberField.objects.all().first()
    assert number_field.name == "Test number field"
    assert number_field.order == 2
    assert number_field.table == table
    assert number_field.number_type == "INTEGER"
    assert number_field.number_decimal_places == 2
    assert number_field.number_negative

    handler.create_field(
        user=user,
        table=table,
        type_name="boolean",
        name="Test boolean field",
        random_other_field="WILL_BE_IGNORED",
    )

    boolean_field = BooleanField.objects.all().first()
    assert boolean_field.name == "Test boolean field"
    assert boolean_field.order == 3
    assert boolean_field.table == table

    assert Field.objects.all().count() == 3
    assert TextField.objects.all().count() == 1
    assert NumberField.objects.all().count() == 1
    assert BooleanField.objects.all().count() == 1

    field_limit = settings.MAX_FIELD_LIMIT
    settings.MAX_FIELD_LIMIT = 2

    with pytest.raises(MaxFieldLimitExceeded):
        handler.create_field(
            user=user,
            table=table,
            type_name="text",
            name="Test text field",
            text_default="Some default",
        )

    settings.MAX_FIELD_LIMIT = field_limit

    with pytest.raises(UserNotInGroup):
        handler.create_field(user=user_2, table=table, type_name="text")

    with pytest.raises(FieldTypeDoesNotExist):
        handler.create_field(user=user, table=table, type_name="UNKNOWN")


@pytest.mark.django_db
def test_create_primary_field(data_fixture):
    user = data_fixture.create_user()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table_1, primary=True)

    with pytest.raises(PrimaryFieldAlreadyExists):
        handler = FieldHandler()
        handler.create_field(user=user, table=table_1, type_name="text", primary=True)

    handler = FieldHandler()
    field = handler.create_field(
        user=user, table=table_2, type_name="text", primary=True
    )

    assert field.primary

    with pytest.raises(PrimaryFieldAlreadyExists):
        handler.create_field(user=user, table=table_2, type_name="text", primary=True)

    # Should be able to create a regular field when there is already a primary field.
    handler.create_field(user=user, table=table_2, type_name="text", primary=False)


@pytest.mark.django_db
@patch("baserow.contrib.database.fields.signals.field_updated.send")
def test_update_field(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table, order=0)
    field = data_fixture.create_text_field(table=table, order=1)

    handler = FieldHandler()

    with pytest.raises(UserNotInGroup):
        handler.update_field(user=user_2, field=field)

    with pytest.raises(ValueError):
        handler.update_field(user=user, field=object())

    with pytest.raises(FieldTypeDoesNotExist):
        handler.update_field(user=user, field=field, new_type_name="NOT_EXISTING")

    # The link row field is not compatible with a primary field so an exception
    # is expected.
    field.primary = True
    field.save()
    with pytest.raises(IncompatiblePrimaryFieldTypeError):
        handler.update_field(user=user, field=field, new_type_name="link_row")
    field.primary = False
    field.save()

    # Change some values of the text field and test if they have been changed.
    field = handler.update_field(
        user=user, field=field, name="Text field", text_default="Default value"
    )

    assert field.name == "Text field"
    assert field.text_default == "Default value"
    assert isinstance(field, TextField)

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["field"].id == field.id
    assert send_mock.call_args[1]["user"].id == user.id

    # Insert some rows to the table which should be converted later.
    model = table.get_model()
    model.objects.create(**{f"field_{field.id}": "Text value"})
    model.objects.create(**{f"field_{field.id}": "100.22"})
    model.objects.create(**{f"field_{field.id}": "10"})

    # Change the field type to a number and test if the values have been changed.
    field = handler.update_field(
        user=user,
        field=field,
        new_type_name="number",
        name="Number field",
        number_type="INTEGER",
        number_negative=False,
    )

    assert field.name == "Number field"
    assert field.number_type == "INTEGER"
    assert field.number_negative is False
    assert not hasattr(field, "text_default")

    model = table.get_model()
    rows = model.objects.all()
    assert getattr(rows[0], f"field_{field.id}") is None
    assert getattr(rows[1], f"field_{field.id}") == 100
    assert getattr(rows[2], f"field_{field.id}") == 10

    # Change the field type to a decimal and test if the values have been changed.
    field = handler.update_field(
        user=user,
        field=field,
        new_type_name="number",
        name="Price field",
        number_type="DECIMAL",
        number_decimal_places=2,
        number_negative=True,
    )

    assert field.name == "Price field"
    assert field.number_type == "DECIMAL"
    assert field.number_decimal_places == 2
    assert field.number_negative is True

    model = table.get_model()
    rows = model.objects.all()
    assert getattr(rows[0], f"field_{field.id}") is None
    assert getattr(rows[1], f"field_{field.id}") == Decimal("100.00")
    assert getattr(rows[2], f"field_{field.id}") == Decimal("10.00")

    # Change the field type to a boolean and test if the values have been changed.
    field = handler.update_field(
        user=user, field=field, new_type_name="boolean", name="Active"
    )

    field.refresh_from_db()
    assert field.name == "Active"
    assert not hasattr(field, "number_type")
    assert not hasattr(field, "number_decimal_places")
    assert not hasattr(field, "number_negative")

    model = table.get_model()
    rows = model.objects.all()
    assert getattr(rows[0], f"field_{field.id}") is False
    assert getattr(rows[1], f"field_{field.id}") is False
    assert getattr(rows[2], f"field_{field.id}") is False


@pytest.mark.django_db
def test_update_field_failing(data_fixture):
    # This failing field type triggers the CannotChangeFieldType error if a field is
    # changed into this type.
    class FailingFieldType(TextFieldType):
        def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
            return "p_in::NOT_VALID_SQL_SO_IT_WILL_FAIL("

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_number_field(table=table, order=1)

    handler = FieldHandler()

    with patch.dict(field_type_registry.registry, {"text": FailingFieldType()}):
        with pytest.raises(CannotChangeFieldType):
            handler.update_field(user=user, field=field, new_type_name="text")

    handler.update_field(user, field=field, new_type_name="text")
    assert Field.objects.all().count() == 1
    assert TextField.objects.all().count() == 1


@pytest.mark.django_db
def test_update_field_when_underlying_sql_type_doesnt_change(data_fixture):
    class AlwaysLowercaseTextField(TextFieldType):
        type = "lowercase_text"
        model_class = LongTextField

        def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
            return """p_in = (lower(p_in));"""

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    existing_text_field = data_fixture.create_text_field(table=table, order=1)

    model = table.get_model()

    field_name = f"field_{existing_text_field.id}"
    row = model.objects.create(
        **{
            field_name: "Test",
        }
    )

    handler = FieldHandler()

    with patch.dict(
        field_type_registry.registry, {"lowercase_text": AlwaysLowercaseTextField()}
    ):
        handler.update_field(
            user=user, field=existing_text_field, new_type_name="lowercase_text"
        )

        row.refresh_from_db()
        assert getattr(row, field_name) == "test"
        assert Field.objects.all().count() == 1
        assert TextField.objects.all().count() == 0
        assert LongTextField.objects.all().count() == 1


@pytest.mark.django_db
def test_field_which_changes_its_underlying_type_will_have_alter_sql_run(data_fixture):
    class ReversingTextFieldUsingBothVarCharAndTextSqlTypes(TextFieldType):
        def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
            return """p_in = (reverse(p_in));"""

        def get_model_field(self, instance, **kwargs):
            kwargs["null"] = True
            kwargs["blank"] = True
            if instance.text_default == "use_other_sql_type":
                return models.TextField(**kwargs)
            else:
                return models.CharField(**kwargs)

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    existing_text_field = data_fixture.create_text_field(table=table, order=1)

    model = table.get_model()

    field_name = f"field_{existing_text_field.id}"
    row = model.objects.create(
        **{
            field_name: "Test",
        }
    )

    handler = FieldHandler()

    with patch.dict(
        field_type_registry.registry,
        {"text": ReversingTextFieldUsingBothVarCharAndTextSqlTypes()},
    ):
        # Update to the same baserow type, but due to this fields implementation of
        # get_model_field this will alter the underlying database column from type
        # of varchar to text, which should make our reversing alter sql run.
        handler.update_field(
            user=user,
            field=existing_text_field,
            new_type_name="text",
            text_default="use_other_sql_type",
        )

        row.refresh_from_db()
        assert getattr(row, field_name) == "tseT"
        assert Field.objects.all().count() == 1
        assert TextField.objects.all().count() == 1


@pytest.mark.django_db
def test_just_changing_a_fields_name_will_not_run_alter_sql(data_fixture):
    class AlwaysReverseOnUpdateField(TextFieldType):
        def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
            return """p_in = (reverse(p_in));"""

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    existing_text_field = data_fixture.create_text_field(table=table, order=1)

    model = table.get_model()

    field_name = f"field_{existing_text_field.id}"
    row = model.objects.create(
        **{
            field_name: "Test",
        }
    )

    handler = FieldHandler()

    with patch.dict(
        field_type_registry.registry, {"text": AlwaysReverseOnUpdateField()}
    ):
        handler.update_field(
            user=user, field=existing_text_field, new_type_name="text", name="new_name"
        )

        row.refresh_from_db()
        # The field has not been reversed as just the name changed!
        assert getattr(row, field_name) == "Test"
        assert Field.objects.all().count() == 1
        assert TextField.objects.all().count() == 1


@pytest.mark.django_db
def test_when_field_type_forces_same_type_alter_fields_alter_sql_is_run(data_fixture):
    class SameTypeAlwaysReverseOnUpdateField(TextFieldType):
        def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
            return """p_in = (reverse(p_in));"""

        def force_same_type_alter_column(self, from_field, to_field):
            return True

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    existing_text_field = data_fixture.create_text_field(table=table, order=1)

    model = table.get_model()

    field_name = f"field_{existing_text_field.id}"
    row = model.objects.create(
        **{
            field_name: "Test",
        }
    )

    handler = FieldHandler()

    with patch.dict(
        field_type_registry.registry, {"text": SameTypeAlwaysReverseOnUpdateField()}
    ):
        handler.update_field(
            user=user, field=existing_text_field, new_type_name="text", name="new_name"
        )

        row.refresh_from_db()
        # The alter sql has been run due to the force override
        assert getattr(row, field_name) == "tseT"
        assert Field.objects.all().count() == 1
        assert TextField.objects.all().count() == 1


@pytest.mark.django_db
def test_update_field_with_type_error_on_conversion_should_null_field(data_fixture):
    class AlwaysThrowsSqlExceptionOnConversionField(TextFieldType):
        type = "throws_field"
        model_class = LongTextField

        def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
            return """p_in = (lower(p_in::numeric::text));"""

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    existing_text_field = data_fixture.create_text_field(table=table, order=1)

    model = table.get_model()

    field_name = f"field_{existing_text_field.id}"
    row = model.objects.create(
        **{
            field_name: "Test",
        }
    )

    handler = FieldHandler()

    with patch.dict(
        field_type_registry.registry,
        {"throws_field": AlwaysThrowsSqlExceptionOnConversionField()},
    ):
        handler.update_field(
            user=user, field=existing_text_field, new_type_name="throws_field"
        )

        row.refresh_from_db()
        assert getattr(row, field_name) is None
        assert Field.objects.all().count() == 1
        assert TextField.objects.all().count() == 0
        assert LongTextField.objects.all().count() == 1


@pytest.mark.django_db
def test_update_field_when_underlying_sql_type_doesnt_change_with_vars(data_fixture):
    class ReversesWhenConvertsAwayTextField(LongTextFieldType):
        type = "reserves_text"
        model_class = LongTextField

        def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
            return """p_in = concat(reverse(p_in), %(some_variable)s);""", {
                "some_variable": "_POST_FIX"
            }

    class AlwaysLowercaseTextField(TextFieldType):
        type = "lowercase_text"
        model_class = LongTextField

        def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
            return """p_in = concat(%(other_variable)s, lower(p_in));""", {
                "other_variable": "pre_fix_"
            }

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    existing_field_with_old_value_prep = data_fixture.create_long_text_field(
        table=table
    )

    model = table.get_model()

    field_name = f"field_{existing_field_with_old_value_prep.id}"
    row = model.objects.create(
        **{
            field_name: "Test",
        }
    )

    handler = FieldHandler()

    with patch.dict(
        field_type_registry.registry,
        {
            "lowercase_text": AlwaysLowercaseTextField(),
            "long_text": ReversesWhenConvertsAwayTextField(),
        },
    ):
        handler.update_field(
            user=user,
            field=existing_field_with_old_value_prep,
            new_type_name="lowercase_text",
        )

        row.refresh_from_db()
        assert getattr(row, field_name) == "pre_fix_tset_post_fix"
        assert Field.objects.all().count() == 1
        assert TextField.objects.all().count() == 0
        assert LongTextField.objects.all().count() == 1


@pytest.mark.django_db
def test_update_field_when_underlying_sql_type_doesnt_change_old_prep(data_fixture):
    class ReversesWhenConvertsAwayTextField(LongTextFieldType):
        type = "reserves_text"
        model_class = LongTextField

        def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
            return """p_in = (reverse(p_in));"""

    class AlwaysLowercaseTextField(TextFieldType):
        type = "lowercase_text"
        model_class = LongTextField

        def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
            return """p_in = (lower(p_in));"""

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    existing_field_with_old_value_prep = data_fixture.create_long_text_field(
        table=table
    )

    model = table.get_model()

    field_name = f"field_{existing_field_with_old_value_prep.id}"
    row = model.objects.create(
        **{
            field_name: "Test",
        }
    )

    handler = FieldHandler()

    with patch.dict(
        field_type_registry.registry,
        {
            "lowercase_text": AlwaysLowercaseTextField(),
            "long_text": ReversesWhenConvertsAwayTextField(),
        },
    ):
        handler.update_field(
            user=user,
            field=existing_field_with_old_value_prep,
            new_type_name="lowercase_text",
        )

        row.refresh_from_db()
        assert getattr(row, field_name) == "tset"
        assert Field.objects.all().count() == 1
        assert TextField.objects.all().count() == 0
        assert LongTextField.objects.all().count() == 1


@pytest.mark.django_db
@patch("baserow.contrib.database.fields.signals.field_deleted.send")
def test_delete_field(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)

    handler = FieldHandler()

    with pytest.raises(UserNotInGroup):
        handler.delete_field(user=user_2, field=text_field)

    with pytest.raises(ValueError):
        handler.delete_field(user=user_2, field=object())

    assert Field.objects.all().count() == 1
    assert TextField.objects.all().count() == 1
    field_id = text_field.id
    handler.delete_field(user=user, field=text_field)
    assert Field.objects.all().count() == 0
    assert TextField.objects.all().count() == 0

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["field_id"] == field_id
    assert send_mock.call_args[1]["field"].id == field_id
    assert send_mock.call_args[1]["user"].id == user.id

    table_model = table.get_model()
    field_name = f"field_{text_field.id}"
    assert field_name not in [field.name for field in table_model._meta.get_fields()]

    primary = data_fixture.create_text_field(table=table, primary=True)
    with pytest.raises(CannotDeletePrimaryField):
        handler.delete_field(user=user, field=primary)


@pytest.mark.django_db
def test_update_select_options(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_single_select_field(table=table)
    field_2 = data_fixture.create_single_select_field(table=table)
    data_fixture.create_text_field(table=table)

    handler = FieldHandler()

    with pytest.raises(UserNotInGroup):
        handler.update_field_select_options(field=field, user=user_2, select_options=[])

    handler.update_field_select_options(
        field=field,
        user=user,
        select_options=[
            {"value": "Option 1", "color": "blue"},
            {"value": "Option 2", "color": "red"},
        ],
    )

    assert SelectOption.objects.all().count() == 2
    select_options = field.select_options.all()
    assert len(select_options) == 2

    assert select_options[0].order == 0
    assert select_options[0].value == "Option 1"
    assert select_options[0].color == "blue"
    assert select_options[0].field_id == field.id

    assert select_options[1].order == 1
    assert select_options[1].value == "Option 2"
    assert select_options[1].color == "red"
    assert select_options[1].field_id == field.id

    handler.update_field_select_options(
        field=field,
        user=user,
        select_options=[
            {"id": select_options[0].id, "value": "Option 1 A", "color": "blue 2"},
            {"id": select_options[1].id, "value": "Option 2 A", "color": "red 2"},
        ],
    )

    assert SelectOption.objects.all().count() == 2
    select_options_2 = field.select_options.all()
    assert len(select_options_2) == 2

    assert select_options_2[0].id == select_options[0].id
    assert select_options_2[0].order == 0
    assert select_options_2[0].value == "Option 1 A"
    assert select_options_2[0].color == "blue 2"
    assert select_options_2[0].field_id == field.id

    assert select_options_2[1].id == select_options[1].id
    assert select_options_2[1].order == 1
    assert select_options_2[1].value == "Option 2 A"
    assert select_options_2[1].color == "red 2"
    assert select_options_2[1].field_id == field.id

    handler.update_field_select_options(
        field=field,
        user=user,
        select_options=[
            {"id": select_options[1].id, "value": "Option 1 B", "color": "red"},
            {"value": "Option 2 B", "color": "green"},
        ],
    )

    assert SelectOption.objects.all().count() == 2
    select_options_3 = field.select_options.all()
    assert len(select_options_3) == 2

    assert select_options_3[0].id == select_options[1].id
    assert select_options_3[0].order == 0
    assert select_options_3[0].value == "Option 1 B"
    assert select_options_3[0].color == "red"
    assert select_options_3[0].field_id == field.id

    assert select_options_3[1].order == 1
    assert select_options_3[1].value == "Option 2 B"
    assert select_options_3[1].color == "green"
    assert select_options_3[1].field_id == field.id

    handler.update_field_select_options(
        field=field_2,
        user=user,
        select_options=[
            {"id": select_options[1].id, "value": "Option 1 B", "color": "red"},
        ],
    )

    assert SelectOption.objects.all().count() == 3
    select_options_4 = field_2.select_options.all()
    assert len(select_options_4) == 1

    assert select_options_4[0].id != select_options[1].id
    assert select_options_4[0].order == 0
    assert select_options_4[0].value == "Option 1 B"
    assert select_options_4[0].color == "red"
    assert select_options_4[0].field_id == field_2.id

    handler.update_field_select_options(field=field_2, user=user, select_options=[])

    assert SelectOption.objects.all().count() == 2
    assert field_2.select_options.all().count() == 0
