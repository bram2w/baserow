from typing import Dict
from urllib.request import Request

from baserow_premium.api.views.errors import (
    ERROR_CANNOT_UPDATE_PREMIUM_ATTRIBUTES_ON_TEMPLATE,
)
from baserow_premium.api.views.exceptions import CannotUpdatePremiumAttributesOnTemplate
from baserow_premium.api.views.serializers import UpdatePremiumViewAttributesSerializer
from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.contrib.database.api.views.errors import ERROR_VIEW_DOES_NOT_EXIST
from baserow.contrib.database.api.views.serializers import ViewSerializer
from baserow.contrib.database.views.actions import UpdateViewActionType
from baserow.contrib.database.views.exceptions import ViewDoesNotExist
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.registries import view_type_registry
from baserow.core.action.registries import action_type_registry
from baserow.core.exceptions import UserNotInWorkspace


class PremiumViewAttributesView(APIView):
    """
    This view allows premium users to override attributes on a view which are only
    accessible to premium users. For example the logo can be hidden.
    """

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="view_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Sets show_logo of this view.",
            ),
        ],
        tags=["Database table views"],
        operation_id="premium_view_attributes_update",
        description="Sets view attributes only available for premium users.",
        request=UpdatePremiumViewAttributesSerializer,
        responses={
            200: ViewSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_FEATURE_NOT_AVAILABLE",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_CANNOT_UPDATE_PREMIUM_ATTRIBUTES_ON_TEMPLATE",
                ]
            ),
            404: get_error_schema(["ERROR_VIEW_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            CannotUpdatePremiumAttributesOnTemplate: ERROR_CANNOT_UPDATE_PREMIUM_ATTRIBUTES_ON_TEMPLATE,  # noqa
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
        }
    )
    @validate_body(UpdatePremiumViewAttributesSerializer)
    def patch(
        self,
        request: Request,
        view_id: int,
        data: Dict[str, any],
    ) -> Response:
        """
        Sets view attributes only available for premium users.
        """

        view_handler = ViewHandler()
        view = view_handler.get_view(view_id).specific
        workspace = view.table.database.workspace

        if workspace.has_template():
            raise CannotUpdatePremiumAttributesOnTemplate()

        LicenseHandler.raise_if_user_doesnt_have_feature(
            PREMIUM, request.user, workspace
        )

        view_type = view_type_registry.get_by_model(view)

        with view_type.map_api_exceptions():
            view = action_type_registry.get_by_type(UpdateViewActionType).do(
                request.user, view, **data
            )

        serializer = view_type_registry.get_serializer(
            view, ViewSerializer, context={"user": request.user}
        )
        return Response(serializer.data)
