import pytest

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from django.shortcuts import reverse

from baserow.contrib.database.views.models import FormView


@pytest.mark.django_db
def test_create_form_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    user_file_1 = data_fixture.create_user_file()
    user_file_2 = data_fixture.create_user_file()

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "name": "Test Form",
            "type": "form",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["slug"]) == 43
    assert response_json["type"] == "form"
    assert response_json["name"] == "Test Form"
    assert response_json["table_id"] == table.id
    assert response_json["public"] is False
    assert response_json["title"] == ""
    assert response_json["description"] == ""
    assert response_json["cover_image"] is None
    assert response_json["logo_image"] is None
    assert response_json["submit_text"] == "Submit"
    assert response_json["submit_action"] == "MESSAGE"
    assert response_json["submit_action_redirect_url"] == ""

    form = FormView.objects.all()[0]
    assert response_json["id"] == form.id
    assert response_json["name"] == form.name
    assert response_json["order"] == form.order
    assert response_json["slug"] == str(form.slug)
    assert form.table_id == table.id
    assert form.public is False
    assert form.title == ""
    assert form.description == ""
    assert form.cover_image is None
    assert form.logo_image is None
    assert form.submit_text == "Submit"
    assert form.submit_action == "MESSAGE"
    assert form.submit_action_redirect_url == ""
    assert "filters" not in response_json
    assert "sortings" not in response_json

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "slug": "Test",
            "name": "Test Form 2",
            "type": "form",
            "public": True,
            "title": "Title",
            "description": "Description",
            "cover_image": {"name": user_file_1.name},
            "logo_image": {"name": user_file_2.name},
            "submit_text": "NEW SUBMIT",
            "submit_action": "REDIRECT",
            "submit_action_redirect_url": "https://localhost",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["slug"] != "Test"
    assert response_json["name"] == "Test Form 2"
    assert response_json["type"] == "form"
    assert response_json["public"] is True
    assert response_json["title"] == "Title"
    assert response_json["description"] == "Description"
    assert response_json["cover_image"]["name"] == user_file_1.name
    assert response_json["logo_image"]["name"] == user_file_2.name
    assert response_json["submit_text"] == "NEW SUBMIT"
    assert response_json["submit_action"] == "REDIRECT"
    assert response_json["submit_action_redirect_url"] == "https://localhost"

    form = FormView.objects.all()[1]
    assert form.name == "Test Form 2"
    assert form.order == 2
    assert form.table == table
    assert form.public is True
    assert form.title == "Title"
    assert form.description == "Description"
    assert form.cover_image_id == user_file_1.id
    assert form.logo_image_id == user_file_2.id
    assert form.submit_text == "NEW SUBMIT"
    assert form.submit_action == "REDIRECT"
    assert form.submit_action_redirect_url == "https://localhost"

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "type": "form",
            "name": "Test",
            "cover_image": None,
            "logo_image": {"name": user_file_2.name},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["cover_image"] is None
    assert response_json["logo_image"]["name"] == user_file_2.name


@pytest.mark.django_db
def test_update_form_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    view = data_fixture.create_form_view(table=table)
    user_file_1 = data_fixture.create_user_file()
    user_file_2 = data_fixture.create_user_file()

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.patch(
        url,
        {
            "slug": "test",
            "name": "Test Form 2",
            "type": "form",
            "public": True,
            "title": "Title",
            "submit_text": "Patched Submit",
            "description": "Description",
            "cover_image": {"name": user_file_1.name},
            "logo_image": {"name": user_file_2.name},
            "submit_action": "REDIRECT",
            "submit_action_redirect_url": "https://localhost",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["slug"] != "test"
    assert response_json["slug"] == str(view.slug)
    assert response_json["name"] == "Test Form 2"
    assert response_json["type"] == "form"
    assert response_json["title"] == "Title"
    assert response_json["description"] == "Description"
    assert response_json["cover_image"]["name"] == user_file_1.name
    assert response_json["logo_image"]["name"] == user_file_2.name
    assert response_json["submit_text"] == "Patched Submit"
    assert response_json["submit_action"] == "REDIRECT"
    assert response_json["submit_action_redirect_url"] == "https://localhost"

    form = FormView.objects.all()[0]
    assert form.name == "Test Form 2"
    assert form.table == table
    assert form.public is True
    assert form.title == "Title"
    assert form.description == "Description"
    assert form.cover_image_id == user_file_1.id
    assert form.logo_image_id == user_file_2.id
    assert form.submit_text == "Patched Submit"
    assert form.submit_action == "REDIRECT"
    assert form.submit_action_redirect_url == "https://localhost"

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.patch(
        url,
        {
            "cover_image": {"name": user_file_2.name},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["cover_image"]["name"] == user_file_2.name
    assert response_json["logo_image"]["name"] == user_file_2.name

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.patch(
        url,
        {
            "cover_image": None,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    print(response_json)
    assert response.status_code == HTTP_200_OK
    assert response_json["cover_image"] is None
    assert response_json["logo_image"]["name"] == user_file_2.name


@pytest.mark.django_db
def test_meta_submit_form_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    user_file_1 = data_fixture.create_user_file()
    user_file_2 = data_fixture.create_user_file()
    form = data_fixture.create_form_view(
        table=table,
        title="Title",
        description="Description",
        cover_image=user_file_1,
        logo_image=user_file_2,
    )
    text_field = data_fixture.create_text_field(table=table)
    number_field = data_fixture.create_number_field(table=table)
    disabled_field = data_fixture.create_text_field(table=table)
    data_fixture.create_form_view_field_option(
        form,
        text_field,
        name="Text field title",
        description="Text field description",
        required=True,
        enabled=True,
        order=1,
    )
    data_fixture.create_form_view_field_option(
        form, number_field, required=False, enabled=True, order=2
    )
    data_fixture.create_form_view_field_option(
        form, disabled_field, required=False, enabled=False, order=3
    )

    url = reverse("api:database:views:form:submit", kwargs={"slug": "NOT_EXISTING"})
    response = api_client.get(url, format="json")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FORM_DOES_NOT_EXIST"

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.get(url, format="json")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FORM_DOES_NOT_EXIST"

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {token_2}")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FORM_DOES_NOT_EXIST"

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_200_OK

    form.public = True
    form.save()

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.get(url, format="json")
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert response_json["title"] == "Title"
    assert response_json["description"] == "Description"
    assert response_json["cover_image"]["name"] == user_file_1.name
    assert response_json["logo_image"]["name"] == user_file_2.name
    assert len(response_json["fields"]) == 2
    assert response_json["fields"][0] == {
        "name": "Text field title",
        "description": "Text field description",
        "required": True,
        "order": 1,
        "field": {"id": text_field.id, "type": "text", "text_default": ""},
    }
    assert response_json["fields"][1] == {
        "name": number_field.name,
        "description": "",
        "required": False,
        "order": 2,
        "field": {
            "id": number_field.id,
            "type": "number",
            "number_type": "INTEGER",
            "number_decimal_places": 1,
            "number_negative": False,
        },
    }


@pytest.mark.django_db
def test_submit_form_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    form = data_fixture.create_form_view(
        table=table,
        submit_action_message="Test",
        submit_action_redirect_url="https://baserow.io",
    )
    text_field = data_fixture.create_text_field(table=table)
    number_field = data_fixture.create_number_field(table=table)
    disabled_field = data_fixture.create_text_field(table=table)
    data_fixture.create_form_view_field_option(
        form, text_field, required=True, enabled=True, order=1
    )
    data_fixture.create_form_view_field_option(
        form, number_field, required=False, enabled=True, order=2
    )
    data_fixture.create_form_view_field_option(
        form, disabled_field, required=False, enabled=False, order=3
    )

    url = reverse("api:database:views:form:submit", kwargs={"slug": "NOT_EXISTING"})
    response = api_client.post(url, {}, format="json")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FORM_DOES_NOT_EXIST"

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.post(url, {}, format="json")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FORM_DOES_NOT_EXIST"

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.post(
        url, {}, format="json", HTTP_AUTHORIZATION=f"JWT" f" {token_2}"
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FORM_DOES_NOT_EXIST"

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.post(
        url,
        {
            # We do not provide the text field value, but that one is required and we
            # provide a wrong value for the number field, so we expect two errors.
            f"field_{number_field.id}": {},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert len(response_json["detail"]) == 2
    assert response_json["detail"][f"field_{text_field.id}"][0]["code"] == "required"
    assert response_json["detail"][f"field_{number_field.id}"][0]["code"] == "invalid"

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.post(
        url,
        {
            f"field_{text_field.id}": "Valid",
            f"field_{number_field.id}": 0,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json == {
        "submit_action": "MESSAGE",
        "submit_action_message": "Test",
        "submit_action_redirect_url": "https://baserow.io",
    }

    model = table.get_model()
    all = model.objects.all()
    assert len(all) == 1
    assert getattr(all[0], f"field_{text_field.id}") == "Valid"
    assert getattr(all[0], f"field_{number_field.id}") == 0

    form.public = True
    form.save()

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.post(
        url,
        {},
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert len(response_json["detail"]) == 1
    assert response_json["detail"][f"field_{text_field.id}"][0]["code"] == "required"

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.post(
        url,
        {
            f"field_{text_field.id}": "A value",
            f"field_{disabled_field.id}": "Value",
        },
        format="json",
    )
    assert response.status_code == HTTP_200_OK

    model = table.get_model()
    all = model.objects.all()
    assert len(all) == 2
    assert getattr(all[1], f"field_{text_field.id}") == "A value"
    assert getattr(all[1], f"field_{number_field.id}") is None
    assert getattr(all[1], f"field_{disabled_field.id}") is None

    date_field = data_fixture.create_date_field(table=table)
    file_field = data_fixture.create_file_field(table=table)
    url_field = data_fixture.create_url_field(table=table)
    single_select_field = data_fixture.create_single_select_field(table=table)
    boolean_field = data_fixture.create_boolean_field(table=table)
    phone_field = data_fixture.create_phone_number_field(table=table)
    data_fixture.create_form_view_field_option(
        form, file_field, required=True, enabled=True
    )
    data_fixture.create_form_view_field_option(
        form, url_field, required=True, enabled=True
    )
    data_fixture.create_form_view_field_option(
        form, single_select_field, required=True, enabled=True
    )
    data_fixture.create_form_view_field_option(
        form, boolean_field, required=True, enabled=True
    )
    data_fixture.create_form_view_field_option(
        form, date_field, required=True, enabled=True
    )
    data_fixture.create_form_view_field_option(
        form, phone_field, required=True, enabled=True
    )

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.post(
        url,
        {
            f"field_{text_field.id}": "",
            f"field_{date_field.id}": None,
            f"field_{file_field.id}": [],
            f"field_{url_field.id}": "",
            f"field_{single_select_field.id}": "",
            f"field_{boolean_field.id}": False,
            f"field_{phone_field.id}": "",
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert len(response_json["detail"]) == 7

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.post(
        url,
        {},
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert len(response_json["detail"]) == 7


@pytest.mark.django_db
def test_form_view_link_row_lookup_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)
    lookup_table = data_fixture.create_database_table(database=database)
    form = data_fixture.create_form_view(table=table)
    form_2 = data_fixture.create_form_view()
    text_field = data_fixture.create_text_field(table=table)
    link_row_field = data_fixture.create_link_row_field(
        table=table, link_row_table=lookup_table
    )
    disabled_link_row_field = data_fixture.create_link_row_field(
        table=table, link_row_table=lookup_table
    )
    unrelated_link_row_field = data_fixture.create_link_row_field(
        table=table, link_row_table=lookup_table
    )
    primary_related_field = data_fixture.create_text_field(
        table=lookup_table, primary=True
    )
    data_fixture.create_text_field(table=lookup_table)
    data_fixture.create_form_view_field_option(
        form, text_field, required=True, enabled=True, order=1
    )
    data_fixture.create_form_view_field_option(
        form, link_row_field, required=True, enabled=True, order=2
    )
    data_fixture.create_form_view_field_option(
        form, disabled_link_row_field, required=True, enabled=False, order=3
    )
    data_fixture.create_form_view_field_option(
        form_2, unrelated_link_row_field, required=True, enabled=True, order=1
    )

    lookup_model = lookup_table.get_model()
    i1 = lookup_model.objects.create(**{f"field_{primary_related_field.id}": "Test 1"})
    i2 = lookup_model.objects.create(**{f"field_{primary_related_field.id}": "Test 2"})
    i3 = lookup_model.objects.create(**{f"field_{primary_related_field.id}": "Test 3"})

    # Anonymous, not existing slug.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": "NOT_EXISTING", "field_id": link_row_field.id},
    )
    response = api_client.get(url, {})
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    # Anonymous, existing slug, but form is not public.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": form.slug, "field_id": link_row_field.id},
    )
    response = api_client.get(url, format="json")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    # user that doesn't have access to the group, existing slug, but form is not public.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": form.slug, "field_id": link_row_field.id},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token_2}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"

    # valid user, existing slug, but invalid wrong field type.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": form.slug, "field_id": text_field.id},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FIELD_DOES_NOT_EXIST"

    # valid user, existing slug, but invalid wrong field type.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": form.slug, "field_id": 0},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FIELD_DOES_NOT_EXIST"

    # valid user, existing slug, but disabled link row field.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": form.slug, "field_id": disabled_link_row_field.id},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FIELD_DOES_NOT_EXIST"

    # valid user, existing slug, but unrelated link row field.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": form.slug, "field_id": unrelated_link_row_field.id},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FIELD_DOES_NOT_EXIST"

    form.public = True
    form.save()

    # anonymous, existing slug, public form, correct link row field.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": form.slug, "field_id": link_row_field.id},
    )
    response = api_client.get(
        url,
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 3
    assert len(response_json["results"]) == 3
    assert response_json["results"][0]["id"] == i1.id
    assert response_json["results"][0]["value"] == "Test 1"
    assert len(response_json["results"][0]) == 2
    assert response_json["results"][1]["id"] == i2.id
    assert response_json["results"][2]["id"] == i3.id

    # same as before only now with search.
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": form.slug, "field_id": link_row_field.id},
    )
    response = api_client.get(
        f"{url}?search=Test 2",
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 1
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == i2.id
    assert response_json["results"][0]["value"] == "Test 2"

    # same as before only now with pagination
    url = reverse(
        "api:database:views:link_row_field_lookup",
        kwargs={"slug": form.slug, "field_id": link_row_field.id},
    )
    response = api_client.get(
        f"{url}?size=1&page=2",
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 3
    assert response_json["next"] is not None
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == i2.id
    assert response_json["results"][0]["value"] == "Test 2"


@pytest.mark.django_db
def test_test_enable_form_view_file_field_options(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)
    file_field = data_fixture.create_file_field(table=table)

    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})
    response = api_client.patch(
        url,
        {"field_options": {file_field.id: {"enabled": True}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_FORM_VIEW_FIELD_TYPE_IS_NOT_SUPPORTED"
    assert (
        response_json["detail"]
        == "The file field type is not compatible with the form view."
    )
