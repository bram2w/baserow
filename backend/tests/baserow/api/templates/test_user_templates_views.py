from datetime import datetime, timezone

from django.db import connection
from django.db.models import F
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

from baserow.core.models import Template, TemplateCategory
from baserow.core.user_templates.job_types import CreateUserTemplateJobType
from baserow.core.user_templates.models import CreateUserTemplateJob

pytestmark = pytest.mark.django_db

LIST_URL = reverse("api:templates:list")


def create_own_template(data_fixture, user, **kwargs):
    kwargs.setdefault("icon", "iconoir-view-grid")
    return data_fixture.create_user_template(user=user, **kwargs)


def publish(template):
    Template.objects.filter(id=template.id).update(public_revision_id=F("id"))
    template.refresh_from_db()
    return template


def list_templates(api_client, token=None, **params):
    params.setdefault("view", "flat")
    headers = {"HTTP_AUTHORIZATION": f"JWT {token}"} if token else {}
    return api_client.get(LIST_URL, params, **headers)


def list_own_templates(api_client, token, **params):
    return list_templates(api_client, token, type="user", owned="true", **params)


def test_list_own_templates(api_client, data_fixture):
    # Which templates are listed and in which order is tested on the handler.
    user, token = data_fixture.create_user_and_token()
    category_1 = data_fixture.create_template_category(name="Cat 1")
    category_2 = data_fixture.create_template_category(name="Cat 2")
    with freeze_time("2026-10-01 10:00"):
        template = create_own_template(
            data_fixture,
            user,
            name="Older",
            description="Plans projects.",
            categories=[category_2, category_1],
            open_application=1,
            review_state="rejected",
            reject_reason="Not a template.",
        )

    response = list_own_templates(api_client, token)

    assert response.status_code == HTTP_200_OK
    assert response.json()["results"] == [
        {
            "id": template.id,
            "type": "user",
            "name": "Older",
            "slug": template.slug,
            "description": "Plans projects.",
            "icon": "iconoir-view-grid",
            "keywords": "",
            "workspace_id": template.workspace_id,
            "is_default": False,
            "open_application": 1,
            "categories": [
                {"id": category_1.id, "name": "Cat 1"},
                {"id": category_2.id, "name": "Cat 2"},
            ],
            "state": "rejected",
            "reason": "Not a template.",
            "created_on": "2026-10-01T10:00:00Z",
            "updated_on": "2026-10-01T10:00:00Z",
        }
    ]


def test_list_templates_lists_what_the_actor_can_open(api_client, data_fixture):
    owner, owner_token = data_fixture.create_user_and_token()
    _, stranger_token = data_fixture.create_user_and_token()
    official = data_fixture.create_template()
    public = publish(create_own_template(data_fixture, owner))
    private = create_own_template(data_fixture, owner)
    blocked = publish(
        create_own_template(data_fixture, owner, blocked_at=django_timezone.now())
    )

    def listed_ids(token):
        response = list_templates(api_client, token)
        assert response.status_code == HTTP_200_OK
        return {t["id"] for t in response.json()["results"]}

    assert listed_ids(None) == {official.id, public.id}
    assert listed_ids(stranger_token) == {official.id, public.id}
    assert listed_ids(owner_token) == {official.id, public.id, private.id, blocked.id}


def test_list_templates_hides_the_state_from_others(api_client, data_fixture):
    owner, owner_token = data_fixture.create_user_and_token()
    _, stranger_token = data_fixture.create_user_and_token()
    publish(create_own_template(data_fixture, owner))
    data_fixture.create_template()

    for token in [None, stranger_token]:
        response = list_templates(api_client, token)
        assert response.status_code == HTTP_200_OK
        results = response.json()["results"]
        assert len(results) == 2
        assert {(t["state"], t["reason"]) for t in results} == {(None, None)}

    response = list_templates(api_client, owner_token, type="user")
    assert response.json()["results"][0]["state"] == "public"


def test_list_templates_filters_by_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    official = data_fixture.create_template()
    # Templates created before the type existed are official.
    legacy = data_fixture.create_template(type=None)
    own = create_own_template(data_fixture, user)

    response = list_templates(api_client, token, type="official")
    assert {t["id"] for t in response.json()["results"]} == {official.id, legacy.id}
    assert {t["type"] for t in response.json()["results"]} == {"official"}

    response = list_templates(api_client, token, type="user")
    assert [t["id"] for t in response.json()["results"]] == [own.id]


def test_list_templates_filters_by_owner(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    data_fixture.create_template()
    publish(data_fixture.create_user_template())
    own = create_own_template(data_fixture, user)

    response = list_templates(api_client, token, owned="true")
    assert [t["id"] for t in response.json()["results"]] == [own.id]

    response = list_templates(api_client, owned="true")
    assert response.status_code == HTTP_200_OK
    assert response.json()["count"] == 0


def test_list_own_templates_paging(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    templates = [
        create_own_template(data_fixture, user, name=f"Template {index}")
        for index in range(25)
    ]
    expected_ids = [template.id for template in reversed(templates)]

    response = list_own_templates(api_client, token)
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 25
    assert [t["id"] for t in response_json["results"]] == expected_ids[:20]
    assert response_json["next"] is not None

    response = list_own_templates(api_client, token, limit=20, offset=20)
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert [t["id"] for t in response_json["results"]] == expected_ids[20:]
    assert response_json["next"] is None


def test_list_own_templates_limit_is_capped(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    category = data_fixture.create_template_category()
    for _ in range(101):
        create_own_template(data_fixture, user, category=category)

    response = list_own_templates(api_client, token, limit=1000)

    assert response.status_code == HTTP_200_OK
    assert response.json()["count"] == 101
    assert len(response.json()["results"]) == 100


def test_list_own_templates_search(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    by_name = create_own_template(data_fixture, user, name="CRM", description="")
    by_description = create_own_template(
        data_fixture, user, name="Sales", description="A small crm for a shop."
    )
    create_own_template(data_fixture, user, name="Tasks", description="To do.")
    publish(data_fixture.create_user_template(name="CRM of another user"))

    response = list_own_templates(api_client, token, search="crm")

    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 2
    assert {t["id"] for t in response_json["results"]} == {
        by_name.id,
        by_description.id,
    }

    response = list_own_templates(api_client, token, search="")

    assert response.status_code == HTTP_200_OK
    assert response.json()["count"] == 3


def test_list_own_templates_query_count_is_constant(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    categories = [data_fixture.create_template_category() for _ in range(2)]
    create_own_template(data_fixture, user, categories=list(categories))

    with CaptureQueriesContext(connection) as one_template:
        response = list_own_templates(api_client, token)
        assert response.status_code == HTTP_200_OK

    for _ in range(3):
        create_own_template(data_fixture, user, categories=list(categories))

    with CaptureQueriesContext(connection) as four_templates:
        response = list_own_templates(api_client, token)
        assert response.status_code == HTTP_200_OK
        assert response.json()["count"] == 4

    assert len(four_templates.captured_queries) == len(one_template.captured_queries)


def test_list_templates_with_flag_off(api_client, data_fixture, settings):
    settings.FEATURE_FLAGS = []
    user, token = data_fixture.create_user_and_token()
    official = data_fixture.create_template()
    create_own_template(data_fixture, user)

    response = list_templates(api_client, token)

    assert response.status_code == HTTP_200_OK
    assert [t["id"] for t in response.json()["results"]] == [official.id]


def test_list_templates_with_an_invalid_parameter(api_client, data_fixture):
    response = list_templates(api_client, type="other")

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"


def test_list_template_categories_ignores_the_parameters(api_client, data_fixture):
    # The deprecated categories never read the parameters, so old clients sending
    # any keep working.
    category = data_fixture.create_template_category(name="Official")
    data_fixture.create_template(category=category)

    response = list_templates(api_client, view="tree", type="other", search="")

    assert response.status_code == HTTP_200_OK
    assert [c["id"] for c in response.json()] == [category.id]


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


@pytest.mark.parametrize(
    "overrides,field",
    [
        ({"name": None}, "name"),
        ({"name": ""}, "name"),
        ({"name": "x" * 65}, "name"),
        ({"description": "x" * 81}, "description"),
        ({"icon": "iconoir-" + "a" * 30}, "icon"),
        ({"icon": None}, "icon"),
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


@pytest.mark.parametrize("unknown", [True, False])
def test_create_user_template_job_with_invalid_categories(
    api_client, data_fixture, unknown
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    category = TemplateCategory.objects.create(name="Cat")
    category_ids = [category.id, category.id + 1000] if unknown else []

    response = create_job(
        api_client, token, workspace, [database], category_ids=category_ids
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_INVALID_TEMPLATE_CATEGORY"
    assert not CreateUserTemplateJob.objects.exists()


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


def get_as_anonymous_stranger_and_owner(api_client, tokens, url):
    return tuple(
        api_client.get(url, **headers).status_code
        for headers in [{}]
        + [{"HTTP_AUTHORIZATION": f"JWT {token}"} for token in tokens]
    )


@pytest.mark.parametrize("user_templates_enabled", [True, False])
def test_open_user_template(api_client, data_fixture, settings, user_templates_enabled):
    if not user_templates_enabled:
        settings.FEATURE_FLAGS = []
    _, stranger_token = data_fixture.create_user_and_token()
    owner, owner_token = data_fixture.create_user_and_token()
    tokens = [stranger_token, owner_token]
    official = data_fixture.create_template()
    user_template = data_fixture.create_user_template(user=owner)
    marked = data_fixture.create_user_template(
        user=owner, marked_for_deletion_at=datetime(2026, 10, 1, tzinfo=timezone.utc)
    )

    # Anonymous, a stranger and the owner.
    for template, opens in [
        (official, (True, True, True)),
        (user_template, (False, False, user_templates_enabled)),
        (marked, (False, False, False)),
    ]:
        grid = create_template_with_rows(data_fixture, template)

        statuses = get_as_anonymous_stranger_and_owner(
            api_client,
            tokens,
            reverse("api:templates:item", kwargs={"slug": template.slug}),
        )
        assert statuses == tuple(
            HTTP_200_OK if allowed else HTTP_404_NOT_FOUND for allowed in opens
        )

        # Not a member, so a signed in user gets a 400 when it's refused.
        refused = (HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST, HTTP_400_BAD_REQUEST)
        statuses = get_as_anonymous_stranger_and_owner(
            api_client,
            tokens,
            reverse(
                "api:applications:list",
                kwargs={"workspace_id": template.workspace_id},
            ),
        )
        assert statuses == tuple(
            HTTP_200_OK if allowed else status
            for allowed, status in zip(opens, refused)
        )

        statuses = get_as_anonymous_stranger_and_owner(
            api_client,
            tokens,
            reverse("api:database:views:grid:list", kwargs={"view_id": grid.id}),
        )
        assert statuses == tuple(
            HTTP_200_OK if allowed else status
            for allowed, status in zip(opens, refused)
        )


def test_template_by_slug_has_its_type(api_client, data_fixture):
    owner, token = data_fixture.create_user_and_token()
    official = data_fixture.create_template()
    legacy = data_fixture.create_template(type=None)
    user_template = data_fixture.create_user_template(user=owner)

    for template, template_type in [
        (official, "official"),
        (legacy, "official"),
        (user_template, "user"),
    ]:
        response = api_client.get(
            reverse("api:templates:item", kwargs={"slug": template.slug}),
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

        assert response.status_code == HTTP_200_OK
        assert response.json()["type"] == template_type
