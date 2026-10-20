from django.urls import reverse

import pytest

from baserow.contrib.dashboard.filters.service import DashboardFilterService
from baserow.core.formula.types import BaserowFormulaObject


@pytest.fixture
def filtered_dashboard(data_fixture):
    user, token = data_fixture.create_user_and_token()
    table, fields, _ = data_fixture.build_table(
        user=user,
        columns=[("Team", "text"), ("Amount", "number")],
        rows=[["Design", 1], ["Marketing", 4], ["", 16]],
    )
    dashboard = data_fixture.create_dashboard_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        authorized_user=user, application=dashboard
    )
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard,
        integration=integration,
        table=table,
        field=fields[1],
        aggregation_type="sum",
    )
    widget = data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    selection = DashboardFilterService().create_filter(
        user, dashboard.id, label="Team", mode="input"
    )
    condition = data_fixture.create_local_baserow_table_service_filter(
        service=source.service,
        field=fields[0],
        type="equal",
        value=BaserowFormulaObject.create(f"get('dashboard_filter.{selection.id}')"),
    )
    return user, token, widget, selection, condition


@pytest.mark.django_db
@pytest.mark.parametrize(
    "operator,values,expected",
    [
        ("equal", ["Design"], "1"),
        ("equal", [" Design "], "1"),
        ("equal", ["  "], "21"),
        ("equal", [], "21"),
        ("not_equal", ["Design"], "20"),
        ("contains", ["DESIGN"], "1"),
        ("contains_not", ["DESIGN"], "20"),
    ],
)
def test_source_condition_uses_builder_filter_semantics(
    api_client, filtered_dashboard, operator, values, expected
):
    _, token, widget, selection, condition = filtered_dashboard
    condition.type = operator
    condition.save()
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": [{"filter_id": selection.id, "values": values}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": expected}


@pytest.mark.django_db
@pytest.mark.parametrize("invalid", ["deleted", "other_dashboard"])
def test_source_cannot_read_an_unavailable_filter(
    api_client, data_fixture, filtered_dashboard, invalid
):
    user, token, widget, selection, condition = filtered_dashboard
    if invalid == "deleted":
        DashboardFilterService().delete_filter(user, selection.id)
    else:
        other = data_fixture.create_dashboard_application(
            user=user, workspace=widget.dashboard.workspace
        )
        selection.dashboard = other
        selection.save()
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": [{"filter_id": selection.id, "values": ["Design"]}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 400, response.json()


@pytest.mark.django_db
def test_multiple_values_are_available_to_source_formulas(
    api_client, filtered_dashboard
):
    user, token, widget, selection, condition = filtered_dashboard
    DashboardFilterService().update_filter(
        user, selection.id, mode="dropdown", multiple=True
    )
    condition.value = BaserowFormulaObject.create(
        f"get('dashboard_filter.{selection.id}.1')"
    )
    condition.save()
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": [{"filter_id": selection.id, "values": ["Design", "Marketing"]}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "4"}


@pytest.mark.django_db
def test_widgets_sharing_a_source_share_its_filter_conditions(
    api_client, data_fixture, filtered_dashboard
):
    _, token, widget, selection, _ = filtered_dashboard
    shared = data_fixture.create_summary_widget(
        dashboard=widget.dashboard, data_source=widget.data_source
    )
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": shared.id}),
        {"filters": [{"filter_id": selection.id, "values": ["Design"]}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200
    assert response.json() == {"result": "1"}
