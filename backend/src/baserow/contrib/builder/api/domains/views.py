from typing import Dict

from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_202_ACCEPTED
from rest_framework.views import APIView

from baserow.api.applications.errors import ERROR_APPLICATION_DOES_NOT_EXIST
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.jobs.serializers import JobSerializer
from baserow.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from baserow.api.utils import DiscriminatorCustomFieldsMappingSerializer
from baserow.contrib.builder.api.data_sources.serializers import DataSourceSerializer
from baserow.contrib.builder.api.domains.errors import (
    ERROR_DOMAIN_DOES_NOT_EXIST,
    ERROR_DOMAIN_NOT_IN_BUILDER,
)
from baserow.contrib.builder.api.domains.serializers import (
    CreateDomainSerializer,
    DomainSerializer,
    OrderDomainsSerializer,
    PublicBuilderSerializer,
)
from baserow.contrib.builder.api.pages.errors import ERROR_PAGE_DOES_NOT_EXIST
from baserow.contrib.builder.data_sources.service import DataSourceService
from baserow.contrib.builder.domains.exceptions import (
    DomainDoesNotExist,
    DomainNotInBuilder,
)
from baserow.contrib.builder.domains.handler import DomainHandler
from baserow.contrib.builder.domains.models import Domain
from baserow.contrib.builder.domains.service import DomainService
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.elements.service import ElementService
from baserow.contrib.builder.errors import ERROR_BUILDER_DOES_NOT_EXIST
from baserow.contrib.builder.exceptions import BuilderDoesNotExist
from baserow.contrib.builder.handler import BuilderHandler
from baserow.contrib.builder.pages.exceptions import PageDoesNotExist
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.service import BuilderService
from baserow.core.exceptions import ApplicationDoesNotExist
from baserow.core.jobs.registries import job_type_registry
from baserow.core.services.registries import service_type_registry

from .serializers import PublicDataSourceSerializer, PublicElementSerializer


class DomainsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="builder_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Creates a domain for the application builder related to"
                "the provided value",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder domains"],
        operation_id="create_builder_domain",
        description="Creates a new domain for an application builder",
        request=CreateDomainSerializer,
        responses={
            200: DomainSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
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
        }
    )
    @validate_body(CreateDomainSerializer)
    def post(self, request, data: Dict, builder_id: int):
        builder = BuilderHandler().get_builder(builder_id)

        domain = DomainService().create_domain(
            request.user, builder, data["domain_name"]
        )

        serializer = DomainSerializer(domain)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="builder_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Gets all the domains for the specified builder",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder domains"],
        operation_id="get_builder_domains",
        description="Gets all the domains of a builder",
        responses={
            200: DomainSerializer(many=True),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                ]
            ),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, builder_id: int):
        builder = BuilderHandler().get_builder(builder_id)

        domains = DomainService().get_domains(
            request.user,
            builder,
        )

        serializer = DomainSerializer(domains, many=True)

        return Response(serializer.data)


class DomainView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="domain_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the domain",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder domains"],
        operation_id="update_builder_domain",
        description="Updates an existing domain of an application builder",
        request=CreateDomainSerializer,
        responses={
            200: DomainSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_DOMAIN_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            DomainDoesNotExist: ERROR_DOMAIN_DOES_NOT_EXIST,
        }
    )
    @validate_body(CreateDomainSerializer)
    def patch(self, request, data: Dict, domain_id: int):
        base_queryset = Domain.objects.select_for_update(of=("self",))

        domain = DomainService().get_domain(
            request.user, domain_id, base_queryset=base_queryset
        )

        domain_updated = DomainService().update_domain(request.user, domain, **data)

        serializer = DomainSerializer(domain_updated)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="domain_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the domain",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder domains"],
        operation_id="delete_builder_domain",
        description="Deletes an existing domain of an application builder",
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_DOMAIN_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            DomainDoesNotExist: ERROR_DOMAIN_DOES_NOT_EXIST,
        }
    )
    @transaction.atomic
    def delete(self, request, domain_id: int):
        base_queryset = Domain.objects.select_for_update(of=("self",))

        domain = DomainService().get_domain(
            request.user, domain_id, base_queryset=base_queryset
        )

        DomainService().delete_domain(request.user, domain)

        return Response(status=204)


class OrderDomainsView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="builder_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The builder the domain belongs to",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder domains"],
        operation_id="order_builder_domains",
        description="Apply a new order to the domains of a builder",
        request=OrderDomainsSerializer,
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_DOMAIN_NOT_IN_BUILDER",
                ]
            ),
            404: get_error_schema(
                ["ERROR_APPLICATION_DOES_NOT_EXIST", "ERROR_DOMAIN_DOES_NOT_EXIST"]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            DomainDoesNotExist: ERROR_DOMAIN_DOES_NOT_EXIST,
            DomainNotInBuilder: ERROR_DOMAIN_NOT_IN_BUILDER,
        }
    )
    @validate_body(OrderDomainsSerializer)
    def post(self, request, data: Dict, builder_id: int):
        builder = BuilderHandler().get_builder(builder_id)

        DomainService().order_domains(request.user, builder, data["domain_ids"])

        return Response(status=204)


class PublicBuilderByDomainNameView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="domain_name",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                description="Returns the builder published for the given domain name.",
            )
        ],
        tags=["Builder public"],
        operation_id="get_public_builder_by_domain_name",
        description=(
            "Returns the public serialized version of the builder for "
            "the given domain name and its pages ."
        ),
        responses={
            200: PublicBuilderSerializer,
            404: get_error_schema(["ERROR_BUILDER_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions({BuilderDoesNotExist: ERROR_BUILDER_DOES_NOT_EXIST})
    def get(self, request, domain_name):
        """
        Responds with a serialized version of the builder related to the query.
        Try to match a published builder for the given domain name. Used to display
        the public site.
        """

        builder = DomainService().get_public_builder_by_domain_name(
            request.user, domain_name
        )

        return Response(PublicBuilderSerializer(builder).data)


class PublicBuilderByIdView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="builder_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the builder related to the "
                "provided Id and its pages.",
            )
        ],
        tags=["Builder public"],
        operation_id="get_public_builder_by_id",
        description=(
            "Returns the public serialized version of the builder and its pages for "
            "the given builder id."
        ),
        responses={
            200: PublicBuilderSerializer,
            404: get_error_schema(["ERROR_BUILDER_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            BuilderDoesNotExist: ERROR_BUILDER_DOES_NOT_EXIST,
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, builder_id):
        """
        Returns a public version of the builder for the given id. This version can be
        used to display the preview before publishing.
        """

        builder = BuilderService().get_builder(request.user, builder_id)

        return Response(PublicBuilderSerializer(builder).data)


class AsyncPublishDomainView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="domain_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The builder application id the user wants to publish.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder domains"],
        operation_id="publish_builder_domain",
        description=(
            "This endpoint starts an asynchronous job to publish the builder. "
            "The job clones the current version of the given builder and publish it "
            "for the given domain."
        ),
        request=None,
        responses={
            204: None,
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
            DomainDoesNotExist: ERROR_DOMAIN_DOES_NOT_EXIST,
        }
    )
    def post(self, request, domain_id: int):
        """
        Starts an async job to publish a builder to the given domain.
        """

        domain = DomainHandler().get_domain(domain_id)

        job = DomainService().async_publish(request.user, domain)

        serializer = job_type_registry.get_serializer(job, JobSerializer)
        return Response(serializer.data, status=HTTP_202_ACCEPTED)


class PublicElementsView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the elements of the page related to the "
                "provided Id.",
            )
        ],
        tags=["Builder elements"],
        operation_id="list_public_builder_page_elements",
        description=(
            "Lists all the elements of the page related to the provided parameter. "
            "If the user is Anonymous, the page must belong to a published builder "
            "instance to being accessible."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                element_type_registry, PublicElementSerializer, many=True
            ),
            404: get_error_schema(["ERROR_PAGE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
        }
    )
    def get(self, request, page_id):
        """
        Responds with a list of serialized elements that belongs to the given page id.
        """

        page = PageHandler().get_page(page_id)

        elements = ElementService().get_elements(request.user, page)

        data = [
            element_type_registry.get_serializer(element, PublicElementSerializer).data
            for element in elements
        ]
        return Response(data)


class PublicDataSourcesView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only the data_sources of the page related to the "
                "provided Id if the related builder is public.",
            )
        ],
        tags=["Builder data sources"],
        operation_id="list_public_builder_page_data_sources",
        description=(
            "Lists all the data_sources of the page related to the provided parameter "
            "if the builder is public."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                service_type_registry, DataSourceSerializer, many=True
            ),
            404: get_error_schema(["ERROR_PAGE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
        }
    )
    def get(self, request, page_id):
        """
        Responds with a list of serialized data_sources that belong to the page if the
        user has access to it.
        """

        page = PageHandler().get_page(page_id)

        data_sources = DataSourceService().get_data_sources(request.user, page)

        data = [
            service_type_registry.get_serializer(
                data_source.service,
                PublicDataSourceSerializer,
                context={"data_source": data_source},
            ).data
            for data_source in data_sources
            if data_source.service and data_source.service.integration_id
        ]
        return Response(data)
