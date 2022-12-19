import uuid
from typing import Any, Dict
from urllib.request import Request

from baserow_premium.license.handler import LicenseHandler
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import (
    map_exceptions,
    validate_body,
    validate_query_parameters,
)
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.api.sessions import set_client_undo_redo_action_group_id
from baserow.core.action.registries import action_type_registry
from baserow.core.exceptions import (
    GroupDoesNotExist,
    ObjectScopeTypeDoesNotExist,
    UserNotInGroup,
)
from baserow.core.handler import CoreHandler
from baserow.core.registries import object_scope_type_registry
from baserow.core.utils import unique_dicts_in_list
from baserow_enterprise.api.errors import (
    ERROR_DUPLICATE_ROLE_ASSIGNMENTS,
    ERROR_OBJECT_SCOPE_TYPE_DOES_NOT_EXIST,
    ERROR_ROLE_DOES_NOT_EXIST,
    ERROR_SCOPE_DOES_NOT_EXIST,
    ERROR_SUBJECT_DOES_NOT_EXIST,
    ERROR_SUBJECT_TYPE_DOES_NOT_EXIST,
)
from baserow_enterprise.exceptions import (
    RoleNotExist,
    ScopeNotExist,
    SubjectNotExist,
    SubjectTypeNotExist,
)
from baserow_enterprise.features import RBAC
from baserow_enterprise.role.actions import AssignRoleActionType
from baserow_enterprise.role.constants import ROLE_ASSIGNABLE_OBJECT_MAP
from baserow_enterprise.role.handler import RoleAssignmentHandler

from .exceptions import DuplicateRoleAssignments
from .serializers import (
    BatchCreateRoleAssignmentSerializer,
    CreateRoleAssignmentSerializer,
    GetRoleAssignmentsQueryParametersSerializer,
    OpenApiRoleAssignmentSerializer,
    RoleAssignmentSerializer,
)


class RoleAssignmentsView(APIView):
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
        operation_id="assign_role",
        description=(
            "You can assign a role to a subject into the given group for the given "
            "scope with this endpoint. If you want to remove the role you can "
            "omit the role property."
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
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            ObjectScopeTypeDoesNotExist: ERROR_OBJECT_SCOPE_TYPE_DOES_NOT_EXIST,
            SubjectTypeNotExist: ERROR_SUBJECT_TYPE_DOES_NOT_EXIST,
            SubjectNotExist: ERROR_SUBJECT_DOES_NOT_EXIST,
            ScopeNotExist: ERROR_SCOPE_DOES_NOT_EXIST,
            RoleNotExist: ERROR_ROLE_DOES_NOT_EXIST,
        }
    )
    @validate_body(CreateRoleAssignmentSerializer, return_validated=True)
    def post(
        self,
        request: Request,
        group_id: int,
        data,
    ) -> Response:
        """Assign or remove a role to the user."""

        group = CoreHandler().get_group(group_id)

        role = data.get("role", None)

        if role is not None:
            # We set the role
            role_assignment = action_type_registry.get_by_type(AssignRoleActionType).do(
                request.user,
                data["subject"],
                group,
                role,
                scope=data["scope"],
            )

            serializer = RoleAssignmentSerializer(role_assignment)

            return Response(serializer.data)
        else:
            # We remove the role
            action_type_registry.get_by_type(AssignRoleActionType).do(
                request.user,
                data["subject"],
                group,
                role=None,
                scope=data["scope"],
            )
            return Response(status=204)

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
        operation_id="list_role_assignments",
        description=(
            "You can list the role assignments within a group, optionally filtered down"
            "to a specific scope inside of that group. If the scope isn't specified,"
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
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
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

        group = CoreHandler().get_group(group_id)
        scope = query_params.get("scope", group)

        LicenseHandler.raise_if_user_doesnt_have_feature(RBAC, request.user, group)

        scope_type = object_scope_type_registry.get_by_model(scope)
        CoreHandler().check_permissions(
            request.user,
            ROLE_ASSIGNABLE_OBJECT_MAP[scope_type.type]["READ"],
            group=group,
            context=scope,
        )

        role_assignments = RoleAssignmentHandler().get_role_assignments(
            group, scope=scope
        )

        return Response(RoleAssignmentSerializer(role_assignments, many=True).data)


class BatchRoleAssignmentsView(APIView):
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
        tags=["Role assignments"],
        operation_id="batch_assign_role",
        description=(
            "You can assign a role to a multiple subjects into the given group for "
            "the given scope with this endpoint. If you want to remove the role you can"
            "omit the role property."
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
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
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

        data = data.get("items", [])
        user = request.user
        group = CoreHandler().get_group(group_id)

        _, duplicates = unique_dicts_in_list(
            data, unique_fields=["subject_id", "subject_type", "scope_id", "scope_type"]
        )
        if len(duplicates) > 0:
            indexes = [data.index(duplicate) for duplicate in duplicates]
            raise DuplicateRoleAssignments(indexes)

        LicenseHandler.raise_if_user_doesnt_have_feature(RBAC, request.user, group)

        set_client_undo_redo_action_group_id(user, uuid.uuid4())

        role_assignments = [
            action_type_registry.get_by_type(AssignRoleActionType).do(
                user,
                role_assignment["subject"],
                group,
                role_assignment["role"],
                scope=role_assignment["scope"],
            )
            for role_assignment in data
        ]

        return Response(RoleAssignmentSerializer(role_assignments, many=True).data)
