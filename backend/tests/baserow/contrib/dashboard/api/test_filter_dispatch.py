from django.urls import reverse

import pytest

from baserow.contrib.dashboard.filters.service import DashboardFilterService
from baserow.contrib.dashboard.widgets.service import WidgetService
from baserow.core.action.handler import ActionHandler
from baserow.core.action.scopes import ApplicationActionScopeType
from baserow.core.formula.types import BaserowFormulaObject
from baserow.core.handler import CoreHandler


@pytest.fixture
def filtered_dashboard(data_fixture):
    user, token = data_fixture.create_user_and_token(session_id="filter-dispatch")
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
@pytest.mark.parametrize("operator", ["equal", "not_equal", "contains", "contains_not"])
def test_deleting_dashboard_filter_restores_unfiltered_widget_data(
    api_client, filtered_dashboard, operator
):
    _, token, widget, selection, condition = filtered_dashboard
    condition.type = operator
    condition.save()
    headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
    response = api_client.delete(
        reverse("api:dashboard:filters:item", kwargs={"filter_id": selection.id}),
        **headers,
    )
    assert response.status_code == 204
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": []},
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "21"}


@pytest.mark.django_db
def test_source_cannot_read_a_filter_from_another_dashboard(
    api_client, data_fixture, filtered_dashboard
):
    user, token, widget, selection, condition = filtered_dashboard
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
def test_deleted_multiple_filter_ignores_stale_client_values(
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
    DashboardFilterService().delete_filter(user, selection.id)
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": [{"filter_id": selection.id, "values": ["Design", "Marketing"]}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "21"}


@pytest.mark.django_db
@pytest.mark.parametrize("path_suffix", ["", ".1"])
def test_copy_after_deleting_filter_keeps_widget_data_available(
    api_client, filtered_dashboard, path_suffix
):
    user, token, widget, selection, condition = filtered_dashboard
    condition.value = BaserowFormulaObject.create(
        f"get('dashboard_filter.{selection.id}{path_suffix}')"
    )
    condition.save()
    headers = {
        "HTTP_AUTHORIZATION": f"JWT {token}",
        "HTTP_CLIENTSESSIONID": "filter-dispatch",
    }
    response = api_client.delete(
        reverse("api:dashboard:filters:item", kwargs={"filter_id": selection.id}),
        **headers,
    )
    assert response.status_code == 204
    copied = CoreHandler().duplicate_application(user, widget.dashboard)
    copied_widget = WidgetService().get_widgets(user, copied.id)[0]
    dispatch_url = reverse(
        "api:dashboard:widgets:dispatch", kwargs={"widget_id": copied_widget.id}
    )
    response = api_client.post(dispatch_url, {"filters": []}, format="json", **headers)
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "21"}

    # Restoring the original control must not reconnect the copied source to it.
    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(widget.dashboard_id)], "filter-dispatch"
    )
    response = api_client.post(
        dispatch_url,
        {"filters": [{"filter_id": selection.id, "values": ["Design", "Marketing"]}]},
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "21"}


@pytest.mark.django_db
def test_deleting_one_filter_preserves_other_conditions_and_can_be_undone(
    api_client, data_fixture, filtered_dashboard
):
    user, token, widget, selection, condition = filtered_dashboard
    other = DashboardFilterService().create_filter(
        user, widget.dashboard_id, label="Other team", mode="input"
    )
    data_fixture.create_local_baserow_table_service_filter(
        service=condition.service,
        field=condition.field,
        type="equal",
        value=BaserowFormulaObject.create(f"get('dashboard_filter.{other.id}')"),
    )
    headers = {
        "HTTP_AUTHORIZATION": f"JWT {token}",
        "HTTP_CLIENTSESSIONID": "filter-dispatch",
    }
    deleted = api_client.delete(
        reverse("api:dashboard:filters:item", kwargs={"filter_id": selection.id}),
        **headers,
    )
    assert deleted.status_code == 204
    dispatch_url = reverse(
        "api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}
    )
    response = api_client.post(
        dispatch_url,
        {"filters": [{"filter_id": other.id, "values": ["Marketing"]}]},
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "4"}

    scope = [ApplicationActionScopeType.value(widget.dashboard_id)]
    ActionHandler.undo(user, scope, "filter-dispatch")
    response = api_client.post(
        dispatch_url,
        {"filters": [{"filter_id": selection.id, "values": ["Design"]}]},
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "1"}

    ActionHandler.redo(user, scope, "filter-dispatch")
    response = api_client.post(dispatch_url, {"filters": []}, format="json", **headers)
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "21"}


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
