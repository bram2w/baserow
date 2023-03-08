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
from baserow.contrib.builder.api.pages.errors import (
    ERROR_PAGE_DOES_NOT_EXIST,
    ERROR_PAGE_NOT_IN_BUILDER,
)
from baserow.contrib.builder.api.pages.serializers import (
    CreatePageSerializer,
    OrderPagesSerializer,
    PageSerializer,
)
from baserow.contrib.builder.handler import BuilderHandler
from baserow.contrib.builder.pages.exceptions import PageDoesNotExist, PageNotInBuilder
from baserow.contrib.builder.pages.service import PageService
from baserow.core.exceptions import ApplicationDoesNotExist


class PagesView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="builder_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Creates a page for the application builder related to the "
                "provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder pages"],
        operation_id="create_builder_page",
        description="Creates a new page for an application builder",
        request=CreatePageSerializer,
        responses={
            200: PageSerializer,
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
    @validate_body(CreatePageSerializer)
    def post(self, request, data: Dict, builder_id: int):
        builder = BuilderHandler().get_builder(builder_id)

        page = PageService().create_page(request.user, builder, data["name"])

        serializer = PageSerializer(page)
        return Response(serializer.data)


class PageView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the page",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder pages"],
        operation_id="update_builder_page",
        description="Updates an existing page of an application builder",
        request=CreatePageSerializer,
        responses={
            200: PageSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_PAGE_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
        }
    )
    @validate_body(CreatePageSerializer)
    def patch(self, request, data: Dict, page_id: int):
        page = PageService().get_page(request.user, page_id)

        page_updated = PageService().update_page(request.user, page, **data)

        serializer = PageSerializer(page_updated)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the page",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder pages"],
        operation_id="delete_builder_page",
        description="Deletes an existing page of an application builder",
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_PAGE_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
        }
    )
    @transaction.atomic
    def delete(self, request, page_id: int):
        page = PageService().get_page(request.user, page_id)

        PageService().delete_page(request.user, page)

        return Response(status=204)


class OrderPagesView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="builder_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The builder the application belongs to",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder pages"],
        operation_id="order_builder_pages",
        description="Apply a new order to the pages of a builder",
        request=OrderPagesSerializer,
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_PAGE_NOT_IN_BUILDER",
                ]
            ),
            404: get_error_schema(
                ["ERROR_APPLICATION_DOES_NOT_EXIST", "ERROR_PAGE_DOES_NOT_EXIST"]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
            PageNotInBuilder: ERROR_PAGE_NOT_IN_BUILDER,
        }
    )
    @validate_body(OrderPagesSerializer)
    def post(self, request, data: Dict, builder_id: int):
        builder = BuilderHandler().get_builder(builder_id)

        PageService().order_pages(request.user, builder, data["page_ids"])

        return Response(status=204)
