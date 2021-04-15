import pytest

from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from django.shortcuts import reverse
from django.db import connections
from django.apps.registry import apps

from baserow.core.handler import CoreHandler
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import LinkRowField
from baserow.contrib.database.fields.exceptions import (
    LinkRowTableNotInSameDatabase,
    LinkRowTableNotProvided,
)
from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
def test_call_apps_registry_pending_operations(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )
    field_handler = FieldHandler()
    field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Test",
        link_row_table=customers_table,
    )
    table.get_model()
    # Make sure that there are no pending operations in the app registry. Because a
    # Django ManyToManyField registers pending operations every time a table model is
    # generated, which can causes a memory leak if they are not triggered.
    assert len(apps._pending_operations) == 0


@pytest.mark.django_db
def test_link_row_field_type(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )
    cars_table = data_fixture.create_database_table(name="Cars", database=database)
    unrelated_table_1 = data_fixture.create_database_table(name="Unrelated")

    field_handler = FieldHandler()
    row_handler = RowHandler()

    # Create a primary field and some example data for the customers table.
    customers_primary_field = field_handler.create_field(
        user=user, table=customers_table, type_name="text", name="Name", primary=True
    )
    customers_row_1 = row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary_field.id}": "John"},
    )
    customers_row_2 = row_handler.create_row(
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

    with pytest.raises(LinkRowTableNotProvided):
        field_handler.create_field(
            user=user, table=table, type_name="link_row", name="Without table"
        )

    with pytest.raises(LinkRowTableNotInSameDatabase):
        field_handler.create_field(
            user=user,
            table=table,
            type_name="link_row",
            name="Unrelated",
            link_row_table=unrelated_table_1,
        )

    link_field_1 = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Customer",
        link_row_table=customers_table,
    )
    link_field_2 = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Customer",
        link_row_table=customers_table,
    )

    assert link_field_1.link_row_related_field.name == "Example"
    assert link_field_2.link_row_related_field.name == "Example"

    connection = connections["default"]
    tables = connection.introspection.table_names()

    assert (
        link_field_1.through_table_name
        == link_field_1.link_row_related_field.through_table_name
    )
    assert (
        link_field_2.through_table_name
        == link_field_2.link_row_related_field.through_table_name
    )

    assert link_field_1.through_table_name in tables
    assert link_field_2.through_table_name in tables

    model = table.get_model()
    table_row = model.objects.create()

    getattr(table_row, f"field_{link_field_1.id}").add(customers_row_1.id)
    results = getattr(table_row, f"field_{link_field_1.id}").all()
    assert len(results) == 1
    assert getattr(results[0], f"field_{customers_primary_field.id}") == "John"

    getattr(table_row, f"field_{link_field_2.id}").add(
        customers_row_1.id, customers_row_2.id
    )
    results = getattr(table_row, f"field_{link_field_2.id}").all()
    assert len(results) == 2
    assert getattr(results[0], f"field_{customers_primary_field.id}") == "John"
    assert getattr(results[1], f"field_{customers_primary_field.id}") == "Jane"

    table_row_2 = model.objects.create()
    getattr(table_row_2, f"field_{link_field_1.id}").add(customers_row_2.id)
    results = getattr(table_row_2, f"field_{link_field_1.id}").all()
    assert len(results) == 1
    assert getattr(results[0], f"field_{customers_primary_field.id}") == "Jane"

    # Going to change only the name of the field. This should not result in any errors
    # of schema changes.
    link_field_1 = field_handler.update_field(user, link_field_1, name="Customer 2")

    with pytest.raises(LinkRowTableNotInSameDatabase):
        field_handler.update_field(user, link_field_1, link_row_table=unrelated_table_1)

    model = table.get_model()
    assert model.objects.all().count() == 2

    # Change the table, this should destroy all relations.
    old_link_field_1_relation_id = link_field_1.link_row_relation_id
    link_field_1 = field_handler.update_field(
        user, link_field_1, link_row_table=cars_table
    )

    model = table.get_model()
    table_rows = model.objects.all()
    table_row = table_rows[0]
    table_row_2 = table_rows[1]

    assert link_field_1.link_row_table.id == cars_table.id
    assert link_field_1.link_row_relation_id == old_link_field_1_relation_id
    assert getattr(table_row, f"field_{link_field_1.id}").all().count() == 0
    assert getattr(table_row, f"field_{link_field_2.id}").all().count() == 2
    assert getattr(table_row_2, f"field_{link_field_1.id}").all().count() == 0
    assert getattr(table_row_2, f"field_{link_field_2.id}").all().count() == 0

    link_field_2 = field_handler.update_field(user, link_field_2, new_type_name="text")

    model = table.get_model()
    table_row = model.objects.all().first()

    assert getattr(table_row, f"field_{link_field_2.id}") is None
    assert LinkRowField.objects.all().count() == 2

    setattr(table_row, f"field_{link_field_2.id}", "Text value")
    table_row.save()
    assert getattr(table_row, f"field_{link_field_2.id}") == "Text value"

    # Delete the existing field. Alter that the related field should be deleted and
    # no table named _relation_ should exist.
    field_handler.delete_field(user, link_field_1)
    assert LinkRowField.objects.all().count() == 0
    for t in connection.introspection.table_names():
        if "_relation_" in t:
            assert False

    # Change a the text field back into a link row field.
    link_field_2 = field_handler.update_field(
        user, link_field_2, new_type_name="link_row", link_row_table=customers_table
    )

    assert link_field_2.link_row_related_field.name == "Example"
    assert (
        link_field_2.through_table_name
        == link_field_2.link_row_related_field.through_table_name
    )
    assert link_field_2.through_table_name in connection.introspection.table_names()
    assert LinkRowField.objects.all().count() == 2

    model = table.get_model()
    table_row = model.objects.all().first()

    getattr(table_row, f"field_{link_field_2.id}").add(
        customers_row_1.id, customers_row_2.id
    )
    results = getattr(table_row, f"field_{link_field_2.id}").all()
    assert len(results) == 2
    assert getattr(results[0], f"field_{customers_primary_field.id}") == "John"
    assert getattr(results[1], f"field_{customers_primary_field.id}") == "Jane"


@pytest.mark.django_db
def test_link_row_field_type_rows(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    example_table = data_fixture.create_database_table(
        name="Example", database=database
    )
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )
    users_table = data_fixture.create_database_table(name="Users", database=database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    link_row_field = field_handler.create_field(
        user=user,
        table=example_table,
        type_name="link_row",
        link_row_table=customers_table,
    )

    customers_row_1 = row_handler.create_row(user=user, table=customers_table)
    customers_row_2 = row_handler.create_row(user=user, table=customers_table)
    customers_row_3 = row_handler.create_row(user=user, table=customers_table)

    row = row_handler.create_row(
        user=user,
        table=example_table,
        values={
            f"field_{link_row_field.id}": [customers_row_1.id, customers_row_2.id],
        },
    )
    row_2 = row_handler.create_row(
        user=user,
        table=example_table,
        values={
            f"field_{link_row_field.id}": [customers_row_1.id],
        },
    )

    example_table.name = "Example2"
    example_table.save()

    customers_table.name = "Customers2"
    customers_table.save()

    row_1_all = getattr(row, f"field_{link_row_field.id}").all()
    row_2_all = getattr(row_2, f"field_{link_row_field.id}").all()
    row_1_ids = [i.id for i in row_1_all]
    row_2_ids = [i.id for i in row_2_all]

    assert row_1_all.count() == 2
    assert row_2_all.count() == 1
    assert customers_row_1.id in row_1_ids
    assert customers_row_2.id in row_1_ids
    assert customers_row_1.id in row_2_ids

    row = row_handler.update_row(
        user=user,
        table=example_table,
        row_id=row.id,
        values={f"field_{link_row_field.id}": [customers_row_3.id]},
    )
    row_2 = row_handler.update_row(
        user=user,
        table=example_table,
        row_id=row_2.id,
        values={f"field_{link_row_field.id}": [customers_row_2.id, customers_row_1.id]},
    )

    row_1_all = getattr(row, f"field_{link_row_field.id}").all()
    row_2_all = getattr(row_2, f"field_{link_row_field.id}").all()
    row_1_ids = [i.id for i in row_1_all]
    row_2_ids = [i.id for i in row_2_all]

    assert row_1_all.count() == 1
    assert row_2_all.count() == 2
    assert customers_row_3.id in row_1_ids
    assert customers_row_1.id in row_2_ids
    assert customers_row_2.id in row_2_ids

    # Check if the relations are there via the customers table.
    customers_table.refresh_from_db()
    customers_model = customers_table.get_model()
    related_field = link_row_field.link_row_related_field
    customer_rows = customers_model.objects.all()

    assert customer_rows.count() == 3

    customers_row_1 = customer_rows[0]
    customers_row_2 = customer_rows[1]
    customers_row_3 = customer_rows[2]

    customer_row_1_all = getattr(customers_row_1, f"field_{related_field.id}").all()
    customer_row_2_all = getattr(customers_row_2, f"field_{related_field.id}").all()
    customer_row_3_all = getattr(customers_row_3, f"field_{related_field.id}").all()

    assert customer_row_1_all.count() == 1
    assert customer_row_2_all.count() == 1
    assert customer_row_3_all.count() == 1

    customers_row_1_ids = [i.id for i in customer_row_1_all]
    customers_row_2_ids = [i.id for i in customer_row_2_all]
    customers_row_3_ids = [i.id for i in customer_row_3_all]

    assert row_2.id in customers_row_1_ids
    assert row_2.id in customers_row_2_ids
    assert row.id in customers_row_3_ids

    # When changing the link row table table all the existing relations should be
    # deleted.
    link_row_field = field_handler.update_field(
        user=user,
        field=link_row_field,
        type_name="link_row",
        link_row_table=users_table,
    )

    example_table.refresh_from_db()
    model = example_table.get_model()
    rows = model.objects.all()
    row = rows[0]
    row_2 = rows[1]

    assert getattr(row, f"field_{link_row_field.id}").all().count() == 0
    assert getattr(row_2, f"field_{link_row_field.id}").all().count() == 0

    # Just check if the field can be deleted can be deleted.
    field_handler.delete_field(user=user, field=link_row_field)
    assert Field.objects.all().count() == 0


@pytest.mark.django_db
def test_link_row_enhance_queryset(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    example_table = data_fixture.create_database_table(
        name="Example", database=database
    )
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )

    field_handler = FieldHandler()
    row_handler = RowHandler()

    link_row_field = field_handler.create_field(
        user=user,
        table=example_table,
        type_name="link_row",
        link_row_table=customers_table,
    )

    customers_row_1 = row_handler.create_row(user=user, table=customers_table)
    customers_row_2 = row_handler.create_row(user=user, table=customers_table)
    customers_row_3 = row_handler.create_row(user=user, table=customers_table)

    row_handler.create_row(
        user=user,
        table=example_table,
        values={
            f"field_{link_row_field.id}": [customers_row_1.id, customers_row_2.id],
        },
    )
    row_handler.create_row(
        user=user,
        table=example_table,
        values={
            f"field_{link_row_field.id}": [customers_row_1.id],
        },
    )
    row_handler.create_row(
        user=user,
        table=example_table,
        values={
            f"field_{link_row_field.id}": [customers_row_3.id],
        },
    )

    model = example_table.get_model()
    rows = list(model.objects.all().enhance_by_fields())

    with django_assert_num_queries(0):
        for row in rows:
            list(getattr(row, f"field_{link_row_field.id}").all())


@pytest.mark.django_db
def test_link_row_field_type_api_views(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    unrelated_database = data_fixture.create_database_application(
        user=user, name="Unrelated"
    )
    table = data_fixture.create_database_table(name="Example", database=database)
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )
    cars_table = data_fixture.create_database_table(name="Cars", database=database)
    unrelated_table_1 = data_fixture.create_database_table(
        name="Unrelated", database=unrelated_database
    )
    unrelated_table_2 = data_fixture.create_database_table(name="Unrelated 2")

    # Try to make a relation with a table from another database
    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "Link", "type": "link_row", "link_row_table": unrelated_table_1.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_LINK_ROW_TABLE_NOT_IN_SAME_DATABASE"
    assert LinkRowField.objects.all().count() == 0

    # Try to make a relation with a table that we don't have access to.
    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "Link", "type": "link_row", "link_row_table": unrelated_table_2.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"
    assert LinkRowField.objects.all().count() == 0

    # Try to make a relation without providing the table
    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "Link", "type": "link_row"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_LINK_ROW_TABLE_NOT_PROVIDED"
    assert LinkRowField.objects.all().count() == 0

    # Create new link row field type.
    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {
            "name": "Link 1",
            "type": "link_row",
            "link_row_table": customers_table.id,
            # The `link_row_related_field` is a read_only field so we deliberately set
            # an unknown id to see if it is ignored.
            "link_row_related_field": 999999,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Link 1"
    assert response_json["type"] == "link_row"
    assert response_json["link_row_table"] == customers_table.id
    assert LinkRowField.objects.all().count() == 2
    field_id = response_json["id"]

    field = LinkRowField.objects.all().order_by("id").first()
    related_field = LinkRowField.objects.all().order_by("id").last()

    assert response_json["link_row_related_field"] == related_field.id
    assert response_json["link_row_related_field"] != 999999

    # Check if the correct fields are correctly linked.
    assert field.table.id == table.id
    assert field.link_row_table.id == customers_table.id
    assert related_field.table.id == customers_table.id
    assert related_field.link_row_table.id == table.id
    assert field.link_row_relation_id == related_field.link_row_relation_id

    # Just fetching the field and check if is has the correct values.
    response = api_client.get(
        reverse("api:database:fields:item", kwargs={"field_id": field_id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Link 1"
    assert response_json["type"] == "link_row"
    assert response_json["link_row_table"] == customers_table.id
    assert response_json["link_row_related_field"] == related_field.id

    # Just fetching the related field and check if is has the correct values.
    response = api_client.get(
        reverse("api:database:fields:item", kwargs={"field_id": related_field.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Example"
    assert response_json["link_row_table"] == table.id
    assert response_json["link_row_related_field"] == field.id

    # Only updating the name of the field without changing anything else
    response = api_client.patch(
        reverse("api:database:fields:item", kwargs={"field_id": field_id}),
        {"name": "Link new name"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Link new name"
    assert response_json["type"] == "link_row"
    assert response_json["link_row_table"] == customers_table.id
    assert response_json["link_row_related_field"] == related_field.id

    # Only try to update the link_row_related_field, but this is a read only field so
    # nothing should happen.
    response = api_client.patch(
        reverse("api:database:fields:item", kwargs={"field_id": field_id}),
        {"link_row_related_field": 9999},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Link new name"
    assert response_json["type"] == "link_row"
    assert response_json["link_row_table"] == customers_table.id
    assert response_json["link_row_related_field"] == related_field.id

    response = api_client.patch(
        reverse("api:database:fields:item", kwargs={"field_id": field_id}),
        {"link_row_table": cars_table.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Link new name"
    assert response_json["type"] == "link_row"
    assert response_json["link_row_table"] == cars_table.id
    assert response_json["link_row_related_field"] == related_field.id

    field.refresh_from_db()
    related_field.refresh_from_db()

    # Check if the correct fields are still linked.
    assert field.table.id == table.id
    assert field.link_row_table.id == cars_table.id
    assert related_field.table.id == cars_table.id
    assert related_field.link_row_table.id == table.id

    url = reverse("api:database:fields:item", kwargs={"field_id": field_id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT
    assert LinkRowField.objects.all().count() == 0


@pytest.mark.django_db
def test_link_row_field_type_api_row_views(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    example_table = data_fixture.create_database_table(
        name="Example", database=database
    )
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )
    grid = data_fixture.create_grid_view(table=example_table)

    data_fixture.create_text_field(name="Name", table=example_table, primary=True)
    customers_primary = data_fixture.create_text_field(
        name="Customer name", table=customers_table, primary=True
    )

    field_handler = FieldHandler()
    row_handler = RowHandler()

    link_row_field = field_handler.create_field(
        user=user,
        table=example_table,
        type_name="link_row",
        link_row_table=customers_table,
    )

    customers_row_1 = row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary.id}": "John Doe"},
    )
    customers_row_2 = row_handler.create_row(
        user=user,
        table=customers_table,
        values={f"field_{customers_primary.id}": "Jane Doe"},
    )
    customers_row_3 = row_handler.create_row(user=user, table=customers_table)

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": example_table.id}),
        {
            f"field_{link_row_field.id}": "Random",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response_json["detail"][f"field_{link_row_field.id}"][0]["code"] == "not_a_list"
    )

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": example_table.id}),
        {
            f"field_{link_row_field.id}": ["a"],
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response_json["detail"][f"field_{link_row_field.id}"]["0"][0]["code"]
        == "invalid"
    )

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": example_table.id}),
        {
            f"field_{link_row_field.id}": [customers_row_1.id, customers_row_2.id, 999],
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    row_id = response_json["id"]
    assert response.status_code == HTTP_200_OK
    assert len(response_json[f"field_{link_row_field.id}"]) == 2
    assert response_json[f"field_{link_row_field.id}"][0]["id"] == customers_row_1.id
    assert response_json[f"field_{link_row_field.id}"][0]["value"] == "John Doe"
    assert response_json[f"field_{link_row_field.id}"][1]["id"] == customers_row_2.id
    assert response_json[f"field_{link_row_field.id}"][1]["value"] == "Jane Doe"

    model = example_table.get_model()
    assert model.objects.all().count() == 1

    url = reverse(
        "api:database:rows:item",
        kwargs={"table_id": example_table.id, "row_id": row_id},
    )
    response = api_client.patch(
        url,
        {
            f"field_{link_row_field.id}": [],
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json[f"field_{link_row_field.id}"]) == 0

    url = reverse(
        "api:database:rows:item",
        kwargs={"table_id": example_table.id, "row_id": row_id},
    )
    response = api_client.patch(
        url,
        {
            f"field_{link_row_field.id}": [customers_row_2.id, customers_row_3.id],
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json[f"field_{link_row_field.id}"]) == 2
    assert response_json[f"field_{link_row_field.id}"][0]["id"] == customers_row_2.id
    assert response_json[f"field_{link_row_field.id}"][0]["value"] == "Jane Doe"
    assert response_json[f"field_{link_row_field.id}"][1]["id"] == customers_row_3.id
    assert not response_json[f"field_{link_row_field.id}"][1]["value"]

    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 1
    assert response_json["results"][0]["id"] == row_id
    assert len(response_json["results"][0][f"field_{link_row_field.id}"]) == 2

    url = reverse(
        "api:database:rows:item",
        kwargs={"table_id": example_table.id, "row_id": row_id},
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT
    assert model.objects.all().count() == 0

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": example_table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json[f"field_{link_row_field.id}"]) == 0


@pytest.mark.django_db
def test_import_export_link_row_field(data_fixture, user_tables_in_separate_db):
    user = data_fixture.create_user()
    imported_group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)
    customers_table = data_fixture.create_database_table(
        name="Customers", database=database
    )
    field_handler = FieldHandler()
    core_handler = CoreHandler()
    link_row_field = field_handler.create_field(
        user=user, table=table, type_name="link_row", link_row_table=customers_table
    )

    row_handler = RowHandler()
    c_row = row_handler.create_row(user=user, table=customers_table, values={})
    c_row_2 = row_handler.create_row(user=user, table=customers_table, values={})
    row = row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{link_row_field.id}": [c_row.id, c_row_2.id]},
    )

    exported_applications = core_handler.export_group_applications(database.group)
    imported_applications, id_mapping = core_handler.import_application_to_group(
        imported_group, exported_applications
    )
    imported_database = imported_applications[0]
    imported_tables = imported_database.table_set.all()
    imported_table = imported_tables[0]
    imported_customers_table = imported_tables[1]
    imported_link_row_field = imported_table.field_set.all().first().specific
    imported_link_row_relation_field = (
        imported_customers_table.field_set.all().first().specific
    )

    assert imported_table.id != table.id
    assert imported_table.name == table.name
    assert imported_customers_table.id != customers_table.id
    assert imported_customers_table.name == customers_table.name
    assert imported_link_row_field.id != link_row_field.id
    assert imported_link_row_field.name == link_row_field.name
    assert imported_link_row_field.link_row_table_id == imported_customers_table.id
    assert imported_link_row_relation_field.link_row_table_id == imported_table.id
    assert imported_link_row_field.link_row_relation_id == (
        imported_link_row_relation_field.link_row_relation_id
    )

    imported_c_row = row_handler.get_row(
        user=user, table=imported_customers_table, row_id=c_row.id
    )
    imported_c_row_2 = row_handler.get_row(
        user=user, table=imported_customers_table, row_id=c_row_2.id
    )
    imported_row = row_handler.get_row(user=user, table=imported_table, row_id=row.id)

    assert imported_row.id == row.id
    assert imported_c_row.id == c_row.id
    assert imported_c_row_2.id == c_row_2.id
    assert [
        r.id for r in getattr(imported_row, f"field_{imported_link_row_field.id}").all()
    ] == [imported_c_row.id, imported_c_row_2.id]
