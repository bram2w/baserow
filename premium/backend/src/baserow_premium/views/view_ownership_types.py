from baserow.contrib.database.views.registries import ViewOwnershipType


class PersonalViewOwnershipType(ViewOwnershipType):
    """
    Represents views that are intended only for a specific user.
    """

    type = "personal"

    def can_import_view(self, serialized_values, id_mapping):
        email = serialized_values.get("created_by", None)
        return id_mapping["created_by"].get(email, None) is not None

    def should_broadcast_signal_to(self, view):
        if view.created_by is None:
            return "", None

        return "users", [view.created_by_id]
