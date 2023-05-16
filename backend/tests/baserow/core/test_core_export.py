from baserow.contrib.database.application_types import DatabaseApplicationType
from baserow.core.export_serialized import CoreExportSerializedStructure
from baserow.core.models import Snapshot

DATABASE_TYPE = DatabaseApplicationType.type


def test_core_serialized_structure_filter_application_fields():
    snapshot_from = Snapshot()
    assert CoreExportSerializedStructure.filter_application_fields(
        {
            "id": 1,
            "name": "Staff",
            "order": 0,
            "type": DATABASE_TYPE,
            "snapshot_from": snapshot_from,
            "tables": [],
            "role_assignments": [
                {
                    "subject_id": 1,
                    "subject_type_id": 82,
                    "role_id": 1,
                }
            ],
        }
    ) == {
        "id": 1,
        "name": "Staff",
        "order": 0,
        "type": DATABASE_TYPE,
        "snapshot_from": snapshot_from,
    }


def test_core_serialized_structure_application():
    assert CoreExportSerializedStructure.application(1, "Staff", 0, DATABASE_TYPE) == {
        "id": 1,
        "name": "Staff",
        "order": 0,
        "type": DATABASE_TYPE,
    }
