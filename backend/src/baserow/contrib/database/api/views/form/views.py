from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.fields import empty
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from baserow.api.decorators import map_exceptions
from baserow.api.schemas import get_error_schema
from baserow.api.utils import validate_data
from baserow.api.pagination import PageNumberPagination
from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.contrib.database.api.rows.serializers import (
    get_row_serializer_class,
    get_example_row_serializer_class,
)
from baserow.contrib.database.api.fields.errors import ERROR_FIELD_DOES_NOT_EXIST
from baserow.contrib.database.api.fields.serializers import LinkRowValueSerializer
from baserow.contrib.database.fields.models import LinkRowField
from baserow.contrib.database.fields.exceptions import FieldDoesNotExist
from baserow.contrib.database.views.exceptions import ViewDoesNotExist
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import FormViewFieldOptions, FormView
from baserow.contrib.database.views.validators import required_validator

from .errors import ERROR_FORM_DOES_NOT_EXIST
from .serializers import PublicFormViewSerializer, FormViewSubmittedSerializer


class SubmitFormViewView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="slug",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                required=True,
                description="The slug related to the form form.",
            )
        ],
        tags=["Database table form view"],
        operation_id="get_meta_database_table_form_view",
        description=(
            "Returns the meta data related to the form view if the form is publicly "
            "shared or if the user has access to the related group. This data can be "
            "used to construct a form with the right fields."
        ),
        responses={
            200: PublicFormViewSerializer,
            404: get_error_schema(["ERROR_FORM_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            ViewDoesNotExist: ERROR_FORM_DOES_NOT_EXIST,
        }
    )
    def get(self, request, slug):
        form = ViewHandler().get_public_view_by_slug(
            request.user, slug, view_model=FormView
        )
        serializer = PublicFormViewSerializer(form)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="slug",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                required=True,
                description="The slug related to the form.",
            )
        ],
        tags=["Database table form view"],
        operation_id="submit_database_table_form_view",
        description=(
            "Submits the form if the form is publicly shared or if the user has "
            "access to the related group. The provided data will be validated based "
            "on the fields that are in the form and the rules per field. If valid, "
            "a new row will be created in the table."
        ),
        request=get_example_row_serializer_class(False),
        responses={
            200: FormViewSubmittedSerializer,
            404: get_error_schema(["ERROR_FORM_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            ViewDoesNotExist: ERROR_FORM_DOES_NOT_EXIST,
        }
    )
    @transaction.atomic
    def post(self, request, slug):
        handler = ViewHandler()
        form = handler.get_public_view_by_slug(request.user, slug, view_model=FormView)
        model = form.table.get_model()

        options = form.active_field_options
        field_kwargs = {
            model._field_objects[option.field_id]["name"]: {
                "required": True,
                "default": empty,
                "validators": [required_validator],
            }
            for option in options
            if option.required
        }
        field_ids = [option.field_id for option in options]
        validation_serializer = get_row_serializer_class(
            model, field_ids=field_ids, field_kwargs=field_kwargs
        )
        data = validate_data(validation_serializer, request.data)

        handler.submit_form_view(form, data, model, options)
        return Response(FormViewSubmittedSerializer(form).data)


class FormViewLinkRowFieldLookupView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="slug",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                required=True,
                description="The slug related to the form.",
            ),
            OpenApiParameter(
                name="field_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                required=True,
                description="The field id of the link row field.",
            ),
        ],
        tags=["Database table form view"],
        operation_id="database_table_form_view_link_row_field_lookup",
        description=(
            "If the form is publicly shared or if an authenticated user has access to "
            "the related group, then this endpoint can be used to do a value lookup of "
            "the link row fields that are included in the form. Normally it is not "
            "possible for a not authenticated visitor to fetch the rows of a table. "
            "This endpoint makes it possible to fetch the id and primary field value "
            "of the related table of a link row included in the form view."
        ),
        responses={
            200: get_example_pagination_serializer_class(LinkRowValueSerializer),
            404: get_error_schema(
                ["ERROR_FORM_DOES_NOT_EXIST", "ERROR_FIELD_DOES_NOT_EXIST"]
            ),
        },
    )
    @map_exceptions(
        {
            ViewDoesNotExist: ERROR_FORM_DOES_NOT_EXIST,
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
        }
    )
    def get(self, request, slug, field_id):
        handler = ViewHandler()
        form = handler.get_public_view_by_slug(request.user, slug, view_model=FormView)
        link_row_field_content_type = ContentType.objects.get_for_model(LinkRowField)

        try:
            field_option = FormViewFieldOptions.objects.get(
                field_id=field_id,
                form_view=form,
                enabled=True,
                field__content_type=link_row_field_content_type,
            )
        except FormViewFieldOptions.DoesNotExist:
            raise FieldDoesNotExist("The form view field option does not exist.")

        search = request.GET.get("search")
        link_row_field = field_option.field.specific
        table = link_row_field.link_row_table
        primary_field = table.field_set.filter(primary=True).first()
        model = table.get_model(fields=[primary_field], field_ids=[])
        queryset = model.objects.all().enhance_by_fields()

        if search:
            queryset = queryset.search_all_fields(search)

        paginator = PageNumberPagination(limit_page_size=settings.ROW_PAGE_SIZE_LIMIT)
        page = paginator.paginate_queryset(queryset, request, self)
        serializer = LinkRowValueSerializer(
            page,
            many=True,
        )
        return paginator.get_paginated_response(serializer.data)
