from typing import Any, Dict
from urllib.request import Request

from django.contrib.auth import get_user_model
from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response

from baserow.api.decorators import (
    map_exceptions,
    validate_body,
    validate_query_parameters,
)
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.core.exceptions import (
    LastAdminOfWorkspace,
    ObjectScopeTypeDoesNotExist,
    SubjectTypeNotExist,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
)
from baserow_enterprise.api.errors import (
    ERROR_DUPLICATE_ROLE_ASSIGNMENTS,
    ERROR_LAST_ADMIN_OF_GROUP,
    ERROR_OBJECT_SCOPE_TYPE_DOES_NOT_EXIST,
    ERROR_ROLE_DOES_NOT_EXIST,
    ERROR_SCOPE_DOES_NOT_EXIST,
    ERROR_SUBJECT_DOES_NOT_EXIST,
    ERROR_SUBJECT_TYPE_DOES_NOT_EXIST,
)
from baserow_enterprise.api.role.exceptions import DuplicateRoleAssignments
from baserow_enterprise.api.role.serializers import (
    BatchCreateRoleAssignmentSerializer,
    CreateRoleAssignmentSerializer,
    GetRoleAssignmentsQueryParametersSerializer,
    OpenApiRoleAssignmentSerializer,
)
from baserow_enterprise.api.role.views import (
    BatchRoleAssignmentsView,
    RoleAssignmentsView,
)
from baserow_enterprise.compat.api.conf import (
    ROLE_DEPRECATION_PREFIXES as DEPRECATION_PREFIXES,
)
from baserow_enterprise.exceptions import RoleNotExist, ScopeNotExist, SubjectNotExist

User = get_user_model()


class RoleAssignmentsCompatView(RoleAssignmentsView):
    """Views to assign a role."""

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The group in which the role assignment takes place.",
            ),
        ],
        tags=["Role assignments"],
        deprecated=True,
        operation_id="group_assign_role",
        description=(
            f"{DEPRECATION_PREFIXES['group_assign_role']} You can assign a role to a "
            "subject into the given group for the given scope with this endpoint. "
            "If you want to remove the role you can omit the role property."
        ),
        request=CreateRoleAssignmentSerializer,
        responses={
            200: OpenApiRoleAssignmentSerializer,
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_CANT_ASSIGN_ROLE_EXCEPTION_TO_ADMIN",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_SCOPE_DOES_NOT_EXIST",
                    "ERROR_GROUP_DOES_NOT_EXIST",
                    "ERROR_OBJECT_SCOPE_TYPE_DOES_NOT_EXIST",
                    "ERROR_SUBJECT_TYPE_DOES_NOT_EXIST",
                    "ERROR_ROLE_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ObjectScopeTypeDoesNotExist: ERROR_OBJECT_SCOPE_TYPE_DOES_NOT_EXIST,
            SubjectTypeNotExist: ERROR_SUBJECT_TYPE_DOES_NOT_EXIST,
            SubjectNotExist: ERROR_SUBJECT_DOES_NOT_EXIST,
            ScopeNotExist: ERROR_SCOPE_DOES_NOT_EXIST,
            RoleNotExist: ERROR_ROLE_DOES_NOT_EXIST,
            LastAdminOfWorkspace: ERROR_LAST_ADMIN_OF_GROUP,
        }
    )
    @validate_body(CreateRoleAssignmentSerializer, return_validated=True)
    @transaction.atomic
    def post(
        self,
        request: Request,
        group_id: int,
        data,
    ) -> Response:
        """Assign or remove a role to the user."""

        return super().post(request, workspace_id=group_id)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The group in which the role assignments are related to.",
            ),
            OpenApiParameter(
                name="scope_id",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="The id of the scope you are trying to get all role"
                "assignments for.",
            ),
            OpenApiParameter(
                name="scope_type",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="The type of scope you are trying to get all role"
                "assignments for.",
            ),
        ],
        tags=["Role assignments"],
        deprecated=True,
        operation_id="group_list_role_assignments",
        description=(
            f"{DEPRECATION_PREFIXES['group_assign_role']} You can list the role "
            "assignments within a group, optionally filtered down to a specific scope "
            "inside of that group. If the scope isn't specified,"
            "the group will be considered the scope."
        ),
        request=GetRoleAssignmentsQueryParametersSerializer,
        responses={
            200: OpenApiRoleAssignmentSerializer(many=True),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_SCOPE_DOES_NOT_EXIST",
                    "ERROR_GROUP_DOES_NOT_EXIST",
                    "ERROR_OBJECT_SCOPE_TYPE_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            ScopeNotExist: ERROR_SCOPE_DOES_NOT_EXIST,
            ObjectScopeTypeDoesNotExist: ERROR_OBJECT_SCOPE_TYPE_DOES_NOT_EXIST,
        }
    )
    @validate_query_parameters(
        GetRoleAssignmentsQueryParametersSerializer, return_validated=True
    )
    def get(
        self,
        request: Request,
        group_id: int,
        query_params: Dict[str, Any],
    ) -> Response:
        return super().get(request, workspace_id=group_id)


class BatchRoleAssignmentsCompatView(BatchRoleAssignmentsView):
    """View for assigning roles in batch"""

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The group in which the role assignment takes place.",
            ),
        ],
        deprecated=True,
        tags=["Role assignments"],
        operation_id="group_batch_assign_role",
        description=(
            f"{DEPRECATION_PREFIXES['group_batch_assign_role']} You can assign a role "
            "to a multiple subjects into the given group for the given scope with "
            "this endpoint. If you want to remove the role you can omit the role "
            "property."
        ),
        request=BatchCreateRoleAssignmentSerializer,
        responses={
            200: OpenApiRoleAssignmentSerializer(many=True),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_DUPLICATE_ROLE_ASSIGNMENTS",
                    "ERROR_CANT_ASSIGN_ROLE_EXCEPTION_TO_ADMIN",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_SCOPE_DOES_NOT_EXIST",
                    "ERROR_GROUP_DOES_NOT_EXIST",
                    "ERROR_OBJECT_SCOPE_TYPE_DOES_NOT_EXIST",
                    "ERROR_SUBJECT_TYPE_DOES_NOT_EXIST",
                    "ERROR_ROLE_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ObjectScopeTypeDoesNotExist: ERROR_OBJECT_SCOPE_TYPE_DOES_NOT_EXIST,
            SubjectTypeNotExist: ERROR_SUBJECT_TYPE_DOES_NOT_EXIST,
            SubjectNotExist: ERROR_SUBJECT_DOES_NOT_EXIST,
            ScopeNotExist: ERROR_SCOPE_DOES_NOT_EXIST,
            RoleNotExist: ERROR_ROLE_DOES_NOT_EXIST,
            DuplicateRoleAssignments: ERROR_DUPLICATE_ROLE_ASSIGNMENTS,
        }
    )
    @validate_body(
        BatchCreateRoleAssignmentSerializer,
        return_validated=True,
    )
    def post(
        self,
        request: Request,
        group_id: int,
        data,
    ) -> Response:
        """Assign or remove a role to the user."""

        return super().post(request, workspace_id=group_id)
