from django.shortcuts import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from baserow.test_utils.helpers import is_dict_subset


@pytest.mark.django_db
@pytest.mark.field_file
@pytest.mark.api_rows
def test_batch_create_rows_file_field(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)
    file1 = data_fixture.create_user_file(
        original_name="test.txt",
        is_image=True,
    )
    file2 = data_fixture.create_user_file(
        original_name="test2.txt",
        is_image=True,
    )
    file3 = data_fixture.create_user_file(
        original_name="test3.txt",
        is_image=True,
    )
    model = table.get_model()
    url = reverse("api:database:rows:batch", kwargs={"table_id": table.id})
    request_body = {
        "items": [
            {
                f"field_{file_field.id}": [
                    {"name": file3.name, "visible_name": "new name"}
                ],
            },
            {
                f"field_{file_field.id}": [
                    {"name": file3.name, "visible_name": "new name"},
                    {"name": file2.name, "visible_name": "new name"},
                ],
            },
            {
                f"field_{file_field.id}": [],
            },
        ]
    }
    expected_response_body = {
        "items": [
            {
                f"id": 1,
                f"field_{file_field.id}": [{"name": file3.name, "is_image": True}],
                "order": "1.00000000000000000000",
            },
            {
                f"id": 2,
                f"field_{file_field.id}": [
                    {
                        "name": file2.name,
                        "is_image": True,
                    },
                    {
                        "name": file3.name,
                        "is_image": True,
                    },
                ],
                "order": "2.00000000000000000000",
            },
            {
                f"id": 3,
                f"field_{file_field.id}": [],
                "order": "3.00000000000000000000",
            },
        ]
    }

    response = api_client.post(
        url,
        request_body,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_200_OK
    assert is_dict_subset(expected_response_body, response.json())
    rows = model.objects.all()
    assert len(getattr(rows[0], f"field_{file_field.id}")) == 1
    assert len(getattr(rows[1], f"field_{file_field.id}")) == 2
    assert len(getattr(rows[2], f"field_{file_field.id}")) == 0


@pytest.mark.django_db
@pytest.mark.field_file
@pytest.mark.api_rows
def test_batch_create_rows_file_field_with_csv_string(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)
    url = reverse("api:database:rows:batch", kwargs={"table_id": table.id})
    file1 = data_fixture.create_user_file(
        original_name="test.txt",
        is_image=True,
    )
    file2 = data_fixture.create_user_file(
        original_name="test2.txt",
        is_image=True,
    )
    file3 = data_fixture.create_user_file(
        original_name="test3.txt",
        is_image=True,
    )

    # Test with only one field name
    request_body = {
        "items": [
            {
                f"field_{file_field.id}": file1.name,
            },
        ]
    }
    response = api_client.post(
        url,
        request_body,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_200_OK

    model = table.get_model()
    rows = model.objects.all()

    assert len(getattr(rows[0], f"field_{file_field.id}")) == 1

    # Test with multiple field names
    request_body = {
        "items": [
            {
                f"field_{file_field.id}": f"{file1.name},{file2.name},{file3.name}",
            },
        ]
    }
    response = api_client.post(
        url,
        request_body,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_200_OK

    rows = model.objects.all()

    assert len(getattr(rows[1], f"field_{file_field.id}")) == 3

    # Test with array of field names
    request_body = {
        "items": [
            {
                f"field_{file_field.id}": [file1.name, file2.name],
            },
        ]
    }
    response = api_client.post(
        url,
        request_body,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_200_OK

    rows = model.objects.all()

    assert len(getattr(rows[2], f"field_{file_field.id}")) == 2


@pytest.mark.django_db
@pytest.mark.field_file
@pytest.mark.api_rows
def test_batch_create_rows_file_field_mixed_types(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)
    url = reverse("api:database:rows:batch", kwargs={"table_id": table.id})
    file1 = data_fixture.create_user_file(
        original_name="test.txt",
        is_image=True,
    )
    file2 = data_fixture.create_user_file(
        original_name="test2.txt",
        is_image=True,
    )

    request_body = {
        "items": [
            {
                f"field_{file_field.id}": [file1.name, {"name": file2.name}],
            },
        ]
    }
    response = api_client.post(
        url,
        request_body,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json == {
        "error": "ERROR_REQUEST_BODY_VALIDATION",
        "detail": {
            "items": {
                "0": {
                    f"field_{file_field.id}": [
                        {
                            "error": "All list values must be same type.",
                            "code": "not_same_type",
                        }
                    ]
                }
            }
        },
    }


@pytest.mark.django_db
@pytest.mark.field_file
@pytest.mark.api_rows
def test_batch_create_rows_file_field_invalid_values(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)
    url = reverse("api:database:rows:batch", kwargs={"table_id": table.id})
    file1 = data_fixture.create_user_file(
        original_name="test.txt",
        is_image=True,
    )
    file2 = data_fixture.create_user_file(
        original_name="test2.txt",
        is_image=True,
    )

    request_body = {
        "items": [
            {
                f"field_{file_field.id}": [1, 2],
            },
        ]
    }
    response = api_client.post(
        url,
        request_body,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json == {
        "error": "ERROR_REQUEST_BODY_VALIDATION",
        "detail": {
            "items": {
                "0": {
                    f"field_{file_field.id}": [
                        {
                            "error": "The provided value should be a list of valid "
                            "string or objects containing a value property.",
                            "code": "invalid",
                        }
                    ]
                }
            }
        },
    }


@pytest.mark.django_db
@pytest.mark.field_file
@pytest.mark.api_rows
def test_batch_create_rows_file_field_without_name_property(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)
    url = reverse("api:database:rows:batch", kwargs={"table_id": table.id})
    request_body = {
        "items": [
            {
                f"field_{file_field.id}": [{"visible_name": "test"}],
            },
        ]
    }
    response = api_client.post(
        url,
        request_body,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json == {
        "error": "ERROR_REQUEST_BODY_VALIDATION",
        "detail": {
            "items": {
                "0": {
                    f"field_{file_field.id}": [
                        {
                            "error": (
                                "A name property is required for all values "
                                "of the list."
                            ),
                            "code": "required",
                        }
                    ]
                }
            }
        },
    }


@pytest.mark.django_db
@pytest.mark.field_file
@pytest.mark.api_rows
def test_batch_update_rows_file_field(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)
    file1 = data_fixture.create_user_file(
        original_name="test.txt",
        is_image=True,
    )
    file2 = data_fixture.create_user_file(
        original_name="test2.txt",
        is_image=True,
    )
    file3 = data_fixture.create_user_file(
        original_name="test3.txt",
        is_image=True,
    )
    model = table.get_model()
    row_1 = model.objects.create()
    row_2 = model.objects.create()
    row_3 = model.objects.create()
    url = reverse("api:database:rows:batch", kwargs={"table_id": table.id})
    request_body = {
        "items": [
            {
                f"id": row_1.id,
                f"field_{file_field.id}": [
                    {"name": file3.name, "visible_name": "new name"}
                ],
            },
            {
                f"id": row_2.id,
                f"field_{file_field.id}": [
                    {"name": file3.name, "visible_name": "new name"},
                    {"name": file2.name, "visible_name": "new name"},
                ],
            },
            {
                f"id": row_3.id,
                f"field_{file_field.id}": [],
            },
        ]
    }
    expected_response_body = {
        "items": [
            {
                f"id": row_1.id,
                f"field_{file_field.id}": [{"name": file3.name, "is_image": True}],
                "order": "1.00000000000000000000",
            },
            {
                f"id": row_2.id,
                f"field_{file_field.id}": [
                    {
                        "name": file2.name,
                        "is_image": True,
                    },
                    {
                        "name": file3.name,
                        "is_image": True,
                    },
                ],
                "order": "1.00000000000000000000",
            },
            {
                f"id": row_3.id,
                f"field_{file_field.id}": [],
                "order": "1.00000000000000000000",
            },
        ]
    }

    response = api_client.patch(
        url,
        request_body,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_200_OK
    assert is_dict_subset(expected_response_body, response.json())
    row_1.refresh_from_db()
    row_2.refresh_from_db()
    row_3.refresh_from_db()
    assert len(getattr(row_1, f"field_{file_field.id}")) == 1
    assert len(getattr(row_2, f"field_{file_field.id}")) == 2
    assert len(getattr(row_3, f"field_{file_field.id}")) == 0


@pytest.mark.django_db
@pytest.mark.field_file
@pytest.mark.api_rows
def test_batch_update_rows_file_field_wrong_file(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)
    file1 = data_fixture.create_user_file(
        original_name="test.txt",
        is_image=True,
    )
    model = table.get_model()
    row_1 = model.objects.create()
    row_2 = model.objects.create()
    row_3 = model.objects.create()
    row_4 = model.objects.create()
    url = reverse("api:database:rows:batch", kwargs={"table_id": table.id})
    invalid_file_names = [
        (
            "EJzuFBNeEp58rcVg1T48bF58kl01w2pn_EIdGnULvJESuG09x4Z"
            "BScablA51hrUP4jPohXi6RL7A0yhgEdgO448gGSVi7502E.txt"
        ),
        (
            "XJzuFBNeEp58rcVg1T48bF58kl01w2pn_EIdGnULvJESuG09x4Z"
            "BScablA51hrUP4jPohXi6RL7A0yhgEdgO448gGSVi7503E.txt"
        ),
        (
            "YJzuFBNeEp58rcVg1T48bF58kl01w2pn_EIdGnULvJESuG09x4Z"
            "BScablA51hrUP4jPohXi6RL7A0yhgEdgO448gGSVi7503E.txt"
        ),
    ]
    request_body = {
        "items": [
            {
                f"id": row_1.id,
                f"field_{file_field.id}": [
                    {"name": invalid_file_names[0], "visible_name": "new name"}
                ],
            },
            {
                f"id": row_2.id,
                f"field_{file_field.id}": [
                    {"name": invalid_file_names[1], "visible_name": "new name"},
                    {"name": invalid_file_names[2], "visible_name": "new name"},
                ],
            },
            {
                f"id": row_3.id,
                f"field_{file_field.id}": [],
            },
            {
                f"id": row_4.id,
                f"field_{file_field.id}": [{"name": file1.name, "visible_name": 42.3}],
            },
        ]
    }

    response = api_client.patch(
        url,
        request_body,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"] == (
        f"The user files ['{invalid_file_names[0]}', '{invalid_file_names[1]}',"
        f" '{invalid_file_names[2]}'] do not exist."
    )


@pytest.mark.django_db
@pytest.mark.field_file
@pytest.mark.api_rows
def test_batch_update_rows_file_field_zero_files(api_client, data_fixture):
    user, jwt_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)
    model = table.get_model()
    row_1 = model.objects.create()
    url = reverse("api:database:rows:batch", kwargs={"table_id": table.id})
    request_body = {
        "items": [
            {
                f"id": row_1.id,
                f"field_{file_field.id}": [],
            },
        ]
    }
    expected_response_body = {
        "items": [
            {
                f"id": row_1.id,
                f"field_{file_field.id}": [],
                "order": "1.00000000000000000000",
            },
        ]
    }

    response = api_client.patch(
        url,
        request_body,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {jwt_token}",
    )

    assert response.status_code == HTTP_200_OK
    assert is_dict_subset(expected_response_body, response.json())
    assert len(getattr(row_1, f"field_{file_field.id}")) == 0
