from unittest.mock import patch

from django.test.utils import override_settings
from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)


@pytest.mark.django_db
def test_get_public_builder_by_domain_name(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    builder_to = data_fixture.create_builder_application(workspace=None)
    page = data_fixture.create_builder_page(user=user, builder=builder_to)
    page2 = data_fixture.create_builder_page(user=user, builder=builder_to)

    domain = data_fixture.create_builder_custom_domain(
        domain_name="test.getbaserow.io", published_to=builder_to
    )

    url = reverse(
        "api:builder:domains:get_builder_by_domain_name",
        kwargs={"domain_name": "test.getbaserow.io"},
    )

    # Anonymous request
    response = api_client.get(
        url,
        format="json",
    )

    response_json = response.json()

    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "id": builder_to.id,
        "name": builder_to.name,
        "pages": [
            {"id": page.id, "name": page.name, "path": page.path, "path_params": []},
            {"id": page2.id, "name": page2.name, "path": page2.path, "path_params": []},
        ],
        "type": "builder",
        "theme": {
            "primary_color": "#5190efff",
            "secondary_color": "#0eaa42ff",
            "border_color": "#d7d8d9ff",
            "heading_1_font_size": 24,
            "heading_1_color": "#070810ff",
            "heading_2_font_size": 20,
            "heading_2_color": "#070810ff",
            "heading_3_font_size": 16,
            "heading_3_color": "#070810ff",
        },
        "user_sources": [],
    }

    # Even if I'm authenticated I should be able to see it.
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_get_builder_missing_domain_name(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    page2 = data_fixture.create_builder_page(builder=page.builder, user=user)

    domain = data_fixture.create_builder_custom_domain(
        domain_name="test.getbaserow.io", published_to=page.builder
    )

    url = reverse(
        "api:builder:domains:get_builder_by_domain_name",
        kwargs={"domain_name": "notexists.getbaserow.io"},
    )
    response = api_client.get(
        url,
        format="json",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_BUILDER_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_get_non_public_builder(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    page2 = data_fixture.create_builder_page(builder=page.builder, user=user)
    domain = data_fixture.create_builder_custom_domain(
        domain_name="test.getbaserow.io", builder=page.builder
    )

    url = reverse(
        "api:builder:domains:get_builder_by_domain_name",
        kwargs={"domain_name": "test.getbaserow.io"},
    )
    response = api_client.get(
        url,
        format="json",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_BUILDER_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_get_public_builder_by_id(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    page2 = data_fixture.create_builder_page(builder=page.builder, user=user)

    url = reverse(
        "api:builder:domains:get_builder_by_id",
        kwargs={"builder_id": page.builder.id},
    )

    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()

    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "id": page.builder.id,
        "name": page.builder.name,
        "pages": [
            {"id": page.id, "name": page.name, "path": page.path, "path_params": []},
            {"id": page2.id, "name": page2.name, "path": page2.path, "path_params": []},
        ],
        "type": "builder",
        "theme": {
            "primary_color": "#5190efff",
            "secondary_color": "#0eaa42ff",
            "border_color": "#d7d8d9ff",
            "heading_1_font_size": 24,
            "heading_1_color": "#070810ff",
            "heading_2_font_size": 20,
            "heading_2_color": "#070810ff",
            "heading_3_font_size": 16,
            "heading_3_color": "#070810ff",
        },
        "user_sources": [],
    }


@pytest.mark.django_db
def test_get_public_builder_by_id_other_user(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    other_user, other_token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    page2 = data_fixture.create_builder_page(builder=page.builder, user=user)

    url = reverse(
        "api:builder:domains:get_builder_by_id",
        kwargs={"builder_id": page.builder.id},
    )

    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {other_token}",
    )

    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db(transaction=True)
@patch("baserow.core.jobs.handler.run_async_job")
def test_publish_builder(mock_run_async_job, api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    builder_from = data_fixture.create_builder_application(user=user)
    page = data_fixture.create_builder_page(builder=builder_from, user=user)
    page2 = data_fixture.create_builder_page(builder=builder_from, user=user)

    domain = data_fixture.create_builder_custom_domain(
        domain_name="test.getbaserow.io", builder=builder_from
    )

    url = reverse(
        "api:builder:domains:publish",
        kwargs={"domain_id": domain.id},
    )
    response = api_client.post(
        url,
        {"domain_id": domain.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()

    assert response.status_code == HTTP_202_ACCEPTED

    mock_run_async_job.delay.assert_called_once()
    args = mock_run_async_job.delay.call_args
    assert args[0][0] == response_json["id"]


@pytest.mark.django_db
def test_get_elements_of_public_builder(api_client, data_fixture):
    user = data_fixture.create_user()
    builder_from = data_fixture.create_builder_application(user=user)
    builder_to = data_fixture.create_builder_application(user=user, workspace=None)
    page = data_fixture.create_builder_page(builder=builder_to, user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)
    element2 = data_fixture.create_builder_heading_element(page=page)
    element3 = data_fixture.create_builder_text_element(page=page)

    domain = data_fixture.create_builder_custom_domain(
        domain_name="test.getbaserow.io",
        published_to=page.builder,
        builder=builder_from,
    )

    url = reverse(
        "api:builder:domains:list_elements",
        kwargs={"page_id": page.id},
    )
    response = api_client.get(
        url,
        format="json",
    )

    response_json = response.json()

    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 3


@pytest.mark.django_db
def test_get_elements_of_public_builder_permission_denied(api_client, data_fixture):
    user = data_fixture.create_user()
    builder_from = data_fixture.create_builder_application(user=user)
    page = data_fixture.create_builder_page(builder=builder_from, user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)

    url = reverse(
        "api:builder:domains:list_elements",
        kwargs={"page_id": page.id},
    )
    response = api_client.get(
        url,
        format="json",
    )

    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_data_source_of_public_builder(api_client, data_fixture):
    user = data_fixture.create_user()
    builder_from = data_fixture.create_builder_application(user=user)
    builder_to = data_fixture.create_builder_application(user=user, workspace=None)
    page = data_fixture.create_builder_page(builder=builder_to, user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    domain = data_fixture.create_builder_custom_domain(
        domain_name="test.getbaserow.io",
        published_to=page.builder,
        builder=builder_from,
    )

    url = reverse(
        "api:builder:domains:list_data_sources",
        kwargs={"page_id": page.id},
    )
    response = api_client.get(
        url,
        format="json",
    )

    response_json = response.json()

    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 3


@pytest.mark.django_db
def test_get_data_source_of_public_builder_permission_denied(api_client, data_fixture):
    user = data_fixture.create_user()
    builder_from = data_fixture.create_builder_application(user=user)
    page = data_fixture.create_builder_page(builder=builder_from, user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    url = reverse(
        "api:builder:domains:list_data_sources",
        kwargs={"page_id": page.id},
    )
    response = api_client.get(
        url,
        format="json",
    )

    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_ask_public_builder_domain_exists(api_client, data_fixture):
    user = data_fixture.create_user()
    builder_from = data_fixture.create_builder_application(user=user)
    builder_to = data_fixture.create_builder_application(user=user, workspace=None)
    data_fixture.create_builder_custom_domain(
        domain_name="test.getbaserow.io",
        published_to=builder_to,
        builder=builder_from,
    )
    data_fixture.create_builder_custom_domain(
        domain_name="another-domain.com",
    )

    url = reverse("api:builder:domains:ask_exists")
    response = api_client.get(url)
    assert response.status_code == 404

    url = reverse("api:builder:domains:ask_exists") + "?domain="
    response = api_client.get(url)
    assert response.status_code == 404

    url = reverse("api:builder:domains:ask_exists") + "?domain=nothing"
    response = api_client.get(url)
    assert response.status_code == 404

    url = reverse("api:builder:domains:ask_exists") + "?domain=nothing.com"
    response = api_client.get(url)
    assert response.status_code == 404

    url = reverse("api:builder:domains:ask_exists") + "?domain=test2.getbaserow.io"
    response = api_client.get(url)
    assert response.status_code == 404

    url = reverse("api:builder:domains:ask_exists") + "?domain=another-domain.com"
    response = api_client.get(url)
    assert response.status_code == 404

    url = reverse("api:builder:domains:ask_exists") + "?domain=test.getbaserow.io"
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(
    PUBLIC_BACKEND_HOSTNAME="backend.localhost",
    PUBLIC_WEB_FRONTEND_HOSTNAME="web-frontend.localhost",
)
def test_ask_public_builder_domain_exists_with_public_backend_and_web_frontend_domains(
    api_client, data_fixture
):
    url = reverse("api:builder:domains:ask_exists") + "?domain=localhost"
    response = api_client.get(url)
    assert response.status_code == 404

    url = reverse("api:builder:domains:ask_exists") + "?domain=backend.localhost"
    response = api_client.get(url)
    assert response.status_code == 200

    url = reverse("api:builder:domains:ask_exists") + "?domain=web-frontend.localhost"
    response = api_client.get(url)
    assert response.status_code == 200
