from django.db import transaction

from baserow_premium.admin.workspaces.exceptions import CannotDeleteATemplateGroupError
from baserow_premium.api.admin.views import AdminListingView
from baserow_premium.api.admin.workspaces.errors import (
    ERROR_CANNOT_DELETE_A_TEMPLATE_GROUP,
)
from baserow_premium.api.admin.workspaces.views import (
    WorkspaceAdminView,
    WorkspacesAdminView,
)
from baserow_premium.compat.api.conf import (
    GROUP_ADMIN_DEPRECATION_PREFIXES as DEPRECATION_PREFIXES,
)
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from baserow.api.decorators import map_exceptions
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST
from baserow.api.schemas import get_error_schema
from baserow.core.exceptions import WorkspaceDoesNotExist


class GroupsAdminCompatView(WorkspacesAdminView):
    @extend_schema(
        tags=["Admin"],
        deprecated=True,
        operation_id="admin_list_groups",
        description=f"{DEPRECATION_PREFIXES['admin_list_groups']} Returns all groups "
        "with detailed information on each group, if the requesting user "
        "is staff.\n\nThis is a **premium** feature.",
        **AdminListingView.get_extend_schema_parameters(
            "groups",
            WorkspacesAdminView.serializer_class,
            WorkspacesAdminView.search_fields,
            WorkspacesAdminView.sort_field_mapping,
        ),
    )
    def get(self, request):
        return super().get(request)


class GroupAdminCompatView(WorkspaceAdminView):
    @extend_schema(
        tags=["Admin"],
        deprecated=True,
        operation_id="admin_delete_group",
        description=f"{DEPRECATION_PREFIXES['admin_delete_group']} Deletes the "
        "specified group and the applications inside that group, if the "
        "requesting user is staff. \n\nThis is a **premium** feature.",
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the group to delete",
            ),
        ],
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_GROUP_DOES_NOT_EXIST", "ERROR_FEATURE_NOT_AVAILABLE"]
            ),
            401: None,
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            CannotDeleteATemplateGroupError: ERROR_CANNOT_DELETE_A_TEMPLATE_GROUP,
        }
    )
    @transaction.atomic
    def delete(self, request, group_id):
        """Deletes the specified group"""

        return super().delete(request, workspace_id=group_id)
