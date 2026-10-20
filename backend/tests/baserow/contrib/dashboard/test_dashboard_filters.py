from copy import deepcopy

import pytest

from baserow.contrib.dashboard.application_types import DashboardApplicationType
from baserow.contrib.dashboard.filters.service import DashboardFilterService
from baserow.contrib.dashboard.widgets.service import WidgetService
from baserow.core.formula.types import BaserowFormulaObject
from baserow.core.registries import ImportExportConfig


@pytest.mark.django_db
@pytest.mark.parametrize("copy_table", [False, True])
def test_dashboard_copy_remaps_filter_and_source_formulas(data_fixture, copy_table):
    user = data_fixture.create_user()
    dashboard = data_fixture.create_dashboard_application(user=user)
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard, table=table
    )
    widget = data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    selection = DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Team",
        formula_name=BaserowFormulaObject.create(
            f"get('table.{table.id}.*.{field.db_column}')"
        ),
        formula_value=BaserowFormulaObject.create(
            f"get('table.{table.id}.*.{field.db_column}')"
        ),
    )
    data_fixture.create_local_baserow_table_service_filter(
        service=source.service,
        field=field,
        type="equal",
        value=BaserowFormulaObject.create(f"get('dashboard_filter.{selection.id}')"),
    )
    application_type = DashboardApplicationType()
    config = ImportExportConfig(include_permission_data=True, is_duplicate=True)
    exported = application_type.export_serialized(dashboard, config)
    assert "bindings" not in exported["filters"][0]
    mapping = {}
    expected_table, expected_field = table, field
    if copy_table:
        expected_table = data_fixture.create_database_table(user=user)
        expected_field = data_fixture.create_text_field(table=expected_table)
        mapping = {
            "database_tables": {table.id: expected_table.id},
            "database_fields": {field.id: expected_field.id},
        }
    imported = application_type.import_serialized(
        dashboard.workspace, deepcopy(exported), config, mapping
    )
    copied_widget = WidgetService().get_widgets(user, imported.id)[0]
    copied_filter = DashboardFilterService().get_filters(user, imported.id)[0]
    assert copied_widget.id != widget.id
    assert (
        copied_filter.formula_name["formula"]
        == f"get('table.{expected_table.id}.*.{expected_field.db_column}')"
    )
    assert (
        copied_widget.data_source.service.specific.service_filters.get().value[
            "formula"
        ]
        == f"get('dashboard_filter.{copied_filter.id}')"
    )
