from django.shortcuts import reverse

import pytest

from baserow.contrib.database.fields.handler import FieldHandler


@pytest.mark.django_db
@pytest.mark.field_link_row
@pytest.mark.api_rows
def test_get_rows_with_lookup_url(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(
        primary=True,
        name="Primary",
        table=table,
    )

    linked_table = data_fixture.create_database_table(
        user=user, database=table.database
    )

    data_fixture.create_text_field(
        primary=True,
        name="Primary",
        table=linked_table,
    )
    data_fixture.create_url_field(
        name="URL",
        table=linked_table,
    )

    FieldHandler().create_field(
        user, table, "link_row", link_row_table=linked_table, name="Link"
    )
    FieldHandler().create_field(
        user,
        table,
        "lookup",
        name="lookup",
        through_field_name="Link",
        target_field_name="URL",
    )

    response = api_client.get(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()

    lookup_field_definition = response_json[-1]
    assert lookup_field_definition["type"] == "lookup"
    assert lookup_field_definition["array_formula_type"] == "url"
