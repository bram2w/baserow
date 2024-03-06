import pytest

from baserow.contrib.database.fields.exceptions import RichTextFieldCannotBePrimaryField
from baserow.contrib.database.fields.handler import FieldHandler


@pytest.mark.django_db
@pytest.mark.field_long_text
def test_rich_text_field_cannot_be_primary(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)

    with pytest.raises(RichTextFieldCannotBePrimaryField):
        FieldHandler().create_field(
            user=user,
            table=table,
            type_name="long_text",
            name="Primary",
            primary=True,
            long_text_enable_rich_text=True,
        )

    # A non rich text field can be used as primary field
    primary_field = FieldHandler().create_field(
        user=user, table=table, type_name="long_text", name="Primary", primary=True
    )

    with pytest.raises(RichTextFieldCannotBePrimaryField):
        FieldHandler().update_field(
            user=user,
            field=primary_field,
            new_type_name="long_text",
            long_text_enable_rich_text=True,
        )
