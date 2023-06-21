from baserow.contrib.database.table.operations import (
    CreateRowDatabaseTableOperationType,
)
from baserow.contrib.database.views.exceptions import ViewDoesNotExist
from baserow.contrib.database.views.operations import (
    CreateAndUsePersonalViewOperationType,
    CreatePublicViewOperationType,
)
from baserow.contrib.database.views.registries import ViewOwnershipType
from baserow.core.handler import CoreHandler


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

    def before_form_view_submitted(self, form, request):
        """
        Ensure that a personal form view can only be submitted if the creator still
        has permissions to create rows. This check can raise for example when a
        user makes a personal form view when they are an editor or higher on a
        table, but then they get lowered to a viewer on the table but again try
        to use the same form.
        """

        CoreHandler().check_permissions(
            form.created_by,
            CreateRowDatabaseTableOperationType.type,
            form.table.database.workspace,
            form.table,
        )

    def before_public_view_accessed(self, view):
        """
        Ensure that if a user who made and publicly shared a personal view
        tries to use the link after they have lost permission to make public views
        on that table it no longer works.
        """

        if not CoreHandler().check_permissions(
            view.created_by,
            CreatePublicViewOperationType.type,
            view.table.database.workspace,
            view.table,
            raise_permission_exceptions=False,
        ):
            raise ViewDoesNotExist("The view does not exist.")

    def get_operation_to_check_to_create_view(self):
        """
        :return: An OperationType that the user must have to create a view of this
            ownership type
        """

        return CreateAndUsePersonalViewOperationType
