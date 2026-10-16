from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.shortcuts import reverse
from django.test.utils import CaptureQueriesContext
from django.utils import timezone as django_timezone

import pytest
from freezegun import freeze_time
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from baserow.api.templates.urls import RESERVED_TEMPLATE_SLUGS
from baserow.core.models import TemplateCategory
from baserow.core.user_templates.job_types import CreateUserTemplateJobType
from baserow.core.user_templates.models import CreateUserTemplateJob

OWN_URL = reverse("api:templates:own")


def create_own_template(data_fixture, user, **kwargs):
    kwargs.setdefault("icon", "iconoir-view-grid")
    return data_fixture.create_user_template(user=user, **kwargs)


@pytest.mark.django_db
def test_list_own_templates(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    category_1 = data_fixture.create_template_category(name="Cat 1")
    category_2 = data_fixture.create_template_category(name="Cat 2")
    with freeze_time("2026-10-01 10:00"):
        older = create_own_template(
            data_fixture,
            user,
            name="Older",
            description="Plans projects.",
            categories=[category_2, category_1],
            open_application=1,
        )
    with freeze_time("2026-10-02 10:00"):
        newer = create_own_template(data_fixture, user, name="Newer")
        # Same `updated_on`, so the higher id comes first.
        newest_id = create_own_template(data_fixture, user, name="Newest id")

    # Revisions, templates of others and templates marked for deletion are left out.
    data_fixture.create_user_template_revision(older)
    data_fixture.create_user_template()
    create_own_template(
        data_fixture, user, marked_for_deletion_at=django_timezone.now()
    )
    data_fixture.create_template()

    response = api_client.get(OWN_URL, HTTP_AUTHORIZATION=f"JWT {token}")

    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 3
    assert [t["id"] for t in response_json["results"]] == [
        newest_id.id,
        newer.id,
        older.id,
    ]
    assert response_json["results"][2] == {
        "id": older.id,
        "type": "user",
        "name": "Older",
        "slug": older.slug,
        "description": "Plans projects.",
        "icon": "iconoir-view-grid",
        "workspace_id": older.workspace_id,
        "open_application": 1,
        "categories": [
            {"id": category_1.id, "name": "Cat 1"},
            {"id": category_2.id, "name": "Cat 2"},
        ],
        "state": "private",
        "reason": None,
        "created_on": "2026-10-01T10:00:00Z",
        "updated_on": "2026-10-01T10:00:00Z",
    }


@pytest.mark.django_db
def test_list_own_templates_shows_state_and_reason(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    create_own_template(
        data_fixture,
        user,
        review_state="rejected",
        reject_reason="Not a template.",
    )

    response = api_client.get(OWN_URL, HTTP_AUTHORIZATION=f"JWT {token}")

    assert response.status_code == HTTP_200_OK
    result = response.json()["results"][0]
    assert result["state"] == "rejected"
    assert result["reason"] == "Not a template."


@pytest.mark.django_db
def test_list_own_templates_paging(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    templates = [
        create_own_template(data_fixture, user, name=f"Template {index}")
        for index in range(25)
    ]
    expected_ids = [template.id for template in reversed(templates)]

    response = api_client.get(OWN_URL, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 25
    assert [t["id"] for t in response_json["results"]] == expected_ids[:20]
    assert response_json["next"] is not None

    response = api_client.get(
        f"{OWN_URL}?limit=20&offset=20", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert [t["id"] for t in response_json["results"]] == expected_ids[20:]
    assert response_json["next"] is None


@pytest.mark.django_db
def test_list_own_templates_limit_is_capped(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    category = data_fixture.create_template_category()
    for _ in range(101):
        create_own_template(data_fixture, user, category=category)

    response = api_client.get(
        f"{OWN_URL}?limit=1000", HTTP_AUTHORIZATION=f"JWT {token}"
    )

    assert response.status_code == HTTP_200_OK
    assert response.json()["count"] == 101
    assert len(response.json()["results"]) == 100


@pytest.mark.django_db
def test_list_own_templates_search(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    by_name = create_own_template(data_fixture, user, name="CRM", description="")
    by_description = create_own_template(
        data_fixture, user, name="Sales", description="A small crm for a shop."
    )
    create_own_template(data_fixture, user, name="Tasks", description="To do.")
    data_fixture.create_user_template(name="CRM of another user")

    response = api_client.get(
        f"{OWN_URL}?search=crm", HTTP_AUTHORIZATION=f"JWT {token}"
    )

    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 2
    assert {t["id"] for t in response_json["results"]} == {
        by_name.id,
        by_description.id,
    }


@pytest.mark.django_db
def test_list_own_templates_query_count_is_constant(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    categories = [data_fixture.create_template_category() for _ in range(2)]
    create_own_template(data_fixture, user, categories=list(categories))

    with CaptureQueriesContext(connection) as one_template:
        response = api_client.get(OWN_URL, HTTP_AUTHORIZATION=f"JWT {token}")
        assert response.status_code == HTTP_200_OK

    for _ in range(3):
        create_own_template(data_fixture, user, categories=list(categories))

    with CaptureQueriesContext(connection) as four_templates:
        response = api_client.get(OWN_URL, HTTP_AUTHORIZATION=f"JWT {token}")
        assert response.status_code == HTTP_200_OK
        assert response.json()["count"] == 4

    assert len(four_templates.captured_queries) == len(one_template.captured_queries)


@pytest.mark.django_db
def test_list_own_templates_requires_authentication(api_client, data_fixture):
    data_fixture.create_user_template()

    response = api_client.get(OWN_URL)

    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_list_own_templates_with_flag_off(api_client, data_fixture, settings):
    settings.FEATURE_FLAGS = []
    user, token = data_fixture.create_user_and_token()
    create_own_template(data_fixture, user)

    response = api_client.get(OWN_URL, HTTP_AUTHORIZATION=f"JWT {token}")

    assert response.status_code == HTTP_403_FORBIDDEN
    assert response.json()["error"] == "ERROR_FEATURE_DISABLED"


@pytest.mark.django_db
def test_own_templates_route_is_not_shadowed_by_the_slug_route(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    # Even a template with that slug can't take the route over.
    data_fixture.create_template(slug="own")

    assert OWN_URL == reverse("api:templates:item", kwargs={"slug": "own"})
    response = api_client.get(OWN_URL, HTTP_AUTHORIZATION=f"JWT {token}")

    assert response.status_code == HTTP_200_OK
    assert response.json()["count"] == 0


def test_no_official_template_slug_is_reserved():
    stems = {
        path.stem for path in Path(settings.APPLICATION_TEMPLATES_DIR).glob("*.json")
    }

    assert stems
    assert stems.isdisjoint(RESERVED_TEMPLATE_SLUGS)


def create_job(api_client, token, workspace, applications, **overrides):
    category = TemplateCategory.objects.create(name="Cat")
    data = {
        "type": CreateUserTemplateJobType.type,
        "workspace_id": workspace.id,
        "application_ids": [application.id for application in applications],
        "name": "My template",
        "description": "What it does",
        "icon": "iconoir-view-grid",
        "category_ids": [category.id],
        **overrides,
    }
    data = {key: value for key, value in data.items() if value is not None}
    return api_client.post(
        reverse("api:jobs:list"),
        data,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "overrides,field",
    [
        ({"name": None}, "name"),
        ({"name": ""}, "name"),
        ({"name": "x" * 65}, "name"),
        ({"description": "x" * 81}, "description"),
        ({"icon": "iconoir-not-allowed"}, "icon"),
        ({"icon": None}, "icon"),
        ({"category_ids": []}, "category_ids"),
        ({"category_ids": None}, "category_ids"),
        ({"application_ids": []}, "application_ids"),
        ({"application_ids": None}, "application_ids"),
    ],
)
def test_create_user_template_job_request_validation(
    api_client, data_fixture, overrides, field
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)

    response = create_job(api_client, token, workspace, [database], **overrides)

    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert list(response_json["detail"]) == [field]
    assert not CreateUserTemplateJob.objects.exists()


@pytest.mark.django_db
def test_create_user_template_job_with_unknown_category(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    category = TemplateCategory.objects.create(name="Cat")

    response = create_job(
        api_client,
        token,
        workspace,
        [database],
        category_ids=[category.id, category.id + 1000],
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_INVALID_TEMPLATE_CATEGORY"
    assert not CreateUserTemplateJob.objects.exists()


@pytest.mark.django_db
def test_create_user_template_job_accepts_valid_request(
    api_client, data_fixture, use_tmp_media_root
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)

    response = create_job(
        api_client, token, workspace, [database], description=None, name="x" * 64
    )

    assert response.status_code == HTTP_200_OK, response.json()
    response_json = response.json()
    assert response_json["type"] == CreateUserTemplateJobType.type
    assert "template" in response_json
    # The request is sent back, so that the wizard can show a running job again.
    assert {
        key: response_json[key]
        for key in [
            "workspace_id",
            "application_ids",
            "name",
            "description",
            "icon",
            "category_ids",
        ]
    } == {
        "workspace_id": workspace.id,
        "application_ids": [database.id],
        "name": "x" * 64,
        "description": "",
        "icon": "iconoir-view-grid",
        "category_ids": [TemplateCategory.objects.get().id],
    }
    job = CreateUserTemplateJob.objects.get(id=response_json["id"])
    assert job.description == ""
    assert job.name == "x" * 64


@pytest.mark.django_db
def test_create_user_template_job_with_flag_off(api_client, data_fixture, settings):
    settings.FEATURE_FLAGS = []
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)

    response = create_job(api_client, token, workspace, [database])

    assert response.status_code == HTTP_403_FORBIDDEN
    assert response.json()["error"] == "ERROR_FEATURE_DISABLED"
    assert not CreateUserTemplateJob.objects.exists()


def create_template_with_rows(data_fixture, template):
    database = data_fixture.create_database_application(workspace=template.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table, primary=True)
    table.get_model().objects.create(**{field.db_column: "Row"})
    return data_fixture.create_grid_view(table=table)


def get_as_anonymous_and_stranger(api_client, token, url):
    return (
        api_client.get(url).status_code,
        api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}").status_code,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("user_templates_enabled", [True, False])
def test_open_user_template(api_client, data_fixture, settings, user_templates_enabled):
    if not user_templates_enabled:
        settings.FEATURE_FLAGS = []
    _, token = data_fixture.create_user_and_token()
    official = data_fixture.create_template()
    user_template = data_fixture.create_user_template()
    marked = data_fixture.create_user_template(
        marked_for_deletion_at=datetime(2026, 10, 1, tzinfo=timezone.utc)
    )

    for template, opens in [
        (official, True),
        (user_template, user_templates_enabled),
        (marked, False),
    ]:
        grid = create_template_with_rows(data_fixture, template)

        statuses = get_as_anonymous_and_stranger(
            api_client,
            token,
            reverse("api:templates:item", kwargs={"slug": template.slug}),
        )
        assert statuses == (
            (HTTP_200_OK, HTTP_200_OK) if opens else (HTTP_404_NOT_FOUND,) * 2
        )

        statuses = get_as_anonymous_and_stranger(
            api_client,
            token,
            reverse(
                "api:applications:list",
                kwargs={"workspace_id": template.workspace_id},
            ),
        )
        assert statuses == (
            (HTTP_200_OK, HTTP_200_OK)
            if opens
            else (HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST)
        )

        url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
        response = api_client.get(url)
        if opens:
            assert response.status_code == HTTP_200_OK
            assert response.json()["count"] == 1
            response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
            assert response.status_code == HTTP_200_OK
        else:
            assert response.status_code == HTTP_401_UNAUTHORIZED
            response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
            assert response.status_code == HTTP_400_BAD_REQUEST
