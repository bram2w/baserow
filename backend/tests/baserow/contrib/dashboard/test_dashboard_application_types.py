import json

import pytest

from baserow.contrib.dashboard.application_types import DashboardApplicationType
from baserow.core.registries import ImportExportConfig


@pytest.mark.django_db
def test_dashboard_export_serialized(data_fixture):
    user = data_fixture.create_user()
    dashboard = data_fixture.create_dashboard_application(
        name="Dashboard 1", description="Description 1", user=user
    )
    serialized = DashboardApplicationType().export_serialized(
        dashboard, ImportExportConfig(include_permission_data=True)
    )
    serialized = json.loads(json.dumps(serialized))

    assert serialized == {
        "id": dashboard.id,
        "name": dashboard.name,
        "description": "Description 1",
        "order": dashboard.order,
        "type": "dashboard",
    }


@pytest.mark.django_db
def test_dashboard_import_serialized(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    id_mapping = {}
    serialized = {
        "id": "999",
        "name": "Dashboard 1",
        "description": "Description 1",
        "order": 99,
        "type": "dashboard",
    }

    dashboard = DashboardApplicationType().import_serialized(
        workspace,
        serialized,
        ImportExportConfig(include_permission_data=True),
        id_mapping,
    )

    dashboard.refresh_from_db()

    assert dashboard.name == "Dashboard 1"
    assert dashboard.description == "Description 1"
    assert dashboard.order == 99
