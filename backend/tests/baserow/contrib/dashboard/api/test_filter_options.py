from django.urls import reverse

import pytest

from baserow.contrib.dashboard.filters.service import DashboardFilterService


@pytest.mark.django_db
def test_options_union_respects_sources_and_checks_availability_outside_search_and_page(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        authorized_user=user, application=dashboard
    )
    bindings = []
    for rows in [
        [["Design", 1], ["Marketing", 1], ["Hidden", 0], ["", 1], ["   ", 1]],
        [["Marketing", 1], ["Sales", 1], ["design", 1], [" Design ", 1]],
    ]:
        table, fields, _ = data_fixture.build_table(
            user=user, columns=[("Team", "text"), ("Visible", "number")], rows=rows
        )
        view = data_fixture.create_grid_view(table=table)
        data_fixture.create_view_filter(
            view=view, field=fields[1], type="equal", value="1"
        )
        source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
            dashboard=dashboard,
            integration=integration,
            table=table,
            view=view,
            field=fields[1],
            aggregation_type="sum",
        )
        widget = data_fixture.create_summary_widget(
            dashboard=dashboard, data_source=source
        )
        bindings.append({"widget_id": widget.id, "field_id": fields[0].id})
    config = DashboardFilterService().create_filter(
        user, dashboard.id, label="Team", bindings=bindings
    )
    url = reverse("api:dashboard:filters:options", kwargs={"filter_id": config.id})
    headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
    response = api_client.post(
        url,
        {"limit": 2, "selected": ["Sales", "Hidden", "Deleted"]},
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "results": [" Design ", "Design"],
        "next": "Design",
        "available": ["Sales"],
    }
    response = api_client.post(
        url,
        {"limit": 2, "after": "Design", "search": "m", "selected": ["Sales", "Hidden"]},
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "results": ["Marketing"],
        "next": None,
        "available": ["Sales"],
    }
    response = api_client.post(
        url, {"limit": 2, "after": "Design"}, format="json", **headers
    )
    assert response.json()["results"] == ["Marketing", "Sales"]
    assert response.json()["next"] == "Sales"
    response = api_client.post(
        url, {"limit": 2, "after": "Sales"}, format="json", **headers
    )
    assert response.json()["results"] == ["design"]
    assert response.json()["next"] is None


@pytest.mark.django_db
def test_options_do_not_expose_another_workspace(api_client, data_fixture):
    user = data_fixture.create_user()
    dashboard = data_fixture.create_dashboard_application(user=user)
    config = DashboardFilterService().create_filter(user, dashboard.id, label="Team")
    _, token = data_fixture.create_user_and_token()
    response = api_client.post(
        reverse("api:dashboard:filters:options", kwargs={"filter_id": config.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_options_search_handles_unicode_case(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        authorized_user=user, application=dashboard
    )
    table, fields, _ = data_fixture.build_table(
        user=user,
        columns=[("Team", "text"), ("Count", "number")],
        rows=[["Équipe", 1], ["équipe", 1]],
    )
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard,
        integration=integration,
        table=table,
        field=fields[1],
        aggregation_type="sum",
    )
    widget = data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    config = DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Team",
        bindings=[{"widget_id": widget.id, "field_id": fields[0].id}],
    )
    response = api_client.post(
        reverse("api:dashboard:filters:options", kwargs={"filter_id": config.id}),
        {"search": "équipe"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json()["results"] == ["Équipe", "équipe"]
