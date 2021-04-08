from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes

from baserow.api.templates.serializers import TemplateCategoriesSerializer
from baserow.api.decorators import map_exceptions
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP, ERROR_GROUP_DOES_NOT_EXIST
from baserow.api.schemas import get_error_schema
from baserow.api.utils import PolymorphicMappingSerializer
from baserow.api.applications.serializers import get_application_serializer
from baserow.api.applications.views import application_type_serializers
from baserow.core.models import TemplateCategory
from baserow.core.handler import CoreHandler
from baserow.core.exceptions import (
    UserNotInGroupError, GroupDoesNotExist, TemplateDoesNotExist,
    TemplateFileDoesNotExist
)

from .errors import ERROR_TEMPLATE_DOES_NOT_EXIST, ERROR_TEMPLATE_FILE_DOES_NOT_EXIST


class TemplatesView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=['Templates'],
        operation_id='list_templates',
        description=(
            'Lists all the template categories and the related templates that are in '
            'that category. The template\'s `group_id` can be used for previewing '
            'purposes because that group contains the applications that are in the '
            'template. All the `get` and `list` endpoints related to that group are '
            'publicly accessible.'
        ),
        responses={
            200: TemplateCategoriesSerializer(many=True)
        }
    )
    def get(self, request):
        """Responds with a list of all template categories and templates."""

        categories = TemplateCategory.objects.all().prefetch_related('templates')
        serializer = TemplateCategoriesSerializer(categories, many=True)
        return Response(serializer.data)


class InstallTemplateView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['Templates'],
        operation_id='install_template',
        parameters=[
            OpenApiParameter(
                name='group_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='The id related to the group where the template '
                            'applications must be installed into.'
            ),
            OpenApiParameter(
                name='template_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description='The id related to the template that must be installed.'
            )
        ],
        description=(
            'Installs the applications of the given template into the given group if '
            'the user has access to that group. The response contains those newly '
            'created applications.'
        ),
        responses={
            200: PolymorphicMappingSerializer(
                'Applications',
                application_type_serializers,
                many=True
            ),
            400: get_error_schema([
                'ERROR_USER_NOT_IN_GROUP',
                'ERROR_TEMPLATE_FILE_DOES_NOT_EXIST'
            ]),
            404: get_error_schema([
                'ERROR_GROUP_DOES_NOT_EXIST',
                'ERROR_TEMPLATE_DOES_NOT_EXIST'
            ])
        }
    )
    @map_exceptions({
        GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
        UserNotInGroupError: ERROR_USER_NOT_IN_GROUP,
        TemplateDoesNotExist: ERROR_TEMPLATE_DOES_NOT_EXIST,
        TemplateFileDoesNotExist: ERROR_TEMPLATE_FILE_DOES_NOT_EXIST
    })
    def get(self, request, group_id, template_id):
        """Install a template into a group."""

        handler = CoreHandler()
        group = handler.get_group(group_id)
        template = handler.get_template(template_id)
        applications, id_mapping = handler.install_template(
            request.user,
            group,
            template
        )

        data = [
            get_application_serializer(application).data
            for application in applications
        ]
        return Response(data)
