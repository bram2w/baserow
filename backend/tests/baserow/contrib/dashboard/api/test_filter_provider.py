from django.urls import reverse

import pytest

from baserow.contrib.dashboard.filters.service import DashboardFilterService


@pytest.mark.django_db
def test_sources_reference_one_dashboard_filter_without_table_bindings(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        authorized_user=user, application=dashboard
    )
    selection = DashboardFilterService().create_filter(
        user, dashboard.id, label="Country", mode="input"
    )
    headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
    widgets = []
    for country_field, rows, expected in [
        ("Country", [["France", 70], ["Belgium", 30]], "70"),
        ("Market", [["France", 12], ["Germany", 8]], "12"),
    ]:
        table, fields, _ = data_fixture.build_table(
            user=user,
            columns=[(country_field, "text"), ("Amount", "number")],
            rows=rows,
        )
        source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
            dashboard=dashboard,
            integration=integration,
            table=table,
            field=fields[1],
            aggregation_type="sum",
        )
        widget = data_fixture.create_summary_widget(
            dashboard=dashboard, data_source=source
        )
        response = api_client.patch(
            reverse(
                "api:dashboard:data_sources:item", kwargs={"data_source_id": source.id}
            ),
            {
                "type": "local_baserow_aggregate_rows",
                "filters": [
                    {
                        "field": fields[0].id,
                        "type": "equal",
                        "value": {
                            "formula": f"get('dashboard_filter.{selection.id}')",
                            "mode": "advanced",
                        },
                    }
                ],
            },
            format="json",
            **headers,
        )
        assert response.status_code == 200, response.json()
        widgets.append((widget, expected))

    unfiltered_source = (
        data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
            dashboard=dashboard,
            integration=integration,
            table=table,
            field=fields[1],
            aggregation_type="sum",
        )
    )
    widgets.append(
        (
            data_fixture.create_summary_widget(
                dashboard=dashboard, data_source=unfiltered_source
            ),
            "20",
        )
    )
    for widget, expected in widgets:
        response = api_client.post(
            reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
            {"filters": [{"filter_id": selection.id, "values": ["France"]}]},
            format="json",
            **headers,
        )
        assert response.status_code == 200, response.json()
        assert response.json() == {"result": expected}


@pytest.mark.django_db
def test_manual_options_have_independent_labels_and_values(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
    response = api_client.post(
        reverse("api:dashboard:filters:list", kwargs={"dashboard_id": dashboard.id}),
        {
            "label": "Country",
            "option_type": "manual",
            "options": [
                {"name": "France", "value": "FR"},
                {"name": "Belgium", "value": "BE"},
            ],
        },
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.json()
    saved = response.json()
    assert saved["options"] == [
        {"name": "France", "value": "FR"},
        {"name": "Belgium", "value": "BE"},
    ]
    assert "bindings" not in saved and "operator" not in saved
    response = api_client.post(
        reverse("api:dashboard:filters:options", kwargs={"filter_id": saved["id"]}),
        {"limit": 1, "selected": ["BE", "DE"]},
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "results": ["FR"],
        "labels": {"FR": "France", "BE": "Belgium"},
        "next": "FR",
        "available": ["BE"],
    }


@pytest.mark.django_db
def test_option_formulas_read_source_data_without_filtering_its_table(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        authorized_user=user, application=dashboard
    )
    table, fields, _ = data_fixture.build_table(
        user=user,
        columns=[("Country", "text"), ("Code", "text")],
        rows=[["France", "FR"], ["Belgium", "BE"]],
    )
    source = data_fixture.create_dashboard_data_source(
        dashboard=dashboard,
        service=data_fixture.create_local_baserow_list_rows_service(
            integration=integration, table=table
        ),
    )
    headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
    response = api_client.post(
        reverse("api:dashboard:filters:list", kwargs={"dashboard_id": dashboard.id}),
        {
            "label": "Country",
            "option_type": "formulas",
            "formula_name": {
                "formula": f"get('data_source.{source.id}.*.{fields[0].db_column}')",
                "mode": "advanced",
            },
            "formula_value": {
                "formula": f"get('data_source.{source.id}.*.{fields[1].db_column}')",
                "mode": "advanced",
            },
        },
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.json()
    response = api_client.post(
        reverse(
            "api:dashboard:filters:options",
            kwargs={"filter_id": response.json()["id"]},
        ),
        {"selected": ["BE"]},
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "results": ["FR", "BE"],
        "labels": {"FR": "France", "BE": "Belgium"},
        "next": None,
        "available": ["BE"],
    }
