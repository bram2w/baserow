from unittest.mock import patch

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.shortcuts import reverse
from django.test.utils import CaptureQueriesContext

import pytest
from freezegun import freeze_time
from PIL import Image
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
)

from baserow.contrib.database.views.models import (
    FormView,
    FormViewFieldOptions,
    FormViewFieldOptionsCondition,
)
from baserow.core.user_files.models import UserFile


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
    assert response_json["mode"] == "form"
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
    assert "decorations" not in response_json

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
    assert response_json["mode"] == "form"
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
            "mode": "form",
            "name": "Test",
            "cover_image": None,
            "logo_image": {"name": user_file_2.name},
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["mode"] == "form"
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
    assert response_json["mode"] == "form"
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
    assert form.mode == "form"
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
    assert response.status_code == HTTP_200_OK
    assert response_json["cover_image"] is None
    assert response_json["mode"] == "form"
    assert response_json["logo_image"]["name"] == user_file_2.name


@pytest.mark.django_db
def test_update_form_view_invalid_mode(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    view = data_fixture.create_form_view(table=table)

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.patch(
        url,
        {"mode": "not_existing"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    print(response_json)
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["mode"][0]["code"] == "invalid_choice"


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
    assert response_json["mode"] == "form"
    assert len(response_json["fields"]) == 2
    assert response_json["fields"][0] == {
        "name": "Text field title",
        "description": "Text field description",
        "required": True,
        "order": 1,
        "condition_type": "AND",
        "conditions": [],
        "show_when_matching_conditions": False,
        "field": {"id": text_field.id, "type": "text", "text_default": ""},
    }
    assert response_json["fields"][1] == {
        "name": number_field.name,
        "description": "",
        "required": False,
        "order": 2,
        "condition_type": "AND",
        "conditions": [],
        "show_when_matching_conditions": False,
        "field": {
            "id": number_field.id,
            "type": "number",
            "number_decimal_places": 0,
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
        "row_id": 1,
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
def test_submit_form_view_skip_required_with_conditions(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    form = data_fixture.create_form_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    number_field = data_fixture.create_number_field(table=table)
    data_fixture.create_form_view_field_option(
        form, text_field, required=True, enabled=True
    )
    number_option = data_fixture.create_form_view_field_option(
        form, number_field, required=True, enabled=True
    )

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.post(
        url,
        {
            f"field_{text_field.id}": "test",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert len(response_json["detail"]) == 1

    number_option.show_when_matching_conditions = True
    number_option.save()

    response = api_client.post(
        url,
        {
            f"field_{text_field.id}": "test",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert len(response_json["detail"]) == 1

    # When there is a condition and `show_when_matching_conditions` is `True`,
    # the backend can't validate whether the values match the filter, we we don't do
    # a required validation at all.
    data_fixture.create_form_view_field_options_condition(
        field_option=number_option, field=text_field
    )
    response = api_client.post(
        url,
        {
            f"field_{text_field.id}": "test",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_200_OK


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
    created_on_field = data_fixture.create_created_on_field(table=table)

    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})
    response = api_client.patch(
        url,
        {"field_options": {created_on_field.id: {"enabled": True}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    print(response_json)
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_FORM_VIEW_FIELD_TYPE_IS_NOT_SUPPORTED"
    assert (
        response_json["detail"]
        == "The created_on field type is not compatible with the form view."
    )


@pytest.mark.django_db
def test_form_view_multiple_collaborators_field_options(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)
    multiple_collaborators_field = data_fixture.create_multiple_collaborators_field(
        table=table
    )

    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})
    response = api_client.patch(
        url,
        {"field_options": {multiple_collaborators_field.id: {"enabled": True}}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_FORM_VIEW_FIELD_TYPE_IS_NOT_SUPPORTED"
    assert (
        response_json["detail"]
        == "The multiple_collaborators field type is not compatible with the form view."
    )


@pytest.mark.django_db
def test_get_form_view_field_options(
    api_client, data_fixture, django_assert_num_queries
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    text_field_2 = data_fixture.create_text_field(table=table)
    text_field_option = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field,
        show_when_matching_conditions=True,
    )
    text_field_option_2 = data_fixture.create_form_view_field_option(
        form_view=form_view, field=text_field_2
    )
    condition_1 = data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option, field=text_field_2
    )

    with CaptureQueriesContext(connection) as captured:
        url = reverse(
            "api:database:views:field_options", kwargs={"view_id": form_view.id}
        )
        response = api_client.get(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        response_json = response.json()

    assert response_json == {
        "field_options": {
            str(text_field.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "order": 32767,
                "show_when_matching_conditions": True,
                "condition_type": "AND",
                "conditions": [
                    {
                        "id": condition_1.id,
                        "field": text_field_2.id,
                        "type": "equal",
                        "value": condition_1.value,
                    }
                ],
            },
            str(text_field_2.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "order": 32767,
                "show_when_matching_conditions": False,
                "condition_type": "AND",
                "conditions": [],
            },
        }
    }

    text_field_3 = data_fixture.create_text_field(table=table)
    text_field_option_3 = data_fixture.create_form_view_field_option(
        form_view=form_view, field=text_field_3
    )
    data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option, field=text_field_2
    )
    data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option_2, field=text_field_3
    )
    data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option_3, field=text_field
    )

    with django_assert_num_queries(len(captured.captured_queries)):
        api_client.get(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )


@pytest.mark.django_db
def test_patch_form_view_field_options_conditions_create(
    api_client, data_fixture, django_assert_num_queries
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    text_field_2 = data_fixture.create_text_field(table=table)
    data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field,
        show_when_matching_conditions=False,
    )
    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})
    response = api_client.patch(
        url,
        {
            "field_options": {
                str(text_field.id): {
                    "show_when_matching_conditions": True,
                    "condition_type": "OR",
                    "conditions": [
                        {
                            "id": 0,
                            "field": text_field_2.id,
                            "type": "equal",
                            "value": "test",
                        }
                    ],
                }
            }
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    condition = FormViewFieldOptionsCondition.objects.all().first()
    assert response_json == {
        "field_options": {
            str(text_field.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "show_when_matching_conditions": True,
                "condition_type": "OR",
                "order": 32767,
                "conditions": [
                    {
                        "id": condition.id,
                        "field": text_field_2.id,
                        "type": "equal",
                        "value": "test",
                    }
                ],
            },
            str(text_field_2.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "show_when_matching_conditions": False,
                "condition_type": "AND",
                "order": 32767,
                "conditions": [],
            },
        }
    }


@pytest.mark.django_db
def test_patch_form_view_field_options_conditions_update(
    api_client, data_fixture, django_assert_num_queries
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    text_field_2 = data_fixture.create_text_field(table=table)
    text_field_3 = data_fixture.create_text_field(table=table)
    text_field_option = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field,
        show_when_matching_conditions=False,
    )
    condition_1 = data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option, field=text_field_2
    )

    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})
    response = api_client.patch(
        url,
        {
            "field_options": {
                str(text_field.id): {
                    "show_when_matching_conditions": True,
                    "conditions": [
                        {
                            "id": condition_1.id,
                            "field": text_field_3.id,
                            "type": "not_equal",
                            "value": "test",
                        }
                    ],
                }
            }
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response_json == {
        "field_options": {
            str(text_field.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "show_when_matching_conditions": True,
                "condition_type": "AND",
                "order": 32767,
                "conditions": [
                    {
                        "id": condition_1.id,
                        "field": text_field_3.id,
                        "type": "not_equal",
                        "value": "test",
                    }
                ],
            },
            str(text_field_2.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "show_when_matching_conditions": False,
                "condition_type": "AND",
                "order": 32767,
                "conditions": [],
            },
            str(text_field_3.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "show_when_matching_conditions": False,
                "condition_type": "AND",
                "order": 32767,
                "conditions": [],
            },
        }
    }


@pytest.mark.django_db
def test_patch_form_view_field_options_conditions_update_position(
    api_client, data_fixture, django_assert_num_queries
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    text_field_2 = data_fixture.create_text_field(table=table)
    text_field_3 = data_fixture.create_text_field(table=table)
    text_field_option = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field,
        show_when_matching_conditions=False,
    )
    text_field_option_2 = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field_2,
        show_when_matching_conditions=False,
    )
    text_field_option_3 = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field_3,
        show_when_matching_conditions=True,
    )
    condition = data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option_3, field=text_field_2
    )

    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})
    response = api_client.patch(
        url,
        {
            "field_options": {
                str(text_field.id): {
                    "order": 1,
                    "show_when_matching_conditions": False,
                    "conditions": [],
                },
                str(text_field_3.id): {
                    "order": 2,
                    "show_when_matching_conditions": True,
                },
                str(text_field_2.id): {
                    "order": 3,
                    "show_when_matching_conditions": False,
                    "conditions": [],
                },
            }
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response_json == {
        "field_options": {
            str(text_field.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "show_when_matching_conditions": False,
                "condition_type": "AND",
                "order": 1,
                "conditions": [],
            },
            str(text_field_3.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "show_when_matching_conditions": True,
                "condition_type": "AND",
                "order": 2,
                "conditions": [
                    {
                        "id": condition.id,
                        "field": text_field_2.id,
                        "type": condition.type,
                        "value": condition.value,
                    }
                ],
            },
            str(text_field_2.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "show_when_matching_conditions": False,
                "condition_type": "AND",
                "order": 3,
                "conditions": [],
            },
        }
    }


@pytest.mark.django_db
def test_patch_form_view_field_options_conditions_delete(
    api_client, data_fixture, django_assert_num_queries
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    text_field_2 = data_fixture.create_text_field(table=table)
    text_field_3 = data_fixture.create_text_field(table=table)
    text_field_option = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field,
        show_when_matching_conditions=False,
    )
    data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option, field=text_field_2
    )

    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})
    response = api_client.patch(
        url,
        {
            "field_options": {
                str(text_field.id): {
                    "show_when_matching_conditions": True,
                    "conditions": [],
                }
            }
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response_json == {
        "field_options": {
            str(text_field.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "show_when_matching_conditions": True,
                "condition_type": "AND",
                "order": 32767,
                "conditions": [],
            },
            str(text_field_2.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "show_when_matching_conditions": False,
                "condition_type": "AND",
                "order": 32767,
                "conditions": [],
            },
            str(text_field_3.id): {
                "name": "",
                "description": "",
                "enabled": False,
                "required": True,
                "show_when_matching_conditions": False,
                "condition_type": "AND",
                "order": 32767,
                "conditions": [],
            },
        }
    }


@pytest.mark.django_db
def test_patch_form_view_field_options_conditions_create_invalid_field(
    api_client, data_fixture, django_assert_num_queries
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    field_in_another_table = data_fixture.create_text_field()
    data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field,
        show_when_matching_conditions=False,
    )
    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})
    response = api_client.patch(
        url,
        {
            "field_options": {
                str(text_field.id): {
                    "show_when_matching_conditions": True,
                    "condition_type": "OR",
                    "conditions": [
                        {
                            "id": 0,
                            "field": field_in_another_table.id,
                            "type": "equal",
                            "value": "test",
                        }
                    ],
                }
            }
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_FIELD_NOT_IN_TABLE"


@pytest.mark.django_db
def test_patch_form_view_field_options_conditions_create_num_queries(
    api_client, data_fixture, django_assert_num_queries
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    text_field_2 = data_fixture.create_text_field(table=table)
    form_view = data_fixture.create_form_view(table=table)

    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})

    with CaptureQueriesContext(connection) as captured:
        api_client.patch(
            url,
            {
                "field_options": {
                    str(text_field.id): {
                        "conditions": [
                            {
                                "id": 0,
                                "field": text_field_2.id,
                                "type": "equal",
                                "value": "test",
                            }
                        ],
                    },
                }
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    # Delete newly created form condition because we want to do the same below with
    # the same amount of queries.
    FormViewFieldOptionsCondition.objects.all().delete()

    # Even though we're adding more conditions, we expect to execute the sam amount
    # of queries.
    with django_assert_num_queries(len(captured.captured_queries)):
        api_client.patch(
            url,
            {
                "field_options": {
                    str(text_field.id): {
                        "conditions": [
                            {
                                "id": 0,
                                "field": text_field.id,
                                "type": "equal",
                                "value": "test",
                            },
                            {
                                "id": 0,
                                "field": text_field_2.id,
                                "type": "equal",
                                "value": "test",
                            },
                        ],
                    },
                    str(text_field_2.id): {
                        "conditions": [
                            {
                                "id": 0,
                                "field": text_field.id,
                                "type": "equal",
                                "value": "test",
                            }
                        ],
                    },
                }
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )


@pytest.mark.django_db
def test_patch_form_view_field_options_conditions_update_num_queries(
    api_client, data_fixture, django_assert_num_queries
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    text_field_2 = data_fixture.create_text_field(table=table)
    text_field_3 = data_fixture.create_text_field(table=table)
    text_field_option = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field,
    )
    text_field_option_2 = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field_2,
    )
    text_field_option_3 = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field_3,
    )
    condition_1 = data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option, field=text_field
    )
    condition_1_2 = data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option, field=text_field
    )
    condition_2 = data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option_2, field=text_field
    )
    condition_3 = data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option_3, field=text_field
    )

    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})

    with CaptureQueriesContext(connection) as captured:
        api_client.patch(
            url,
            {
                "field_options": {
                    str(text_field_3.id): {
                        "conditions": [
                            {
                                "id": condition_3.id,
                                "field": condition_3.id,
                                "type": condition_3.type,
                                "value": condition_3.type,
                            }
                        ],
                    }
                }
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    # Even though we're update more conditions, we expect to execute the same amount
    # of queries.
    with django_assert_num_queries(len(captured.captured_queries)):
        api_client.patch(
            url,
            {
                "field_options": {
                    str(text_field.id): {
                        "conditions": [
                            {
                                "id": condition_1.id,
                                "field": condition_1.id,
                                "type": condition_1.type,
                                "value": condition_1.type,
                            },
                            {
                                "id": condition_1_2.id,
                                "field": condition_1_2.field_id,
                                "type": condition_1_2.type,
                                "value": condition_1_2.type,
                            },
                        ],
                    },
                    str(text_field_2.id): {
                        "conditions": [
                            {
                                "id": condition_2.id,
                                "field": condition_2.id,
                                "type": condition_2.type,
                                "value": condition_2.type,
                            }
                        ],
                    },
                    str(text_field_3.id): {
                        "conditions": [
                            {
                                "id": 0,
                                "field": condition_3.id,
                                "type": condition_3.type,
                                "value": condition_3.type,
                            },
                            {
                                "id": condition_3.id,
                                "field": condition_3.id,
                                "type": condition_3.type,
                                "value": condition_3.type,
                            },
                        ],
                    },
                }
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )


@pytest.mark.django_db
def test_patch_form_view_field_options_conditions_delete_num_queries(
    api_client, data_fixture, django_assert_num_queries
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    text_field_2 = data_fixture.create_text_field(table=table)
    text_field_3 = data_fixture.create_text_field(table=table)
    text_field_option = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field,
    )
    text_field_option_2 = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field_2,
    )
    text_field_option_3 = data_fixture.create_form_view_field_option(
        form_view=form_view,
        field=text_field_3,
    )
    data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option, field=text_field
    )
    data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option, field=text_field
    )
    data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option_2, field=text_field
    )
    data_fixture.create_form_view_field_options_condition(
        field_option=text_field_option_3, field=text_field
    )

    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})

    with CaptureQueriesContext(connection) as captured:
        api_client.patch(
            url,
            {
                "field_options": {
                    str(text_field_3.id): {
                        "conditions": [],
                    }
                }
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    # Even though we're deleting more conditions, we expect to execute the same amount
    # of queries.
    with django_assert_num_queries(len(captured.captured_queries)):
        api_client.patch(
            url,
            {
                "field_options": {
                    str(text_field.id): {
                        "conditions": [],
                    },
                    str(text_field_2.id): {
                        "conditions": [],
                    },
                    str(text_field_3.id): {
                        "conditions": [],
                    },
                }
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )


@pytest.mark.django_db
def test_submit_password_protected_form_view_requires_authorization(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    password = "87654321"
    form_view = data_fixture.create_public_password_protected_form_view(
        table=table,
        password=password,
        submit_action_message="Test",
        submit_action_redirect_url="https://baserow.io",
    )
    text_field = data_fixture.create_text_field(table=table)
    number_field = data_fixture.create_number_field(table=table)
    data_fixture.create_form_view_field_option(
        form_view, text_field, required=True, enabled=True, order=1
    )
    data_fixture.create_form_view_field_option(
        form_view, number_field, required=False, enabled=True, order=2
    )

    # without a valid token it is not possible to submit form data
    url = reverse("api:database:views:form:submit", kwargs={"slug": form_view.slug})
    response = api_client.get(url, format="json")
    assert response.status_code == HTTP_401_UNAUTHORIZED

    response = api_client.post(
        reverse("api:database:views:form:submit", kwargs={"slug": form_view.slug}),
        {
            f"field_{text_field.id}": "Valid",
            f"field_{number_field.id}": 0,
        },
        format="json",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # Get the authorization token
    response = api_client.post(
        reverse("api:database:views:public_auth", kwargs={"slug": form_view.slug}),
        {"password": password},
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    public_view_token = response_json.get("access_token", None)
    assert public_view_token is not None

    # Add the token in the header
    url = reverse("api:database:views:form:submit", kwargs={"slug": form_view.slug})
    response = api_client.get(
        url, format="json", HTTP_BASEROW_VIEW_AUTHORIZATION=f"JWT {public_view_token}"
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        url,
        {
            f"field_{text_field.id}": "Valid",
            f"field_{number_field.id}": 0,
        },
        format="json",
        HTTP_BASEROW_VIEW_AUTHORIZATION=f"JWT {public_view_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json == {
        "row_id": 1,
        "submit_action": "MESSAGE",
        "submit_action_message": "Test",
        "submit_action_redirect_url": "https://baserow.io",
    }

    # The original user can always submit forms, even if password protected
    url = reverse("api:database:views:form:submit", kwargs={"slug": form_view.slug})
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        url,
        {
            f"field_{text_field.id}": "More Valid",
            f"field_{number_field.id}": 1,
        },
        format="json",
        HTTP_BASEROW_VIEW_AUTHORIZATION=f"JWT {public_view_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json == {
        "row_id": 2,
        "submit_action": "MESSAGE",
        "submit_action_message": "Test",
        "submit_action_redirect_url": "https://baserow.io",
    }


@pytest.mark.django_db
def test_changing_password_of_a_public_password_protected_form_view_invalidate_previous_tokens(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    password = "12345678"
    form_view = data_fixture.create_public_password_protected_form_view(
        user=user, password=password
    )

    # Get the authorization token
    response = api_client.post(
        reverse("api:database:views:public_auth", kwargs={"slug": form_view.slug}),
        {"password": password},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK, response_json
    public_view_token = response_json.get("access_token", None)
    assert public_view_token is not None

    # Get access using the token
    response = api_client.get(
        reverse("api:database:views:form:submit", kwargs={"slug": form_view.slug}),
        format="json",
        HTTP_BASEROW_VIEW_AUTHORIZATION=f"JWT {public_view_token}",
    )
    assert response.status_code == HTTP_200_OK, response.json()

    # Changing password invalidate tokens
    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": form_view.id}),
        {"public_view_password": "Just another original password"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    # Previous tokens are now invalid
    response = api_client.get(
        reverse("api:database:views:form:submit", kwargs={"slug": form_view.slug}),
        format="json",
        HTTP_BASEROW_VIEW_AUTHORIZATION=f"JWT {public_view_token}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_submit_form_view_for_required_number_field_with_0(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    form = data_fixture.create_form_view(
        table=table,
        submit_action_message="Test",
        submit_action_redirect_url="https://baserow.io",
    )
    number_field = data_fixture.create_number_field(
        table=table, number_negative=False, number_decimal_places=0
    )
    data_fixture.create_form_view_field_option(
        form, number_field, required=True, enabled=True, order=2
    )

    url = reverse("api:database:views:form:submit", kwargs={"slug": form.slug})
    response = api_client.post(
        url,
        {
            f"field_{number_field.id}": "0",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT" f" {token}",
    )
    assert response.status_code == HTTP_200_OK, (
        "Got an error response "
        "instead of the expected "
        "200 OK with body: " + str(response.json())
    )
    response_json = response.json()
    assert response_json == {
        "row_id": 1,
        "submit_action": "MESSAGE",
        "submit_action_message": "Test",
        "submit_action_redirect_url": "https://baserow.io",
    }


@pytest.mark.django_db
def test_upload_file_view(api_client, data_fixture, tmpdir):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    view = data_fixture.create_form_view(public=True)
    file_field = data_fixture.create_file_field()
    data_fixture.create_form_view_field_option(view, field=file_field, enabled=True)

    response = api_client.post(
        reverse(
            "api:database:views:form:upload_file",
            kwargs={"slug": view.slug},
        ),
        format="multipart",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_INVALID_FILE"

    response = api_client.post(
        reverse(
            "api:database:views:form:upload_file",
            kwargs={"slug": view.slug},
        ),
        data={"file": ""},
        format="multipart",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_INVALID_FILE"

    old_limit = settings.BASEROW_FILE_UPLOAD_SIZE_LIMIT_MB
    settings.BASEROW_FILE_UPLOAD_SIZE_LIMIT_MB = 6
    response = api_client.post(
        reverse(
            "api:database:views:form:upload_file",
            kwargs={"slug": view.slug},
        ),
        data={"file": SimpleUploadedFile("test.txt", b"Hello World")},
        format="multipart",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    settings.BASEROW_FILE_UPLOAD_SIZE_LIMIT_MB = old_limit
    assert response.status_code == HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert response.json()["error"] == "ERROR_FILE_SIZE_TOO_LARGE"
    assert response.json()["detail"] == (
        "The provided file is too large. Max 0MB is allowed."
    )

    response = api_client.post(
        reverse(
            "api:database:views:form:upload_file",
            kwargs={"slug": view.slug},
        ),
        data={"file": "not a file"},
        format="multipart",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_INVALID_FILE"

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")

    with patch("baserow.core.user_files.handler.default_storage", new=storage):
        with freeze_time("2020-01-01 12:00"):
            file = SimpleUploadedFile("test.txt", b"Hello World")
            response = api_client.post(
                reverse(
                    "api:database:views:form:upload_file",
                    kwargs={"slug": view.slug},
                ),
                data={"file": file},
                format="multipart",
                HTTP_AUTHORIZATION=f"JWT {token}",
            )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["size"] == 11
    assert response_json["mime_type"] == "text/plain"
    assert response_json["is_image"] is False
    assert response_json["image_width"] is None
    assert response_json["image_height"] is None
    assert response_json["uploaded_at"] == "2020-01-01T12:00:00Z"
    assert response_json["thumbnails"] is None
    assert response_json["original_name"] == "test.txt"
    assert "localhost:8000" in response_json["url"]

    user_file = UserFile.objects.all().last()
    assert user_file.name == response_json["name"]
    assert response_json["url"].endswith(response_json["name"])
    file_path = tmpdir.join("user_files", user_file.name)
    assert file_path.isfile()

    with patch("baserow.core.user_files.handler.default_storage", new=storage):
        file = SimpleUploadedFile("test.txt", b"Hello World")
        response_2 = api_client.post(
            reverse(
                "api:database:views:form:upload_file",
                kwargs={"slug": view.slug},
            ),
            data={"file": file},
            format="multipart",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    # The old file should be provided.
    assert response_2.json()["name"] == response_json["name"]
    assert response_json["original_name"] == "test.txt"

    image = Image.new("RGB", (100, 140), color="red")
    file = SimpleUploadedFile("test.png", b"")
    image.save(file, format="PNG")
    file.seek(0)

    with patch("baserow.core.user_files.handler.default_storage", new=storage):
        response = api_client.post(
            reverse(
                "api:database:views:form:upload_file",
                kwargs={"slug": view.slug},
            ),
            data={"file": file},
            format="multipart",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["mime_type"] == "image/png"
    assert response_json["is_image"] is True
    assert response_json["image_width"] == 100
    assert response_json["image_height"] == 140
    assert len(response_json["thumbnails"]) == 1
    assert "localhost:8000" in response_json["thumbnails"]["tiny"]["url"]
    assert "tiny" in response_json["thumbnails"]["tiny"]["url"]
    assert response_json["thumbnails"]["tiny"]["width"] == 21
    assert response_json["thumbnails"]["tiny"]["height"] == 21
    assert response_json["original_name"] == "test.png"

    user_file = UserFile.objects.all().last()
    file_path = tmpdir.join("user_files", user_file.name)
    assert file_path.isfile()
    file_path = tmpdir.join("thumbnails", "tiny", user_file.name)
    assert file_path.isfile()
    thumbnail = Image.open(file_path.open("rb"))
    assert thumbnail.height == 21
    assert thumbnail.width == 21


@pytest.mark.django_db
def test_upload_file_view_with_no_public_file_field(api_client, data_fixture, tmpdir):
    view = data_fixture.create_form_view(public=True)
    file_field = data_fixture.create_file_field()
    data_fixture.create_form_view_field_option(view, field=file_field, enabled=False)

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    with patch("baserow.core.user_files.handler.default_storage", new=storage):
        with freeze_time("2020-01-01 12:00"):
            file = SimpleUploadedFile("test.txt", b"Hello World")
            response = api_client.post(
                reverse(
                    "api:database:views:form:upload_file",
                    kwargs={"slug": view.slug},
                ),
                data={"file": file},
                format="multipart",
            )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_VIEW_HAS_NO_PUBLIC_FILE_FIELD"


@pytest.mark.django_db
def test_upload_file_form_view_does_not_exist(api_client, data_fixture, tmpdir):
    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    with patch("baserow.core.user_files.handler.default_storage", new=storage):
        with freeze_time("2020-01-01 12:00"):
            file = SimpleUploadedFile("test.txt", b"Hello World")
            response = api_client.post(
                reverse(
                    "api:database:views:form:upload_file",
                    kwargs={"slug": 99999999},
                ),
                data={"file": file},
                format="multipart",
            )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_upload_file_view_form_is_password_protected(api_client, data_fixture, tmpdir):
    password = "password"
    view = data_fixture.create_public_password_protected_form_view(password=password)
    file_field = data_fixture.create_file_field()
    data_fixture.create_form_view_field_option(view, field=file_field, enabled=True)

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    with patch("baserow.core.user_files.handler.default_storage", new=storage):
        with freeze_time("2020-01-01 12:00"):
            file = SimpleUploadedFile("test.txt", b"Hello World")
            response = api_client.post(
                reverse(
                    "api:database:views:form:upload_file",
                    kwargs={"slug": view.slug},
                ),
                data={"file": file},
                format="multipart",
            )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW"

    response = api_client.post(
        reverse("api:database:views:public_auth", kwargs={"slug": view.slug}),
        {"password": password},
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    public_view_token = response_json.get("access_token", None)
    assert public_view_token is not None

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    with patch("baserow.core.user_files.handler.default_storage", new=storage):
        with freeze_time("2020-01-01 12:00"):
            file = SimpleUploadedFile("test.txt", b"Hello World")
            response = api_client.post(
                reverse(
                    "api:database:views:form:upload_file",
                    kwargs={"slug": view.slug},
                ),
                data={"file": file},
                format="multipart",
                HTTP_BASEROW_VIEW_AUTHORIZATION=f"JWT {public_view_token}",
            )

    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_patch_multiple_form_view_field_options_conditions_update(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    text_field_2 = data_fixture.create_text_field(table=table)

    form_view = data_fixture.create_form_view(table=table)
    text_field_2_field_options = FormViewFieldOptions.objects.get(
        form_view=form_view, field=text_field_2
    )

    condition = data_fixture.create_form_view_field_options_condition(
        field_option=text_field_2_field_options, field=text_field
    )

    form_view_2 = data_fixture.create_form_view(table=table)
    text_field_2_field_options_2 = FormViewFieldOptions.objects.get(
        form_view=form_view_2, field=text_field_2
    )
    condition_2 = data_fixture.create_form_view_field_options_condition(
        field_option=text_field_2_field_options_2, field=text_field
    )

    assert FormViewFieldOptions.objects.count() == 4
    assert FormViewFieldOptionsCondition.objects.count() == 2
    assert list(
        FormViewFieldOptionsCondition.objects.order_by("id").values(
            "field_option_id", "field_id", "type"
        )
    ) == [
        {
            "field_option_id": text_field_2_field_options.id,
            "field_id": text_field.id,
            "type": "equal",
        },
        {
            "field_option_id": text_field_2_field_options_2.id,
            "field_id": text_field.id,
            "type": "equal",
        },
    ]

    url = reverse("api:database:views:field_options", kwargs={"view_id": form_view.id})
    response = api_client.patch(
        url,
        {
            "field_options": {
                str(text_field_2.id): {
                    "show_when_matching_conditions": True,
                    "conditions": [
                        {
                            "id": condition.id,
                            "field": text_field.id,
                            "type": "not_equal",
                            "value": "test",
                        }
                    ],
                }
            }
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    assert FormViewFieldOptionsCondition.objects.count() == 2, list(
        FormViewFieldOptionsCondition.objects.values()
    )

    assert list(
        FormViewFieldOptionsCondition.objects.order_by("id").values(
            "field_option_id", "field_id", "type"
        )
    ) == [
        {
            "field_option_id": text_field_2_field_options.id,
            "field_id": text_field.id,
            "type": "not_equal",
        },
        {
            "field_option_id": text_field_2_field_options_2.id,
            "field_id": text_field.id,
            "type": "equal",
        },
    ]
