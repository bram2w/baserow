from django.db import transaction
from django.db.models import Count

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions
from baserow.api.schemas import get_error_schema
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST
from baserow.core.models import Group
from baserow.core.handler import CoreHandler
from baserow.core.exceptions import GroupDoesNotExist
from baserow_premium.admin.groups.exceptions import CannotDeleteATemplateGroupError
from baserow_premium.api.admin.views import AdminListingView
from baserow_premium.admin.groups.handler import GroupsAdminHandler
from baserow_premium.license.handler import check_active_premium_license

from .errors import ERROR_CANNOT_DELETE_A_TEMPLATE_GROUP
from .serializers import GroupsAdminResponseSerializer


class GroupsAdminView(AdminListingView):
    serializer_class = GroupsAdminResponseSerializer
    search_fields = ["id", "name"]
    sort_field_mapping = {
        "id": "id",
        "name": "name",
        "application_count": "application_count",
        "created_on": "created_on",
    }

    def get_queryset(self, request):
        return (
            Group.objects.prefetch_related("groupuser_set", "groupuser_set__user")
            .annotate(
                application_count=Count("application"), template_count=Count("template")
            )
            .exclude(template_count__gt=0)
        )

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_list_groups",
        description="Returns all groups with detailed information on each group, "
        "if the requesting user is staff.\n\nThis is a **premium** feature.",
        **AdminListingView.get_extend_schema_parameters(
            "groups", serializer_class, search_fields, sort_field_mapping
        ),
    )
    def get(self, request):
        check_active_premium_license(request.user)
        return super().get(request)


class GroupAdminView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_delete_group",
        description="Deletes the specified group and the applications inside that "
        "group, if the requesting user is staff. \n\nThis is a **premium** feature.",
        parameters=[
            OpenApiParameter(
                name="group_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the group to delete",
            ),
        ],
        responses={
            204: None,
            400: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
            401: None,
        },
    )
    @map_exceptions(
        {
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            CannotDeleteATemplateGroupError: ERROR_CANNOT_DELETE_A_TEMPLATE_GROUP,
        }
    )
    @transaction.atomic
    def delete(self, request, group_id):
        """Deletes the specified group"""

        group = CoreHandler().get_group(
            group_id, base_queryset=Group.objects.select_for_update()
        )
        handler = GroupsAdminHandler()
        handler.delete_group(request.user, group)

        return Response(status=204)
