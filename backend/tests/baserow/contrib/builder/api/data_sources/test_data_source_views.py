from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from baserow.contrib.builder.data_sources.models import DataSource
from baserow.core.services.models import Service


@pytest.mark.django_db
def test_get_data_sources(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source3 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page
    )

    url = reverse("api:builder:data_source:list", kwargs={"page_id": page.id})
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 3
    assert response_json[0]["id"] == data_source1.id
    assert response_json[0]["type"] == "local_baserow_get_row"
    assert "row_id" in response_json[0]
    assert response_json[1]["id"] == data_source2.id
    assert response_json[1]["type"] == "local_baserow_get_row"
    assert response_json[2]["id"] == data_source3.id
    assert response_json[2]["type"] == "local_baserow_list_rows"
    assert "row_id" not in response_json[2]


@pytest.mark.django_db
def test_create_data_source(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)

    url = reverse("api:builder:data_source:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": "local_baserow_get_row"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "local_baserow_get_row"
    assert response_json["view_id"] is None
    assert response_json["table_id"] is None

    table = data_fixture.create_database_table(user=user)

    response = api_client.post(
        url,
        {
            "type": "local_baserow_get_row",
            "table_id": table.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["table_id"] == table.id
    assert response_json["view_id"] is None


@pytest.mark.django_db
def test_create_data_source_bad_request(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)

    url = reverse("api:builder:data_source:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": "local_baserow_get_row", "table_id": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
def test_create_data_source_permission_denied(
    api_client, data_fixture, stub_check_permissions
):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)

    url = reverse("api:builder:data_source:list", kwargs={"page_id": page.id})
    with stub_check_permissions(raise_permission_denied=True):
        response = api_client.post(
            url,
            {"type": "local_baserow_get_row"},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "PERMISSION_DENIED"


@pytest.mark.django_db
def test_create_data_source_page_does_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    url = reverse("api:builder:data_source:list", kwargs={"page_id": 0})
    response = api_client.post(
        url,
        {"type": "local_baserow_get_row"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_PAGE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_update_data_source(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    view = data_fixture.create_grid_view(user, table=table)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:data_source:item", kwargs={"data_source_id": data_source1.id}
    )

    response = api_client.patch(
        url,
        {
            "table_id": table.id,
            "view_id": view.id,
            "row_id": '"test"',
            "name": "name test",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["view_id"] == view.id
    assert response.json()["table_id"] == table.id
    assert response.json()["row_id"] == '"test"'
    assert response.json()["name"] == "name test"


@pytest.mark.django_db
def test_update_data_source_with_filters(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    formula_field = data_fixture.create_text_field(table=table)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:data_source:item", kwargs={"data_source_id": data_source1.id}
    )

    # No existing filters, add one.
    response = api_client.patch(
        url,
        {
            "filters": [
                {
                    "field": text_field.id,
                    "type": "equals",
                    "value": "foobar",
                    "value_is_formula": False,
                },
                {
                    "field": formula_field.id,
                    "type": "equals",
                    "value": "get('page_parameter.id')",
                    "value_is_formula": True,
                },
            ]
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    service_filters = data_source1.service.service_filters.order_by("id")
    assert response.json()["filters"] == [
        {
            "id": service_filters[0].id,
            "order": service_filters[0].order,
            "field": text_field.id,
            "type": "equals",
            "value": "foobar",
            "value_is_formula": False,
        },
        {
            "id": service_filters[1].id,
            "order": service_filters[1].order,
            "field": formula_field.id,
            "type": "equals",
            "value": "get('page_parameter.id')",
            "value_is_formula": True,
        },
    ]

    # Reset the filters to nothing.
    response = api_client.patch(
        url,
        {"filters": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["filters"] == []

    # Given an existing filter, we delete it if it's not in the payload.
    data_fixture.create_local_baserow_table_service_filter(
        service=data_source1.service, field=text_field, value="baz", order=0
    )
    response = api_client.patch(
        url,
        {
            "filters": [
                {
                    "service": data_source1.service_id,
                    "field": text_field.id,
                    "type": "equals",
                    "value": "foobar",
                    "value_is_formula": False,
                }
            ]
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    service_filter = data_source1.service.service_filters.get()
    assert response.json()["filters"] == [
        {
            "id": service_filter.id,
            "order": 0,
            "field": text_field.id,
            "type": "equals",
            "value": "foobar",
            "value_is_formula": False,
        }
    ]


@pytest.mark.django_db
def test_update_data_source_change_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:data_source:item", kwargs={"data_source_id": data_source1.id}
    )

    response = api_client.patch(
        url,
        {"type": "local_baserow_list_rows"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json()["type"] == "local_baserow_list_rows"

    response = api_client.patch(
        url,
        {"type": None},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json()["type"] is None


@pytest.mark.django_db
def test_update_data_source_with_service_type_for_different_dispatch_type(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:data_source:item", kwargs={"data_source_id": data_source.id}
    )

    response = api_client.patch(
        url,
        {"type": "local_baserow_upsert_row"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_DATA_SOURCE_CANNOT_USE_SERVICE_TYPE"


@pytest.mark.django_db
def test_update_data_source_compatible_integration_is_persisted(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:data_source:item", kwargs={"data_source_id": data_source1.id}
    )

    response = api_client.patch(
        url,
        {"type": "local_baserow_list_rows"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["integration_id"] == data_source1.service.integration_id


@pytest.mark.django_db
def test_update_data_source_bad_request(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:data_source:item", kwargs={"data_source_id": data_source1.id}
    )
    response = api_client.patch(
        url,
        {"table_id": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
def test_update_data_source_does_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    url = reverse("api:builder:data_source:item", kwargs={"data_source_id": 0})
    response = api_client.patch(
        url,
        {"table_id": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_DATA_SOURCE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_move_data_source_empty_payload(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:data_source:move", kwargs={"data_source_id": data_source1.id}
    )
    response = api_client.patch(
        url,
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    assert DataSource.objects.last().id == data_source1.id


@pytest.mark.django_db
def test_move_data_source_null_before_id(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:data_source:move", kwargs={"data_source_id": data_source1.id}
    )
    response = api_client.patch(
        url,
        {"before_id": None},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    assert DataSource.objects.last().id == data_source1.id


@pytest.mark.django_db
def test_move_data_source_before(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:data_source:move", kwargs={"data_source_id": data_source3.id}
    )
    response = api_client.patch(
        url,
        {"before_id": data_source2.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["id"] == data_source3.id

    assert list(DataSource.objects.all())[1].id == data_source3.id


@pytest.mark.django_db
def test_move_data_source_before_not_in_same_page(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    page2 = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page2
    )

    url = reverse(
        "api:builder:data_source:move", kwargs={"data_source_id": data_source3.id}
    )
    response = api_client.patch(
        url,
        {"before_id": data_source2.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_DATA_SOURCE_NOT_IN_SAME_PAGE"


@pytest.mark.django_db
def test_create_data_source_with_service_type_for_different_dispatch_type(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)

    url = reverse("api:builder:data_source:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": "local_baserow_upsert_row"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_DATA_SOURCE_CANNOT_USE_SERVICE_TYPE"


@pytest.mark.django_db
def test_move_data_source_bad_before_id(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:data_source:move", kwargs={"data_source_id": data_source1.id}
    )
    response = api_client.patch(
        url,
        {"before_id": 9999},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_data_source(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    assert Service.objects.count() == 1
    url = reverse(
        "api:builder:data_source:item", kwargs={"data_source_id": data_source1.id}
    )
    response = api_client.delete(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT

    # Ensure the service also is deleted
    assert Service.objects.count() == 0


@pytest.mark.django_db
def test_delete_data_source_permission_denied(
    api_client, data_fixture, stub_check_permissions
):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:data_source:item", kwargs={"data_source_id": data_source1.id}
    )

    with stub_check_permissions(raise_permission_denied=True):
        response = api_client.delete(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "PERMISSION_DENIED"


@pytest.mark.django_db
def test_delete_data_source_data_source_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    url = reverse("api:builder:data_source:item", kwargs={"data_source_id": 0})
    response = api_client.delete(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_DATA_SOURCE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_dispatch_data_source(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="2",
    )

    url = reverse(
        "api:builder:data_source:dispatch", kwargs={"data_source_id": data_source.id}
    )

    response = api_client.post(
        url,
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "id": 2,
        "order": "1.00000000000000000000",
        fields[0].db_column: "Audi",
        fields[1].db_column: "Orange",
    }


@pytest.mark.django_db
def test_dispatch_data_source_permission_denied(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table, fields, rows = data_fixture.build_table(
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="2",
    )

    url = reverse(
        "api:builder:data_source:dispatch", kwargs={"data_source_id": data_source.id}
    )

    response = api_client.post(
        url,
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_dispatch_data_source_using_formula(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id='get("page_parameter.id")',
    )

    url = reverse(
        "api:builder:data_source:dispatch", kwargs={"data_source_id": data_source.id}
    )

    response = api_client.post(
        url,
        {"page_parameter": {"id": 2}, "data_source": {"page_id": page.id}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "id": 2,
        "order": "1.00000000000000000000",
        fields[0].db_column: "Audi",
        fields[1].db_column: "Orange",
    }


@pytest.mark.django_db
def test_dispatch_data_source_improperly_configured(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "2"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source0 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="1",
        name="Working",
    )

    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        row_id='get("page_parameter.id")',
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        view=view,
        table=table,
        integration=None,
        row_id='get("page_parameter.id")',
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id='get("page_parameter.id")',
    )
    data_source4 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id='get("data_source.Working.My Color")',
    )

    url = reverse(
        "api:builder:data_source:dispatch", kwargs={"data_source_id": data_source1.id}
    )

    # The given dispatch query context is wrong
    response = api_client.post(
        url,
        {
            "page_parameter": {"id": 2},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED"
    assert (
        response.json()["detail"] == "The data_source configuration is incorrect: "
        "The table property is missing."
    )

    url = reverse(
        "api:builder:data_source:dispatch", kwargs={"data_source_id": data_source2.id}
    )

    # The given dispatch query context is wrong
    response = api_client.post(
        url,
        {
            "page_parameter": {"id": 2},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED"
    assert (
        response.json()["detail"] == "The data_source configuration is incorrect: "
        "The integration property is missing."
    )

    url = reverse(
        "api:builder:data_source:dispatch", kwargs={"data_source_id": data_source3.id}
    )

    # The given dispatch query context is wrong
    response = api_client.post(
        url,
        {
            "page_parameter": {"id": "test"},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED"
    assert (
        response.json()["detail"] == "The data_source configuration is incorrect: "
        "The result of the `row_id` formula must be an integer or "
        "convertible to an integer."
    )

    url = reverse(
        "api:builder:data_source:dispatch", kwargs={"data_source_id": data_source4.id}
    )


@pytest.mark.django_db
def test_dispatch_data_sources(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
            ["2Cv", "Green"],
            ["Tesla", "Dark"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="2",
    )
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="3",
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="4",
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="bad",
    )
    data_source4 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user, integration=integration, view=view, table=table, row_id="4"
    )

    url = reverse("api:builder:data_source:dispatch-all", kwargs={"page_id": page.id})

    response = api_client.post(
        url,
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        str(data_source.id): {
            fields[1].db_column: "Orange",
            fields[0].db_column: "Audi",
            "id": rows[1].id,
            "order": "1.00000000000000000000",
        },
        str(data_source1.id): {
            fields[1].db_column: "Green",
            fields[0].db_column: "2Cv",
            "id": rows[2].id,
            "order": "1.00000000000000000000",
        },
        str(data_source2.id): {
            fields[1].db_column: "Dark",
            fields[0].db_column: "Tesla",
            "id": rows[3].id,
            "order": "1.00000000000000000000",
        },
        str(data_source3.id): {
            "_error": "ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED",
            "detail": "The data_source configuration is incorrect: "
            "The `row_id` formula can't be resolved: "
            "Invalid syntax at line 1, col 3: mismatched input "
            "'the end of the formula' expecting '('",
        },
    }
