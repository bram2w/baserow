from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema

from baserow.api.applications.views import application_type_serializers
from baserow.api.decorators import map_exceptions
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.api.jobs.errors import ERROR_MAX_JOB_COUNT_EXCEEDED
from baserow.api.schemas import (
    CLIENT_SESSION_ID_SCHEMA_PARAMETER,
    CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
    get_error_schema,
)
from baserow.api.templates.errors import (
    ERROR_TEMPLATE_DOES_NOT_EXIST,
    ERROR_TEMPLATE_FILE_DOES_NOT_EXIST,
)
from baserow.api.templates.serializers import TemplateCategoriesSerializer
from baserow.api.templates.views import (
    AsyncInstallTemplateView,
    InstallTemplateJobTypeSerializer,
    InstallTemplateView,
    TemplatesView,
)
from baserow.api.utils import DiscriminatorMappingSerializer
from baserow.compat.api.conf import (
    TEMPLATES_DEPRECATION_PREFIXES as DEPRECATION_PREFIXES,
)
from baserow.core.exceptions import (
    TemplateDoesNotExist,
    TemplateFileDoesNotExist,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
)
from baserow.core.jobs.exceptions import MaxJobCountExceeded


class TemplatesCompatView(TemplatesView):
    @extend_schema(
        tags=["Templates"],
        deprecated=True,
        operation_id="group_list_templates",
        description=(
            f"{DEPRECATION_PREFIXES['group_list_templates']} Lists all the template "
            "categories and the related templates that are in that category. The "
            "template's `group_id` can be used for previewing purposes because that "
            "group contains the applications that are in the template. All the `get` "
            "and `list` endpoints related to that group are publicly accessible."
        ),
        responses={200: TemplateCategoriesSerializer(many=True)},
    )
    def get(self, request):
        """Responds with a list of all template categories and templates."""

        return super().get(request)


class InstallTemplateCompatView(InstallTemplateView):
    @extend_schema(
        tags=["Templates"],
        deprecated=True,
        operation_id="group_install_template",
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id related to the group where the template "
                "applications must be installed into.",
            ),
            OpenApiParameter(
                name="template_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id related to the template that must be installed.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        description=(
            f"{DEPRECATION_PREFIXES['group_install_template']} Installs the "
            "applications of the given template into the given group if the user has "
            "access to that group. The response contains those newly created "
            "applications."
        ),
        request=None,
        responses={
            200: DiscriminatorMappingSerializer(
                "Applications", application_type_serializers, many=True
            ),
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_TEMPLATE_FILE_DOES_NOT_EXIST"]
            ),
            404: get_error_schema(
                ["ERROR_GROUP_DOES_NOT_EXIST", "ERROR_TEMPLATE_DOES_NOT_EXIST"]
            ),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            TemplateDoesNotExist: ERROR_TEMPLATE_DOES_NOT_EXIST,
            TemplateFileDoesNotExist: ERROR_TEMPLATE_FILE_DOES_NOT_EXIST,
        }
    )
    @transaction.atomic
    def post(self, request, group_id, template_id):
        """Install a template into a group."""

        return super().post(request, group_id, template_id)


class AsyncInstallTemplateCompatView(AsyncInstallTemplateView):
    @extend_schema(
        tags=["Templates"],
        deprecated=True,
        operation_id="group_install_template_async",
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id related to the group where the template "
                "applications must be installed into.",
            ),
            OpenApiParameter(
                name="template_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id related to the template that must be installed.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        description=(
            f"{DEPRECATION_PREFIXES['group_install_template_async']} Start an async "
            "job to install the applications of the given template into the given "
            "group if the user has access to that group. The response contains those "
            "newly created applications."
        ),
        request=None,
        responses={
            202: InstallTemplateJobTypeSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_TEMPLATE_FILE_DOES_NOT_EXIST",
                    "ERROR_MAX_JOB_COUNT_EXCEEDED",
                ]
            ),
            404: get_error_schema(
                ["ERROR_GROUP_DOES_NOT_EXIST", "ERROR_TEMPLATE_DOES_NOT_EXIST"]
            ),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            TemplateDoesNotExist: ERROR_TEMPLATE_DOES_NOT_EXIST,
            MaxJobCountExceeded: ERROR_MAX_JOB_COUNT_EXCEEDED,
            TemplateFileDoesNotExist: ERROR_TEMPLATE_FILE_DOES_NOT_EXIST,
        }
    )
    @transaction.atomic
    def post(self, request, group_id, template_id):
        """Start an async job to install a template into a group."""

        return super().post(request, group_id, template_id)
