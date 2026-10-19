from django.urls import reverse

import pytest

from baserow.core.action.handler import ActionHandler
from baserow.core.action.scopes import ApplicationActionScopeType


@pytest.mark.django_db
def test_create_filter_and_read_its_configuration(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    url = reverse("api:dashboard:filters:list", kwargs={"dashboard_id": dashboard.id})
    headers = {
        "HTTP_AUTHORIZATION": f"JWT {token}",
        "HTTP_CLIENTSESSIONID": "filters-session",
    }

    response = api_client.post(
        url,
        {
            "label": "Team",
            "type": "text",
            "operator": "equal",
            "mode": "dropdown",
            "multiple": True,
        },
        format="json",
        **headers,
    )

    assert response.status_code == 200
    created = response.json()
    assert created["label"] == "Team"
    assert created["dashboard_id"] == dashboard.id
    assert created["operator"] == "equal"
    assert created["multiple"] is True
    assert "value" not in created
    assert api_client.get(url, **headers).json() == [created]


@pytest.mark.django_db
def test_filter_configuration_can_be_updated_deleted_and_undone(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token(session_id="filters-session")
    dashboard = data_fixture.create_dashboard_application(user=user)
    url = reverse("api:dashboard:filters:list", kwargs={"dashboard_id": dashboard.id})
    headers = {
        "HTTP_AUTHORIZATION": f"JWT {token}",
        "HTTP_CLIENTSESSIONID": "filters-session",
    }
    created = api_client.post(url, {"label": "Team"}, format="json", **headers).json()
    item_url = reverse(
        "api:dashboard:filters:item", kwargs={"filter_id": created["id"]}
    )

    response = api_client.patch(
        item_url,
        {"label": "Department", "operator": "contains"},
        format="json",
        **headers,
    )
    assert response.status_code == 200
    assert response.json()["label"] == "Department"
    assert response.json()["operator"] == "contains"
    assert api_client.delete(item_url, **headers).status_code == 204
    assert api_client.get(url, **headers).json() == []

    scope = [ApplicationActionScopeType.value(dashboard.id)]
    ActionHandler.undo(user, scope, "filters-session")
    restored = api_client.get(url, **headers).json()
    assert restored[0]["label"] == "Department"
    ActionHandler.undo(user, scope, "filters-session")
    assert api_client.get(url, **headers).json() == [created]
    ActionHandler.undo(user, scope, "filters-session")
    assert api_client.get(url, **headers).json() == []
    ActionHandler.redo(user, scope, "filters-session")
    assert api_client.get(url, **headers).json() == [created]


@pytest.mark.django_db
def test_filters_are_private_to_the_dashboard_workspace(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token()
    other_dashboard = data_fixture.create_dashboard_application()
    url = reverse(
        "api:dashboard:filters:list", kwargs={"dashboard_id": other_dashboard.id}
    )
    headers = {
        "HTTP_AUTHORIZATION": f"JWT {token}",
        "HTTP_CLIENTSESSIONID": "filters-session",
    }
    assert api_client.get(url, **headers).status_code == 401
    assert (
        api_client.post(url, {"label": "Team"}, format="json", **headers).status_code
        == 401
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "values", [{"type": "number"}, {"operator": "gt"}, {"mode": "select"}]
)
def test_filter_rejects_unsupported_configuration(api_client, data_fixture, values):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    url = reverse("api:dashboard:filters:list", kwargs={"dashboard_id": dashboard.id})
    response = api_client.post(
        url,
        {"label": "Team", **values},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_bind_filter_to_widget_and_preserve_binding_through_undo(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard, table=table
    )
    widget = data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    url = reverse("api:dashboard:filters:list", kwargs={"dashboard_id": dashboard.id})
    headers = {
        "HTTP_AUTHORIZATION": f"JWT {token}",
        "HTTP_CLIENTSESSIONID": "bindings-session",
    }
    created = api_client.post(url, {"label": "Team"}, format="json", **headers).json()
    item_url = reverse(
        "api:dashboard:filters:item", kwargs={"filter_id": created["id"]}
    )
    bindings = [{"widget_id": widget.id, "field_id": field.id}]
    response = api_client.patch(
        item_url, {"bindings": bindings}, format="json", **headers
    )
    assert response.status_code == 200
    assert response.json()["bindings"] == bindings
    assert api_client.delete(item_url, **headers).status_code == 204
    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(dashboard.id)], "bindings-session"
    )
    assert api_client.get(url, **headers).json()[0]["bindings"] == bindings
    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(dashboard.id)], "bindings-session"
    )
    assert api_client.get(url, **headers).json()[0]["bindings"] == []


@pytest.mark.django_db
@pytest.mark.parametrize("invalid", ["widget", "table", "type", "duplicate"])
def test_filter_rejects_invalid_bindings(api_client, data_fixture, invalid):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    table = data_fixture.create_database_table(user=user)
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard, table=table
    )
    widget = data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    field = data_fixture.create_text_field(table=table)
    if invalid == "widget":
        widget = data_fixture.create_summary_widget()
    elif invalid == "table":
        field = data_fixture.create_text_field()
    elif invalid == "type":
        field = data_fixture.create_number_field(table=table)
    bindings = [{"widget_id": widget.id, "field_id": field.id}]
    if invalid == "duplicate":
        bindings *= 2
    url = reverse("api:dashboard:filters:list", kwargs={"dashboard_id": dashboard.id})
    response = api_client.post(
        url,
        {"label": "Team", "bindings": bindings},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 400
