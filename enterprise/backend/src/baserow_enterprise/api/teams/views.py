from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from baserow.core.action.registries import action_type_registry
from baserow.core.exceptions import UserNotInGroup
from baserow.core.handler import CoreHandler
from baserow_enterprise.api.errors import (
    ERROR_SUBJECT_DOES_NOT_EXIST,
    ERROR_TEAM_DOES_NOT_EXIST,
    ERROR_USER_NOT_IN_TEAM,
)
from baserow_enterprise.api.serializers import (
    TeamResponseSerializer,
    TeamSerializer,
    TeamSubjectResponseSerializer,
    TeamSubjectSerializer,
)
from baserow_enterprise.exceptions import TeamDoesNotExist, TeamSubjectDoesNotExist
from baserow_enterprise.teams.actions import (
    CreateTeamActionType,
    CreateTeamSubjectActionType,
    DeleteTeamActionType,
    DeleteTeamSubjectActionType,
    UpdateTeamActionType,
)
from baserow_enterprise.teams.exceptions import UserNotInTeam
from baserow_enterprise.teams.handler import TeamHandler
from baserow_enterprise.teams.operations import (
    CreateTeamOperationType,
    CreateTeamSubjectOperationType,
    DeleteTeamOperationType,
    DeleteTeamSubjectOperationType,
    ListTeamsOperationType,
    ListTeamSubjectsOperationType,
    ReadTeamOperationType,
    ReadTeamSubjectOperationType,
    UpdateTeamOperationType,
)


class TeamsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Lists all teams in a given group.",
            ),
        ],
        tags=["Teams"],
        operation_id="list_teams",
        description=("Lists all teams in a given group."),
        responses={200: TeamResponseSerializer(many=True)},
    )
    def get(self, request, group_id: int):
        """Responds with a list of teams in a specific group."""

        group = CoreHandler().get_group(group_id)
        CoreHandler().check_permissions(
            request.user,
            ListTeamsOperationType.type,
            group=group,
            context=group,
        )

        teams = TeamHandler().list_teams_in_group(request.user, group)
        serializer = TeamResponseSerializer(teams, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[CLIENT_SESSION_ID_SCHEMA_PARAMETER],
        tags=["Teams"],
        operation_id="create_team",
        description=("Creates a new team."),
        request=TeamSerializer,
        responses={
            200: TeamResponseSerializer,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(TeamSerializer)
    def post(self, request, group_id: int, data):
        """Creates a new team for a user."""

        group = CoreHandler().get_group(group_id)
        CoreHandler().check_permissions(
            request.user,
            CreateTeamOperationType.type,
            group=group,
            context=group,
        )

        team = action_type_registry.get_by_type(CreateTeamActionType).do(
            request.user, data["name"], group
        )
        return Response(TeamResponseSerializer(team).data)


class TeamView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="team_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the team related to the provided value.",
            )
        ],
        tags=["Teams"],
        operation_id="get_team",
        description=("Returns the information related to the provided team id."),
        responses={
            200: TeamResponseSerializer,
            400: get_error_schema(["ERROR_USER_NOT_IN_TEAM"]),
            404: get_error_schema(["ERROR_TEAM_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            TeamDoesNotExist: ERROR_TEAM_DOES_NOT_EXIST,
            UserNotInTeam: ERROR_USER_NOT_IN_TEAM,
        }
    )
    def get(self, request, team_id: int):
        """Responds with a single team."""

        team = TeamHandler().get_team(request.user, team_id)
        CoreHandler().check_permissions(
            request.user,
            ReadTeamOperationType.type,
            group=team.group,
            context=team,
        )

        serializer = TeamResponseSerializer(team)
        return Response(serializer.data)

    @extend_schema(
        parameters=[CLIENT_SESSION_ID_SCHEMA_PARAMETER],
        tags=["Teams"],
        operation_id="update_team",
        description=("Updates an existing team with a new name."),
        request=TeamSerializer,
        responses={
            200: TeamResponseSerializer,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
        },
    )
    @transaction.atomic
    @validate_body(TeamSerializer)
    @map_exceptions(
        {
            TeamDoesNotExist: ERROR_TEAM_DOES_NOT_EXIST,
            UserNotInTeam: ERROR_USER_NOT_IN_TEAM,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def patch(self, request, data, team_id: int):
        """Updates the team if the user belongs to the group."""

        team = TeamHandler().get_team_for_update(request.user, team_id)
        CoreHandler().check_permissions(
            request.user,
            UpdateTeamOperationType.type,
            group=team.group,
            context=team,
        )

        team = action_type_registry.get_by_type(UpdateTeamActionType).do(
            request.user, team, name=data["name"]
        )

        return Response(TeamResponseSerializer(team).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="team_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Deletes the team related to the provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Teams"],
        operation_id="delete_team",
        description=(
            "Deletes a team if the authorized user is in the team's "
            "group. All the related children (e.g. subjects) are also going to be deleted."
        ),
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_TEAM",
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM",
                ]
            ),
            404: get_error_schema(["ERROR_TEAM_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            TeamDoesNotExist: ERROR_TEAM_DOES_NOT_EXIST,
            UserNotInTeam: ERROR_USER_NOT_IN_TEAM,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def delete(self, request, team_id: int):
        """Deletes an existing team if the user belongs to the group."""

        team = TeamHandler().get_team_for_update(request.user, team_id)
        CoreHandler().check_permissions(
            request.user,
            DeleteTeamOperationType.type,
            group=team.group,
            context=team,
        )

        action_type_registry.get_by_type(DeleteTeamActionType).do(request.user, team)

        return Response(status=204)


class TeamSubjectsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Teams"],
        operation_id="list_team_subjects",
        description=("Lists all team subjects in a given team."),
        responses={200: TeamSubjectResponseSerializer(many=True)},
    )
    def get(self, request, team_id: int):
        """Responds with a list of team subjects in a specific team."""

        team = TeamHandler().get_team(request.user, team_id)
        CoreHandler().check_permissions(
            request.user,
            ListTeamSubjectsOperationType.type,
            group=team.group,
            context=team,
        )

        subjects = TeamHandler().list_subjects_in_team(team_id)
        serializer = TeamSubjectResponseSerializer(subjects, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[CLIENT_SESSION_ID_SCHEMA_PARAMETER],
        tags=["Teams"],
        operation_id="create_subject",
        description=("Creates a new team subject."),
        request=TeamSubjectSerializer,
        responses={200: TeamSubjectResponseSerializer},
    )
    @transaction.atomic
    @validate_body(TeamSubjectSerializer)
    def post(self, request, team_id: int, data):

        team = TeamHandler().get_team(request.user, team_id)
        CoreHandler().check_permissions(
            request.user,
            CreateTeamSubjectOperationType.type,
            group=team.group,
            context=team,
        )

        subject_lookup = {"id": data["subject_id"]}
        if data["subject_user_email"]:
            subject_lookup = {"email": data["subject_user_email"]}

        subject = action_type_registry.get_by_type(CreateTeamSubjectActionType).do(
            request.user, subject_lookup, data["subject_type"], team
        )
        return Response(TeamSubjectResponseSerializer(subject).data)


class TeamSubjectView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="subject_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the subject related to the provided value.",
            )
        ],
        tags=["Teams"],
        operation_id="get_subject",
        description=("Returns the information related to the provided subject id"),
        responses={
            200: TeamSubjectResponseSerializer,
            404: get_error_schema(["ERROR_SUBJECT_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions({TeamSubjectDoesNotExist: ERROR_SUBJECT_DOES_NOT_EXIST})
    def get(self, request, team_id: int, subject_id: int):
        """Responds with a single subject."""

        team = TeamHandler().get_team(request.user, team_id)
        subject = TeamHandler().get_subject(subject_id)
        CoreHandler().check_permissions(
            request.user,
            ReadTeamSubjectOperationType.type,
            group=team.group,
            context=subject,
        )

        serializer = TeamSubjectResponseSerializer(subject)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="team_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The team id which the subject will be removed from.",
            ),
            OpenApiParameter(
                name="subject_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The subject id to remove from the team.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Teams"],
        operation_id="delete_subject",
        description=(
            "Deletes a subject if the authorized user is in the team's group."
        ),
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_TEAM", "ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM"]
            ),
            404: get_error_schema(["ERROR_TEAM_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    def delete(self, request, team_id: int, subject_id: int):
        """Deletes an existing team subject if the user belongs to the group."""

        team = TeamHandler().get_team(request.user, team_id)
        subject = TeamHandler().get_subject_for_update(subject_id)
        CoreHandler().check_permissions(
            request.user,
            DeleteTeamSubjectOperationType.type,
            group=team.group,
            context=subject,
        )

        action_type_registry.get_by_type(DeleteTeamSubjectActionType).do(
            request.user, subject
        )

        return Response(status=204)
