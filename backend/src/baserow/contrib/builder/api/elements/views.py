from typing import Dict

from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import (
    map_exceptions,
    validate_body,
    validate_body_custom_fields,
)
from baserow.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from baserow.api.utils import (
    CustomFieldRegistryMappingSerializer,
    DiscriminatorCustomFieldsMappingSerializer,
    type_from_data_or_registry,
    validate_data_custom_fields,
)
from baserow.contrib.builder.api.elements.errors import (
    ERROR_ELEMENT_DOES_NOT_EXIST,
    ERROR_ELEMENT_NOT_IN_PAGE,
)
from baserow.contrib.builder.api.elements.serializers import (
    CreateElementSerializer,
    ElementSerializer,
    OrderElementsSerializer,
    UpdateElementSerializer,
)
from baserow.contrib.builder.api.pages.errors import ERROR_PAGE_DOES_NOT_EXIST
from baserow.contrib.builder.elements.exceptions import (
    ElementDoesNotExist,
    ElementNotInPage,
)
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.models import Element
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.elements.service import ElementService
from baserow.contrib.builder.pages.exceptions import PageDoesNotExist
from baserow.contrib.builder.pages.handler import PageHandler


class ElementsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only the elements of the page related to the "
                "provided Id.",
            )
        ],
        tags=["Builder page elements"],
        operation_id="list_builder_page_elements",
        description=(
            "Lists all the elements of the page related to the provided parameter if "
            "the user has access to the related builder's workspace. "
            "If the workspace is related to a template, then this endpoint will be "
            "publicly accessible."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                element_type_registry, ElementSerializer, many=True
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
        Responds with a list of serialized elements that belong to the page if the user
        has access to that page.
        """

        page = PageHandler().get_page(page_id)

        elements = ElementService().get_elements(request.user, page)

        data = [
            element_type_registry.get_serializer(element, ElementSerializer).data
            for element in elements
        ]
        return Response(data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Creates an element for the builder page related to the "
                "provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder page elements"],
        operation_id="create_builder_page_element",
        description="Creates a new builder element",
        request=DiscriminatorCustomFieldsMappingSerializer(
            element_type_registry,
            CreateElementSerializer,
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                element_type_registry, ElementSerializer
            ),
            400: get_error_schema(
                [
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
    @validate_body_custom_fields(
        element_type_registry, base_serializer_class=CreateElementSerializer
    )
    def post(self, request, data: Dict, page_id: int):
        """Creates a new element."""

        type_name = data.pop("type")
        page = PageHandler().get_page(page_id)

        before_id = data.pop("before_id", None)
        before = ElementHandler().get_element(before_id) if before_id else None

        element_type = element_type_registry.get(type_name)
        element = ElementService().create_element(
            request.user, element_type, page, before=before, **data
        )

        serializer = element_type_registry.get_serializer(element, ElementSerializer)
        return Response(serializer.data)


class OrderElementsPageView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The page id we want to order the elements for.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder page elements"],
        operation_id="order_builder_page_elements",
        description="Apply a new order to the elements of the given page.",
        request=OrderElementsSerializer,
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_ELEMENT_NOT_IN_PAGE",
                ]
            ),
            404: get_error_schema(["ERROR_PAGE_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
            ElementNotInPage: ERROR_ELEMENT_NOT_IN_PAGE,
        }
    )
    @validate_body(OrderElementsSerializer)
    def post(self, request, data: Dict, page_id: int):
        """
        Change order of the pages to the given order.
        """

        page = PageHandler().get_page(page_id)

        ElementService().order_elements(request.user, page, data["element_ids"])

        return Response(status=204)


class ElementView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="element_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the element",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder page elements"],
        operation_id="update_builder_page_element",
        description="Updates an existing builder element.",
        request=CustomFieldRegistryMappingSerializer(
            element_type_registry,
            UpdateElementSerializer,
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                element_type_registry, ElementSerializer
            ),
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_ELEMENT_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            ElementDoesNotExist: ERROR_ELEMENT_DOES_NOT_EXIST,
        }
    )
    def patch(self, request, element_id: int):
        """
        Update an element.
        """

        element = ElementHandler().get_element(
            element_id,
            base_queryset=Element.objects.select_for_update(of=("self",)),
        )
        type_name = type_from_data_or_registry(
            request.data, element_type_registry, element
        )
        data = validate_data_custom_fields(
            type_name,
            element_type_registry,
            request.data,
            base_serializer_class=UpdateElementSerializer,
        )

        element_updated = ElementService().update_element(request.user, element, **data)

        serializer = element_type_registry.get_serializer(
            element_updated, ElementSerializer
        )
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="element_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the element",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder page elements"],
        operation_id="delete_builder_page_element",
        description="Deletes the element related by the given id.",
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_ELEMENT_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            ElementDoesNotExist: ERROR_ELEMENT_DOES_NOT_EXIST,
        }
    )
    @transaction.atomic
    def delete(self, request, element_id: int):
        """
        Deletes an element.
        """

        element = ElementHandler().get_element(
            element_id,
            base_queryset=Element.objects.select_for_update(of=("self",)),
        )

        ElementService().delete_element(request.user, element)

        return Response(status=204)
