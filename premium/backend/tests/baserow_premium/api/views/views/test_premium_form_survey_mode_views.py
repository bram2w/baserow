from django.shortcuts import reverse
from django.test.utils import override_settings

import pytest
from rest_framework.status import HTTP_200_OK

from baserow.contrib.database.views.models import FormView


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_form_view_survey(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {
            "type": "form",
            "name": "Test Survey",
            "mode": "survey",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json["slug"]) == 43
    assert response_json["type"] == "form"
    assert response_json["name"] == "Test Survey"
    assert response_json["mode"] == "survey"

    form = FormView.objects.all()[0]
    assert response_json["id"] == form.id
    assert response_json["name"] == form.name
    assert response_json["mode"] == form.mode


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_update_form_view_survey(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)
    view = premium_data_fixture.create_form_view(table=table)

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.patch(
        url,
        {
            "name": "Test Survey",
            "mode": "survey",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["name"] == "Test Survey"
    assert response_json["mode"] == "survey"

    form = FormView.objects.all()[0]
    assert form.name == "Test Survey"
    assert form.mode == "survey"
