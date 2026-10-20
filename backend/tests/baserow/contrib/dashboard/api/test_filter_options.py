from django.urls import reverse

import pytest

from baserow.contrib.dashboard.filters.service import DashboardFilterService
from baserow.core.formula.types import BaserowFormulaObject


@pytest.mark.django_db
def test_manual_options_search_pagination_and_availability(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)
    selection = DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Team",
        options=[
            {"name": "Équipe Design", "value": "design"},
            {"name": "Marketing", "value": "marketing"},
        ],
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
    first = api_client.post(url, {"limit": 1}, format="json", **headers).json()
    assert first["next"] == "design"
    second = api_client.post(
        url, {"after": first["next"]}, format="json", **headers
    ).json()
    assert second["results"] == ["marketing"]
    assert second["next"] is None


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
@pytest.mark.parametrize("invalid", ["deleted", "other_dashboard", "recursive"])
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
