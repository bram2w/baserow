from django.urls import reverse

import pytest

from baserow.contrib.dashboard.filters.service import DashboardFilterService
from baserow.core.formula.types import BaserowFormulaObject


@pytest.mark.django_db
def test_table_options_search_pagination_and_availability(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    table, fields, _ = data_fixture.build_table(
        user=user,
        columns=[("Label", "text"), ("Value", "text")],
        rows=[
            ["Équipe Design", "design"],
            ["Marketing", "marketing"],
            ["Duplicate", "design"],
            ["Empty", ""],
        ],
    )
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard, table=table
    )
    data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    selection = DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Team",
        formula_name=BaserowFormulaObject.create(
            f"get('table.{table.id}.*.{fields[0].db_column}')"
        ),
        formula_value=BaserowFormulaObject.create(
            f"get('table.{table.id}.*.{fields[1].db_column}')"
        ),
    )
    url = reverse("api:dashboard:filters:options", kwargs={"filter_id": selection.id})
    headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
    result = api_client.post(
        url,
        {"search": "ÉQUIPE", "selected": ["marketing", "sales"]},
        format="json",
        **headers,
    ).json()
    assert result["results"] == ["design"]
    assert result["available"] == ["marketing"]
    assert result["labels"] == {"design": "Équipe Design", "marketing": "Marketing"}
    first = api_client.post(url, {"limit": 1}, format="json", **headers).json()
    assert first["next"] == "design"
    assert first["labels"] == {"design": "Équipe Design"}
    second = api_client.post(
        url, {"after": first["next"]}, format="json", **headers
    ).json()
    assert second["results"] == ["marketing"]
    assert second["labels"] == {"marketing": "Marketing"}
    assert second["next"] is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rows, expected",
    [
        ([["France", None], ["Belgique", 2]], {"2": "Belgique"}),
        ([[None, 1], ["Belgique", 2]], {"1": "1", "2": "Belgique"}),
    ],
)
def test_table_options_keep_labels_and_values_aligned_with_empty_fields(
    api_client, data_fixture, rows, expected
):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    table, fields, _ = data_fixture.build_table(
        user=user, columns=[("Label", "text"), ("Value", "number")], rows=rows
    )
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard, table=table
    )
    data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    selection = DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Country",
        formula_name=BaserowFormulaObject.create(
            f"get('table.{table.id}.*.{fields[0].db_column}')"
        ),
        formula_value=BaserowFormulaObject.create(
            f"get('table.{table.id}.*.{fields[1].db_column}')"
        ),
    )
    response = api_client.post(
        reverse("api:dashboard:filters:options", kwargs={"filter_id": selection.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json()["labels"] == expected


@pytest.mark.django_db
def test_options_require_dashboard_permission(api_client, data_fixture):
    user = data_fixture.create_user()
    _, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    selection = DashboardFilterService().create_filter(user, dashboard.id, label="Team")
    response = api_client.post(
        reverse("api:dashboard:filters:options", kwargs={"filter_id": selection.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid", ["deleted", "other_dashboard", "missing_service", "recursive"]
)
def test_options_report_broken_source_instead_of_empty_choices(
    api_client, data_fixture, invalid
):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    table, fields, _ = data_fixture.build_table(
        user=user, columns=[("Team", "text")], rows=[["Design"]]
    )
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard, table=table
    )
    selection = DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Team",
        option_type="formulas",
        formula_value=BaserowFormulaObject.create(
            f"get('data_source.{source.id}.result')"
        ),
    )
    if invalid == "deleted":
        source.delete()
    elif invalid == "missing_service":
        source.service = None
        source.save()
    elif invalid == "other_dashboard":
        source.dashboard = data_fixture.create_dashboard_application(
            user=user, workspace=dashboard.workspace
        )
        source.save()
    else:
        data_fixture.create_local_baserow_table_service_filter(
            service=source.service,
            field=fields[0],
            type="equal",
            value=BaserowFormulaObject.create(f"get('data_source.{source.id}.result')"),
        )
    response = api_client.post(
        reverse("api:dashboard:filters:options", kwargs={"filter_id": selection.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 400, response.json()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid", ["unused_table", "deleted_widget", "deleted_field", "deleted_table"]
)
def test_table_options_reject_unavailable_or_unrelated_records(
    api_client, data_fixture, invalid
):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    table, fields, _ = data_fixture.build_table(
        user=user, columns=[("Country", "text")], rows=[["France"]]
    )
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard, table=table
    )
    widget = data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    selection = DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Country",
        formula_value=BaserowFormulaObject.create(
            f"get('table.{table.id}.*.{fields[0].db_column}')"
        ),
    )
    if invalid == "unused_table":
        source.service.table = data_fixture.create_database_table(user=user)
        source.service.save()
    elif invalid == "deleted_widget":
        widget.trashed = True
        widget.save()
    elif invalid == "deleted_field":
        fields[0].trashed = True
        fields[0].save()
    else:
        table.trashed = True
        table.save()
    response = api_client.post(
        reverse("api:dashboard:filters:options", kwargs={"filter_id": selection.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 400, response.json()


@pytest.mark.django_db
def test_table_options_require_access_to_the_underlying_database(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    table, fields, _ = data_fixture.build_table(
        columns=[("Country", "text")], rows=[["France"]]
    )
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard, table=table
    )
    data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    selection = DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Country",
        formula_value=BaserowFormulaObject.create(
            f"get('table.{table.id}.*.{fields[0].db_column}')"
        ),
    )
    response = api_client.post(
        reverse("api:dashboard:filters:options", kwargs={"filter_id": selection.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 401, response.json()


@pytest.mark.django_db
def test_table_options_include_rows_beyond_the_list_service_limit(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    table, fields, _ = data_fixture.build_table(
        user=user,
        columns=[("Country", "text")],
        rows=[["France"]] * 250 + [["Belgique"]],
    )
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard, table=table
    )
    first = data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    first.trashed = True
    first.save()
    selection = DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Country",
        formula_value=BaserowFormulaObject.create(
            f"get('table.{table.id}.*.{fields[0].db_column}')"
        ),
    )
    response = api_client.post(
        reverse("api:dashboard:filters:options", kwargs={"filter_id": selection.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json()["results"] == ["France", "Belgique"]
