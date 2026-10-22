from typing import Any, Dict

from baserow.core.utils import extract_allowed


class CoreExportSerializedStructure:
    # Explicitly defines the core fields necessary to create an Application.
    # This is needed by `DatabaseApplicationType.import_serialized` to prevent
    # additional data being  passed up to `ApplicationType.import_serialized`
    # when the `Application` is being created.
    fields = ["id", "name", "order", "type", "snapshot_from"]

    @classmethod
    def filter_application_fields(
        cls, serialized_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build a dictionary of values which we can pass to
        `ApplicationType.import_serialized`. We can't pass it `serialized_values`
        as it can contain keys which can't be dropped in the Application model.
        """

        return extract_allowed(serialized_values, cls.fields)

    @staticmethod
    def application(id, name, order, type):
        return {
            "id": id,
            "name": name,
            "order": order,
            "type": type,
        }
