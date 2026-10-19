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
        bindings=[{"widget_id": widget.id, "field_id": field.id}],
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
    assert list(imported_filter.bindings.values("widget_id", "field_id")) == [
        {"widget_id": imported_widget.id, "field_id": field.id}
    ]
    assert imported_widget.id != widget.id

    replacement = data_fixture.create_text_field(table=table)
    mapped = application_type.import_serialized(
        dashboard.workspace,
        deepcopy(exported),
        config,
        {"database_fields": {field.id: replacement.id}},
    )
    mapped_filter = DashboardFilterService().get_filters(user, mapped.id)[0]
    assert mapped_filter.bindings.get().field_id == replacement.id
