from baserow.contrib.database.views.registries import ViewOwnershipType


class CollaborativeViewOwnershipType(ViewOwnershipType):
    """
    Represents views that are shared between all users that can access
    a specific table.
    """

    type = "collaborative"
