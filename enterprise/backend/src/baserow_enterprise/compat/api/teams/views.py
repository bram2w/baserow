from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema

from baserow.api.decorators import (
    map_exceptions,
    validate_body,
    validate_query_parameters,
)
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from baserow.core.exceptions import UserNotInWorkspace, WorkspaceDoesNotExist
from baserow_enterprise.api.errors import (
    ERROR_ROLE_DOES_NOT_EXIST,
    ERROR_SUBJECT_BAD_REQUEST,
    ERROR_SUBJECT_DOES_NOT_EXIST,
    ERROR_SUBJECT_NOT_IN_GROUP,
    ERROR_SUBJECT_TYPE_UNSUPPORTED,
    ERROR_TEAM_NAME_NOT_UNIQUE,
)
from baserow_enterprise.api.teams.serializers import (
    GetTeamsViewParamsSerializer,
    TeamResponseSerializer,
    TeamSerializer,
)
from baserow_enterprise.api.teams.views import TeamsView
from baserow_enterprise.compat.api.conf import (
    TEAMS_DEPRECATION_PREFIXES as DEPRECATION_PREFIXES,
)
from baserow_enterprise.exceptions import RoleUnsupported
from baserow_enterprise.teams.exceptions import (
    TeamNameNotUnique,
    TeamSubjectBadRequest,
    TeamSubjectDoesNotExist,
    TeamSubjectNotInGroup,
    TeamSubjectTypeUnsupported,
)


class TeamsCompatView(TeamsView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Lists all teams in a given group.",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Search for teams by their name.",
            ),
            OpenApiParameter(
                name="sorts",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Sort teams by name or subjects.",
            ),
        ],
        tags=["Teams"],
        operation_id="group_list_teams",
        deprecated=True,
        description=(
            f"{DEPRECATION_PREFIXES['group_list_teams']} Lists all teams in a "
            "given group."
        ),
        responses={
            200: TeamResponseSerializer(many=True),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions({WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST})
    @validate_query_parameters(GetTeamsViewParamsSerializer)
    def get(self, request, group_id: int, query_params):
        """Responds with a list of teams in a specific group."""

        return super().get(request, workspace_id=group_id)

    @extend_schema(
        parameters=[CLIENT_SESSION_ID_SCHEMA_PARAMETER],
        tags=["Teams"],
        operation_id="group_create_team",
        deprecated=True,
        description=(
            f"{DEPRECATION_PREFIXES['group_create_team']} Creates a new team in a "
            "given group."
        ),
        request=TeamSerializer,
        responses={
            200: TeamResponseSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_SUBJECT_BAD_REQUEST",
                    "ERROR_TEAM_NAME_NOT_UNIQUE",
                    "ERROR_SUBJECT_NOT_IN_GROUP",
                    "ERROR_SUBJECT_TYPE_UNSUPPORTED",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_GROUP_DOES_NOT_EXIST",
                    "ERROR_SUBJECT_DOES_NOT_EXIST",
                    "ERROR_ROLE_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            RoleUnsupported: ERROR_ROLE_DOES_NOT_EXIST,
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            TeamNameNotUnique: ERROR_TEAM_NAME_NOT_UNIQUE,
            TeamSubjectBadRequest: ERROR_SUBJECT_BAD_REQUEST,
            TeamSubjectDoesNotExist: ERROR_SUBJECT_DOES_NOT_EXIST,
            TeamSubjectNotInGroup: ERROR_SUBJECT_NOT_IN_GROUP,
            TeamSubjectTypeUnsupported: ERROR_SUBJECT_TYPE_UNSUPPORTED,
        }
    )
    @transaction.atomic
    @validate_body(TeamSerializer)
    def post(self, request, group_id: int, data):
        """Creates a new team for a user."""

        return super().post(request, workspace_id=group_id)
