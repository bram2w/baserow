from django.db import connection
from django.shortcuts import reverse
from django.test.utils import CaptureQueriesContext

import pytest
from rest_framework.status import HTTP_200_OK

from baserow.contrib.builder.models import Builder


@pytest.mark.django_db
def test_list_builder_applications_theme_config_block_created_number_of_queries(
    api_client, data_fixture, django_assert_num_queries
):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    workspace = data_fixture.create_workspace(user=user)
    data_fixture.create_builder_application(workspace=workspace, order=1)
    data_fixture.create_builder_application(workspace=workspace, order=2)

    url = reverse("api:applications:list", kwargs={"workspace_id": workspace.id})

    with CaptureQueriesContext(connection) as queries_request_1:
        response = api_client.get(
            url,
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == HTTP_200_OK

    with CaptureQueriesContext(connection) as queries_request_2:
        response = api_client.get(
            url,
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == HTTP_200_OK

    # The first request executed more queries because the `MainThemeConfigBlockType`
    # entries had to be automatically created.
    assert len(queries_request_2.captured_queries) < len(
        queries_request_1.captured_queries
    )


@pytest.mark.django_db
def test_list_builder_applications_equal_number_of_queries_n_builders(
    api_client, data_fixture, bypass_check_permissions
):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    workspace = data_fixture.create_workspace(user=user)

    url = reverse("api:applications:list", kwargs={"workspace_id": workspace.id})

    # Making first call to make sure that the settings object is created so we can
    # accurately measure the queries later on.
    api_client.get(
        url,
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    data_fixture.create_builder_application(workspace=workspace, order=1)
    data_fixture.create_builder_application(workspace=workspace, order=2)

    # Force the `MainThemeConfigBlockType` to be created.
    [builder.mainthemeconfigblock for builder in Builder.objects.all()]

    with CaptureQueriesContext(connection) as queries_request_1:
        response = api_client.get(
            url,
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == HTTP_200_OK

    # Force the `MainThemeConfigBlockType` to be created.
    data_fixture.create_builder_application(workspace=workspace, order=2)
    [builder.mainthemeconfigblock for builder in Builder.objects.all()]

    with CaptureQueriesContext(connection) as queries_request_2:
        response = api_client.get(
            url,
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == HTTP_200_OK

    # The number of queries should not increase because another builder application
    # is added, with its own theme.

    assert (
        len(queries_request_1.captured_queries)
        # The -2 queries are expected because that's another a
        # savepoint + release savepoint. This is unrelated to the builder application
        # specific code.
        == len(queries_request_2.captured_queries) - 2
    )


@pytest.mark.django_db
def test_list_builder_applications_theme(
    api_client, data_fixture, django_assert_num_queries
):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    workspace = data_fixture.create_workspace(user=user)
    application_1 = data_fixture.create_builder_application(
        workspace=workspace, order=1
    )
    data_fixture.create_builder_application(workspace=workspace, order=2)

    application_1.mainthemeconfigblock.primary_color = "#ccccccff"
    application_1.mainthemeconfigblock.save()

    url = reverse("api:applications:list", kwargs={"workspace_id": workspace.id})

    response = api_client.get(
        url,
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json[0]["theme"] == {
        "primary_color": "#ccccccff",
        "secondary_color": "#0eaa42ff",
        "border_color": "#d7d8d9ff",
        "heading_1_font_size": 24,
        "heading_1_color": "#070810ff",
        "heading_2_font_size": 20,
        "heading_2_color": "#070810ff",
        "heading_3_font_size": 16,
        "heading_3_color": "#070810ff",
    }
    assert response_json[1]["theme"] == {
        "primary_color": "#5190efff",
        "secondary_color": "#0eaa42ff",
        "border_color": "#d7d8d9ff",
        "heading_1_font_size": 24,
        "heading_1_color": "#070810ff",
        "heading_2_font_size": 20,
        "heading_2_color": "#070810ff",
        "heading_3_font_size": 16,
        "heading_3_color": "#070810ff",
    }
