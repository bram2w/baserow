from django.urls import reverse

import pytest

from baserow.contrib.dashboard.filters.service import DashboardFilterService
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler


@pytest.fixture
def filtered_dashboard(data_fixture):
    user, token = data_fixture.create_user_and_token()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[("Team", "text"), ("Amount", "number")],
        rows=[
            ["Design", 1],
            ["design", 2],
            ["Marketing", 4],
            [" Design ", 8],
            ["", 16],
        ],
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
    filter_config = DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Team",
        multiple=True,
        bindings=[{"widget_id": widget.id, "field_id": fields[0].id}],
    )
    return user, token, widget, filter_config, table, fields, rows


@pytest.mark.django_db
@pytest.mark.parametrize(
    "operator,mode,values,expected",
    [
        ("equal", "dropdown", ["Design"], "1"),
        ("equal", "dropdown", [" Design "], "8"),
        ("equal", "input", [" Design "], "1"),
        ("equal", "input", ["  "], "31"),
        ("equal", "dropdown", ["Design", "Marketing"], "5"),
        ("not_equal", "dropdown", ["Design", "Marketing"], "26"),
        ("contains", "dropdown", ["DESIGN"], "11"),
        ("contains_not", "dropdown", ["DESIGN"], "20"),
        ("equal", "dropdown", [], "31"),
        ("equal", "dropdown", ["Design"] + [f"Other {i}" for i in range(100)], "1"),
    ],
)
def test_dispatch_applies_saved_filter_before_aggregation(
    api_client, filtered_dashboard, operator, mode, values, expected
):
    user, token, widget, filter_config, *_ = filtered_dashboard
    DashboardFilterService().update_filter(
        user, filter_config.id, operator=operator, mode=mode
    )
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": [{"filter_id": filter_config.id, "values": values}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": expected}


@pytest.mark.django_db
def test_filter_is_scoped_to_widget_even_when_source_is_shared(
    api_client, data_fixture, filtered_dashboard
):
    user, token, widget, filter_config, *_ = filtered_dashboard
    unbound = data_fixture.create_summary_widget(
        dashboard=widget.dashboard, data_source=widget.data_source
    )
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": unbound.id}),
        {"filters": [{"filter_id": filter_config.id, "values": ["Design"]}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "31"}


@pytest.mark.django_db
def test_broken_binding_fails_but_deleted_filter_is_ignored(
    api_client, filtered_dashboard
):
    user, token, widget, filter_config, _, fields, _ = filtered_dashboard
    fields[0].trashed = True
    fields[0].save()
    url = reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id})
    headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
    response = api_client.post(url, {}, format="json", **headers)
    assert response.status_code == 400
    DashboardFilterService().delete_filter(user, filter_config.id)
    response = api_client.post(
        url,
        {"filters": [{"filter_id": filter_config.id, "values": ["Design"]}]},
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "31"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_kind", ["single_select", "formula_select", "formula_text"]
)
@pytest.mark.parametrize(
    "operator,expected",
    [("equal", "1"), ("not_equal", "6"), ("contains", "3"), ("contains_not", "4")],
)
def test_filter_compares_select_labels_and_scalar_formulas(
    api_client, data_fixture, filtered_dashboard, field_kind, operator, expected
):
    user, token, widget, filter_config, table, fields, _ = filtered_dashboard
    field = fields[0]
    if field_kind != "formula_text":
        field = data_fixture.create_single_select_field(table=table, name="Select team")
        design = data_fixture.create_select_option(
            field=field, value="Design", color="blue"
        )
        lower = data_fixture.create_select_option(
            field=field, value="design", color="red"
        )
        model = table.get_model()
        model.objects.all().delete()
        RowHandler().create_rows(
            user,
            table,
            [
                {field.db_column: design.id, fields[1].db_column: 1},
                {field.db_column: lower.id, fields[1].db_column: 2},
                {fields[1].db_column: 4},
            ],
        )
    else:
        model = table.get_model()
        model.objects.all().delete()
        RowHandler().create_rows(
            user,
            table,
            [
                {field.db_column: "Design", fields[1].db_column: 1},
                {field.db_column: "design", fields[1].db_column: 2},
                {fields[1].db_column: 4},
            ],
        )
    if field_kind.startswith("formula"):
        field = FieldHandler().create_field(
            user,
            table,
            "formula",
            name="Team formula",
            formula=f"field('{field.name}')",
        )
    DashboardFilterService().update_filter(
        user,
        filter_config.id,
        operator=operator,
        bindings=[{"widget_id": widget.id, "field_id": field.id}],
    )
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": [{"filter_id": filter_config.id, "values": ["Design"]}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": expected}


@pytest.mark.django_db
def test_filters_intersect_with_each_other_and_saved_view_and_source_filters(
    api_client, data_fixture, filtered_dashboard
):
    user, token, widget, filter_config, table, fields, _ = filtered_dashboard
    view = data_fixture.create_grid_view(table=table)
    data_fixture.create_view_filter(
        view=view, field=fields[1], type="higher_than", value="1"
    )
    service = widget.data_source.service.specific
    service.view = view
    service.save()
    data_fixture.create_local_baserow_table_service_filter(
        service=service, field=fields[1], type="lower_than", value="10"
    )
    other = DashboardFilterService().create_filter(
        user,
        widget.dashboard_id,
        label="Contains",
        operator="contains",
        mode="input",
        bindings=[{"widget_id": widget.id, "field_id": fields[0].id}],
    )
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {
            "filters": [
                {
                    "filter_id": filter_config.id,
                    "values": ["Design", "design", "Marketing"],
                },
                {"filter_id": other.id, "values": ["design"]},
            ]
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {"result": "2"}
