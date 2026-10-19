from copy import deepcopy

import pytest

from baserow.contrib.dashboard.application_types import DashboardApplicationType
from baserow.contrib.dashboard.filters.service import DashboardFilterService
from baserow.contrib.dashboard.widgets.service import WidgetService
from baserow.core.registries import ImportExportConfig


@pytest.mark.django_db
def test_dashboard_export_import_preserves_filters_and_remaps_bindings(data_fixture):
    user = data_fixture.create_user()
    dashboard = data_fixture.create_dashboard_application(user=user)
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    source = data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard, table=table
    )
    widget = data_fixture.create_summary_widget(dashboard=dashboard, data_source=source)
    DashboardFilterService().create_filter(
        user,
        dashboard.id,
        label="Team",
        bindings=[{"table_id": table.id, "field_id": field.id}],
    )
    application_type = DashboardApplicationType()
    config = ImportExportConfig(include_permission_data=True, is_duplicate=True)
    exported = application_type.export_serialized(dashboard, config)
    assert exported["filters"][0]["label"] == "Team"

    mapping = {}
    imported = application_type.import_serialized(
        dashboard.workspace, deepcopy(exported), config, mapping
    )
    imported_widget = WidgetService().get_widgets(user, imported.id)[0]
    imported_filter = DashboardFilterService().get_filters(user, imported.id)[0]
    assert imported_filter.label == "Team"
    assert list(imported_filter.bindings.values("table_id", "field_id")) == [
        {"table_id": table.id, "field_id": field.id}
    ]
    assert imported_widget.id != widget.id

    replacement_table = data_fixture.create_database_table(user=user)
    replacement = data_fixture.create_text_field(table=replacement_table)
    mapped = application_type.import_serialized(
        dashboard.workspace,
        deepcopy(exported),
        config,
        {
            "database_tables": {table.id: replacement_table.id},
            "database_fields": {field.id: replacement.id},
        },
    )
    assert application_type.export_serialized(mapped, config)["filters"][0][
        "bindings"
    ] == [{"table_id": replacement_table.id, "field_id": replacement.id}]
