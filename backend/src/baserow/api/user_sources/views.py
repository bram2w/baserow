from typing import Dict

from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.applications.errors import (
    ERROR_APPLICATION_DOES_NOT_EXIST,
    ERROR_APPLICATION_OPERATION_NOT_SUPPORTED,
)
from baserow.api.decorators import (
    map_exceptions,
    validate_body,
    validate_body_custom_fields,
)
from baserow.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from baserow.api.user_sources.errors import (
    ERROR_USER_SOURCE_DOES_NOT_EXIST,
    ERROR_USER_SOURCE_NOT_IN_SAME_APPLICATION,
)
from baserow.api.user_sources.serializers import (
    CreateUserSourceSerializer,
    MoveUserSourceSerializer,
    UpdateUserSourceSerializer,
    UserSourceSerializer,
)
from baserow.api.utils import (
    CustomFieldRegistryMappingSerializer,
    DiscriminatorCustomFieldsMappingSerializer,
    type_from_data_or_registry,
    validate_data_custom_fields,
)
from baserow.core.exceptions import (
    ApplicationDoesNotExist,
    ApplicationOperationNotSupported,
)
from baserow.core.handler import CoreHandler
from baserow.core.user_sources.exceptions import (
    UserSourceDoesNotExist,
    UserSourceNotInSameApplication,
)
from baserow.core.user_sources.handler import UserSourceHandler
from baserow.core.user_sources.registries import user_source_type_registry
from baserow.core.user_sources.service import UserSourceService


class UserSourcesView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="application_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only the user_sources of the application related "
                "to the provided Id.",
            )
        ],
        tags=["UserSources"],
        operation_id="list_application_user_sources",
        description=(
            "Lists all the user_sources of the application related to the provided "
            "parameter if the user has access to the related application's workspace. "
            "If the workspace is related to a template, then this endpoint will be "
            "publicly accessible."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                user_source_type_registry, UserSourceSerializer, many=True
            ),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, application_id):
        """
        Responds with a list of serialized user_sources that belong to the application
        if the user has access to that application.
        """

        application = CoreHandler().get_application(application_id)

        user_sources = UserSourceService().get_user_sources(request.user, application)

        data = [
            user_source_type_registry.get_serializer(
                user_source, UserSourceSerializer
            ).data
            for user_source in user_sources
        ]

        return Response(data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="application_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Creates an user_source for the application related to the "
                "provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["UserSources"],
        operation_id="create_application_user_source",
        description="Creates a new user_source",
        request=DiscriminatorCustomFieldsMappingSerializer(
            user_source_type_registry,
            CreateUserSourceSerializer,
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                user_source_type_registry, UserSourceSerializer
            ),
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            ApplicationOperationNotSupported: ERROR_APPLICATION_OPERATION_NOT_SUPPORTED,
        }
    )
    @validate_body_custom_fields(
        user_source_type_registry,
        base_serializer_class=CreateUserSourceSerializer,
    )
    def post(self, request, data: Dict, application_id: int):
        """Creates a new user_source."""

        type_name = data.pop("type")
        application = CoreHandler().get_application(application_id)

        before_id = data.pop("before_id", None)
        before = UserSourceHandler().get_user_source(before_id) if before_id else None

        user_source_type = user_source_type_registry.get(type_name)
        user_source = UserSourceService().create_user_source(
            request.user, user_source_type, application, before=before, **data
        )

        serializer = user_source_type_registry.get_serializer(
            user_source, UserSourceSerializer
        )
        return Response(serializer.data)


class UserSourceView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_source_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the user_source",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["UserSources"],
        operation_id="update_application_user_source",
        description="Updates an existing user_source.",
        request=CustomFieldRegistryMappingSerializer(
            user_source_type_registry,
            UpdateUserSourceSerializer,
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                user_source_type_registry, UserSourceSerializer
            ),
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_USER_SOURCE_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserSourceDoesNotExist: ERROR_USER_SOURCE_DOES_NOT_EXIST,
        }
    )
    def patch(self, request, user_source_id: int):
        """
        Update an user_source.
        """

        user_source = UserSourceHandler().get_user_source_for_update(user_source_id)
        user_source_type = type_from_data_or_registry(
            request.data, user_source_type_registry, user_source
        )

        data = validate_data_custom_fields(
            user_source_type.type,
            user_source_type_registry,
            request.data,
            base_serializer_class=UpdateUserSourceSerializer,
            return_validated=True,
        )

        user_source_updated = UserSourceService().update_user_source(
            request.user, user_source, **data
        )

        serializer = user_source_type_registry.get_serializer(
            user_source_updated, UserSourceSerializer
        )
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_source_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the user_source",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["UserSources"],
        operation_id="delete_application_user_source",
        description="Deletes the user_source related by the given id.",
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_USER_SOURCE_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserSourceDoesNotExist: ERROR_USER_SOURCE_DOES_NOT_EXIST,
        }
    )
    @transaction.atomic
    def delete(self, request, user_source_id: int):
        """
        Deletes an user_source.
        """

        user_source = UserSourceHandler().get_user_source_for_update(user_source_id)

        UserSourceService().delete_user_source(request.user, user_source)

        return Response(status=204)


class MoveUserSourceView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_source_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the user_source to move",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["UserSources"],
        operation_id="move_application_user_source",
        description=(
            "Moves the user_source in the application before another user_source or at "
            "the end of the application if no before user_source is given. "
            "The user_sources must belong to the same application."
        ),
        request=MoveUserSourceSerializer,
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                user_source_type_registry, UserSourceSerializer
            ),
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_USER_SOURCE_NOT_IN_SAME_APPLICATION",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_USER_SOURCE_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserSourceDoesNotExist: ERROR_USER_SOURCE_DOES_NOT_EXIST,
            UserSourceNotInSameApplication: ERROR_USER_SOURCE_NOT_IN_SAME_APPLICATION,
        }
    )
    @validate_body(MoveUserSourceSerializer)
    def patch(self, request, data: Dict, user_source_id: int):
        """
        Moves the user_source in the application before another user_source or at the
        end of the application if no before user_source is given.
        """

        user_source = UserSourceHandler().get_user_source_for_update(user_source_id)

        before_id = data.get("before_id", None)

        before = None
        if before_id:
            before = UserSourceHandler().get_user_source(before_id)

        moved_user_source = UserSourceService().move_user_source(
            request.user, user_source, before
        )

        serializer = user_source_type_registry.get_serializer(
            moved_user_source, UserSourceSerializer
        )
        return Response(serializer.data)
