from django.urls import reverse

import pytest

from baserow.contrib.dashboard.filters.service import DashboardFilterService
from baserow.core.formula.types import BaserowFormulaObject
from baserow_premium.integrations.local_baserow.models import (
    LocalBaserowTableServiceAggregationGroupBy,
    LocalBaserowTableServiceAggregationSeries,
)


@pytest.mark.django_db
def test_text_filter_is_applied_before_grouped_aggregation(
    api_client, premium_data_fixture
):
    fixture = premium_data_fixture
    user, token = fixture.create_user_and_token()
    dashboard = fixture.create_dashboard_application(user=user)
    integration = fixture.create_local_baserow_integration(
        application=dashboard, authorized_user=user
    )
    table, fields, _ = fixture.build_table(
        user=user,
        columns=[("Team", "text"), ("Region", "text"), ("Budget", "number")],
        rows=[
            ["Design", "Europe", 20],
            ["Design", "Europe", 30],
            ["Sales", "Europe", 70],
            ["Design", "Asia", 10],
        ],
    )
    source = fixture.create_dashboard_local_baserow_grouped_aggregate_rows_data_source(
        dashboard=dashboard, integration=integration, table=table
    )
    LocalBaserowTableServiceAggregationSeries.objects.create(
        service=source.service, field=fields[2], aggregation_type="sum", order=1
    )
    LocalBaserowTableServiceAggregationGroupBy.objects.create(
        service=source.service, field=fields[1], order=1
    )
    widget = fixture.create_chart_widget(dashboard=dashboard, data_source=source)
    config = DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Team",
    )
    fixture.create_local_baserow_table_service_filter(
        service=source.service,
        field=fields[0],
        type="equal",
        value=BaserowFormulaObject.create(f"get('dashboard_filter.{config.id}')"),
    )
    response = api_client.post(
        reverse("api:dashboard:widgets:dispatch", kwargs={"widget_id": widget.id}),
        {"filters": [{"filter_id": config.id, "values": ["Design"]}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert sorted(
        (row["Region"], row["Budget sum"]) for row in response.json()["results"]
    ) == [("Asia", 10), ("Europe", 50)]
