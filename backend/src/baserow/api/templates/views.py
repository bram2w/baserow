from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.applications.serializers import (
    PolymorphicApplicationResponseSerializer,
)
from baserow.api.decorators import map_exceptions, validate_query_parameters
from baserow.api.errors import (
    ERROR_GROUP_DOES_NOT_EXIST,
    ERROR_USER_NOT_IN_GROUP,
)
from baserow.api.jobs.errors import ERROR_MAX_JOB_COUNT_EXCEEDED
from baserow.api.jobs.serializers import JobSerializer
from baserow.api.mixins import SearchableViewMixin
from baserow.api.pagination import LimitOffsetPagination
from baserow.api.schemas import (
    CLIENT_SESSION_ID_SCHEMA_PARAMETER,
    CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
    get_error_schema,
)
from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.api.templates.serializers import (
    ListTemplatesQueryParamSerializer,
    TemplateCategoriesSerializer,
    TemplateListItemSerializer,
    TemplateSerializer,
)
from baserow.core.action.registries import action_type_registry
from baserow.core.actions import InstallTemplateActionType
from baserow.core.exceptions import (
    TemplateDoesNotExist,
    TemplateFileDoesNotExist,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
)
from baserow.core.handler import CoreHandler
from baserow.core.job_types import InstallTemplateJobType
from baserow.core.jobs.exceptions import MaxJobCountExceeded
from baserow.core.jobs.handler import JobHandler
from baserow.core.jobs.registries import job_type_registry
from baserow.core.models import Template, TemplateCategory

from .errors import ERROR_TEMPLATE_DOES_NOT_EXIST, ERROR_TEMPLATE_FILE_DOES_NOT_EXIST

TEMPLATE_LIST_EXAMPLE = {
    "id": 1,
    "type": "user",
    "name": "Sales pipeline",
    "slug": "sales-pipeline-a1b2c3",
    "description": "Track deals from lead to close.",
    "icon": "iconoir-coins",
    "keywords": "",
    "workspace_id": 10,
    "is_default": False,
    "open_application": None,
    "categories": [{"id": 2, "name": "Sales"}],
    "state": "private",
    "reason": None,
    "created_on": "2026-10-01T10:00:00Z",
    "updated_on": "2026-10-01T10:00:00Z",
}


class TemplatesView(APIView, SearchableViewMixin):
    permission_classes = (AllowAny,)
    search_fields = ["name", "description"]

    @extend_schema(
        tags=["Templates"],
        operation_id="list_templates",
        parameters=[
            OpenApiParameter(
                name="view",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                enum=["flat"],
                description="`flat` responds with a paginated list of templates. "
                "Otherwise, the response is the list of categories with their "
                "official templates, which is deprecated.",
            ),
            OpenApiParameter(
                name="type",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                enum=Template.Type.values,
                description="Only templates of this type. Only with `view=flat`.",
            ),
            OpenApiParameter(
                name="owned",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
                description="Only templates owned by the authenticated user. Only "
                "with `view=flat`.",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Only templates whose name or description contains "
                "this value. Only with `view=flat`.",
            ),
            OpenApiParameter(
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="How many templates to return, at most 100. Only with "
                "`view=flat`.",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="The offset of the templates to return. Only with "
                "`view=flat`.",
            ),
        ],
        description=(
            "Lists the templates. The template's `workspace_id` can be used for "
            "previewing purposes because that workspace contains the applications "
            "that are in the template. All the `get` and `list` endpoints related to "
            "that workspace are accessible to whoever can list the template.\n\n"
            "The `view` query parameter selects the shape of the response:\n\n"
            "- `view=flat`: a paginated list of the official templates and the user "
            "templates the caller can open, most recently updated first, filtered "
            "with `type`, `owned` and `search`. `state` and `reason` are only set "
            "for the owner of a user template.\n"
            "- Any other or no `view` (deprecated): a list of the template "
            "categories, each with its official templates, ignoring the other query "
            "parameters. Categories holding only user templates are left out."
        ),
        responses={
            200: OpenApiResponse(
                response=PolymorphicProxySerializer(
                    component_name="TemplatesListResponse",
                    serializers=[
                        get_example_pagination_serializer_class(
                            TemplateListItemSerializer,
                            serializer_name="TemplatePagination",
                        ),
                        TemplateCategoriesSerializer(many=True),
                    ],
                    resource_type_field_name=None,
                    many=False,
                ),
                examples=[
                    OpenApiExample(
                        "view=flat",
                        value={
                            "count": 1,
                            "next": None,
                            "previous": None,
                            "results": [TEMPLATE_LIST_EXAMPLE],
                        },
                    ),
                    OpenApiExample(
                        "No view (deprecated)",
                        value=[
                            {
                                "id": 2,
                                "name": "Sales",
                                "templates": [
                                    {
                                        "id": 3,
                                        "type": "official",
                                        "name": "CRM",
                                        "slug": "crm",
                                        "description": "Manage customers.",
                                        "icon": "iconoir-user",
                                        "keywords": "crm,sales",
                                        "workspace_id": 11,
                                        "is_default": False,
                                        "open_application": None,
                                    }
                                ],
                            }
                        ],
                    ),
                ],
            ),
            400: get_error_schema(["ERROR_QUERY_PARAMETER_VALIDATION"]),
        },
    )
    def get(self, request):
        """
        Responds with a page of templates, or with the template categories and their
        official templates. The deprecated categories ignore the query parameters, as
        they always did.
        """

        if request.GET.get("view") == "flat":
            return self._get_flat(request)

        # Hide the categories holding only user templates. Empty ones stay listed.
        official_templates = Template.objects.official()
        categories = TemplateCategory.objects.filter(
            Exists(official_templates.filter(categories=OuterRef("pk")))
            | ~Exists(Template.objects.filter(categories=OuterRef("pk")))
        ).prefetch_related(Prefetch("templates", queryset=official_templates))
        serializer = TemplateCategoriesSerializer(categories, many=True)
        return Response(serializer.data)

    @validate_query_parameters(ListTemplatesQueryParamSerializer)
    def _get_flat(self, request, query_params):
        templates = CoreHandler().list_templates(
            request.user,
            template_type=query_params.get("type"),
            owned=query_params["owned"],
        )
        templates = self.apply_search(query_params.get("search"), templates)

        paginator = LimitOffsetPagination()
        paginator.default_limit = 20
        paginator.max_limit = 100
        page = paginator.paginate_queryset(templates, request, self)
        return paginator.get_paginated_response(
            TemplateListItemSerializer(
                page, many=True, context={"request": request}
            ).data
        )


class TemplateView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(exclude=True)
    @map_exceptions(
        {
            TemplateDoesNotExist: ERROR_TEMPLATE_DOES_NOT_EXIST,
        }
    )
    def get(self, request, slug):
        """
        Responds with a more detailed serialized version of the template related to
        the provided template slug.
        """

        try:
            template = (
                Template.objects.openable(request.user)
                .prefetch_related("categories")
                .get(slug=slug)
            )
        except Template.DoesNotExist as exc:
            raise TemplateDoesNotExist(
                f"The template with slug {slug} does not exist."
            ) from exc

        return Response(TemplateSerializer(template).data)


class InstallTemplateView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Templates"],
        operation_id="install_template",
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id related to the workspace where the template "
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
            "(Deprecated) Installs the applications of the given template into "
            "the given workspace if the user has access to that workspace. The response "
            "contains those newly created applications."
        ),
        request=None,
        responses={
            200: PolymorphicApplicationResponseSerializer(many=True),
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
    def post(self, request, workspace_id, template_id):
        """Install a template into a workspace."""

        handler = CoreHandler()
        workspace = handler.get_workspace(workspace_id)
        template = handler.get_template(template_id)
        installed_applications = action_type_registry.get_by_type(
            InstallTemplateActionType
        ).do(request.user, workspace, template)

        data = [
            PolymorphicApplicationResponseSerializer(application).data
            for application in installed_applications
        ]
        return Response(data)


class AsyncInstallTemplateView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Templates"],
        operation_id="install_template_async",
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id related to the workspace where the template "
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
            "Start an async job to install the applications of the given template into "
            "the given workspace if the user has access to that workspace. The response "
            "contains those newly created applications."
        ),
        request=None,
        responses={
            202: InstallTemplateJobType().response_serializer_class,
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
    def post(self, request, workspace_id, template_id):
        """Start an async job to install a template into a workspace."""

        job = JobHandler().create_and_start_job(
            request.user,
            InstallTemplateJobType.type,
            workspace_id=workspace_id,
            template_id=template_id,
        )

        serializer = job_type_registry.get_serializer(job, JobSerializer)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
