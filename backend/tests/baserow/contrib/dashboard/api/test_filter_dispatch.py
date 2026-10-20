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
        ("starts_with", ["Des"], "1"),
        ("contains_word", ["Design"], "1"),
        ("doesnt_contain_word", ["Design"], "20"),
        ("length_is_lower_than", ["7"], "17"),
        ("empty", ["true"], "16"),
        ("not_empty", ["true"], "5"),
        ("empty", [], "21"),
        ("not_empty", [], "21"),
    ],
)
def test_dashboard_control_uses_builder_filter_operators(
    api_client, filtered_dashboard, operator, values, expected
):
    user, token, widget, selection, condition = filtered_dashboard
    DashboardFilterService().update_filter(user, selection.id, operator=operator)
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": [{"filter_id": selection.id, "values": values}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": expected}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "operator", ["equal", "not_equal", "contains", "contains_not", "empty", "not_empty"]
)
def test_deleting_dashboard_filter_restores_unfiltered_widget_data(
    api_client, filtered_dashboard, operator
):
    user, token, widget, selection, condition = filtered_dashboard
    DashboardFilterService().update_filter(user, selection.id, operator=operator)
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


@pytest.mark.django_db
def test_dashboard_operator_controls_multiple_values(api_client, filtered_dashboard):
    _, token, widget, selection, _ = filtered_dashboard
    headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
    item_url = reverse("api:dashboard:filters:item", kwargs={"filter_id": selection.id})
    response = api_client.patch(
        item_url,
        {"mode": "dropdown", "multiple": True, "operator": "equal"},
        format="json",
        **headers,
    )
    assert response.status_code == 200
    dispatch_url = reverse(
        "api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}
    )
    data = {"filters": [{"filter_id": selection.id, "values": ["Design", "Marketing"]}]}
    assert api_client.post(dispatch_url, data, format="json", **headers).json() == {
        "result": "5"
    }
    response = api_client.patch(
        item_url, {"operator": "not_equal"}, format="json", **headers
    )
    assert response.status_code == 200
    assert api_client.post(dispatch_url, data, format="json", **headers).json() == {
        "result": "16"
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "operator,values,expected",
    [
        ("equal", ["Design", "Marketing"], "5"),
        ("not_equal", ["Design", "Marketing"], "16"),
        ("contains", ["DES", "MARK"], "5"),
        ("contains_not", ["DES", "MARK"], "16"),
        ("contains_word", ["Design", "Marketing"], "5"),
        ("doesnt_contain_word", ["Design", "Marketing"], "16"),
        ("starts_with", ["Des", "Mar"], "5"),
        ("length_is_lower_than", ["2", "7"], "17"),
        ("not_equal", [], "21"),
        ("not_equal", [" ", ""], "21"),
        ("equal", ["Design,Marketing"], None),
    ],
)
def test_multiple_dashboard_values_are_individual_operands(
    api_client, filtered_dashboard, operator, values, expected
):
    user, token, widget, selection, _ = filtered_dashboard
    DashboardFilterService().update_filter(
        user, selection.id, mode="dropdown", multiple=True, operator=operator
    )
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": [{"filter_id": selection.id, "values": values}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": expected}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "expression",
    [
        "get('dashboard_filter.{id}')",
        ' GET("dashboard_filter.{id}") ',
        "get( 'dashboard_filter.{id}' )",
        "get(('dashboard_filter.{id}'))",
        "(get('dashboard_filter.{id}'))",
        "get('dashboard_filter.{id}.*')",
    ],
)
def test_dashboard_operator_overrides_only_direct_references(
    api_client, filtered_dashboard, expression
):
    user, token, widget, selection, condition = filtered_dashboard
    DashboardFilterService().update_filter(
        user, selection.id, mode="dropdown", multiple=True, operator="not_equal"
    )
    condition.value = BaserowFormulaObject.create(expression.format(id=selection.id))
    condition.save()
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": [{"filter_id": selection.id, "values": ["Design"]}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "20"}


@pytest.mark.django_db
def test_calculated_conditions_keep_their_own_operator(api_client, filtered_dashboard):
    user, token, widget, selection, condition = filtered_dashboard
    DashboardFilterService().update_filter(user, selection.id, operator="not_equal")
    condition.value = BaserowFormulaObject.create(
        f"concat(get('dashboard_filter.{selection.id}'), '')"
    )
    condition.save()
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": [{"filter_id": selection.id, "values": ["Design"]}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "1"}
