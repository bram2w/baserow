from typing import Dict

from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.applications.errors import ERROR_APPLICATION_DOES_NOT_EXIST
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from baserow.contrib.builder.api.domains.errors import (
    ERROR_DOMAIN_DOES_NOT_EXIST,
    ERROR_DOMAIN_NOT_IN_BUILDER,
    ERROR_ONLY_ONE_DOMAIN_ALLOWED,
)
from baserow.contrib.builder.api.domains.serializers import (
    CreateDomainSerializer,
    DomainSerializer,
    OrderDomainsSerializer,
)
from baserow.contrib.builder.domains.exceptions import (
    DomainDoesNotExist,
    DomainNotInBuilder,
    OnlyOneDomainAllowed,
)
from baserow.contrib.builder.domains.models import Domain
from baserow.contrib.builder.domains.service import DomainService
from baserow.contrib.builder.handler import BuilderHandler
from baserow.core.exceptions import ApplicationDoesNotExist


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
                    "ERROR_ONLY_ONE_DOMAIN_ALLOWED",
                ]
            ),
            404: get_error_schema(["ERROR_APPLICATION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            OnlyOneDomainAllowed: ERROR_ONLY_ONE_DOMAIN_ALLOWED,
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
