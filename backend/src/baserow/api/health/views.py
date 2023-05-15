import traceback
from typing import Any, Dict

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import validate_body
from baserow.api.health.serializers import (
    EmailTesterRequestSerializer,
    EmailTesterResponseSerializer,
    FullHealthCheckSerializer,
)
from baserow.api.schemas import get_error_schema
from baserow.core.health.handler import HealthCheckHandler


class FullHealthCheckView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Health"],
        request=None,
        operation_id="full_health_check",
        description="Runs a full health check testing as many services and systems "
        "as possible. These health checks can be expensive operations such as writing "
        "files to storage etc.",
        responses={
            200: FullHealthCheckSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        result = HealthCheckHandler.run_all_checks()
        return Response(
            FullHealthCheckSerializer(
                {"checks": result.checks, "passing": result.passing}
            ).data
        )


class EmailTesterView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Health"],
        request=EmailTesterRequestSerializer,
        operation_id="email_tester",
        description="Sends a test email to the provided email address. Useful for "
        "testing Baserow's email configuration as errors are clearly "
        "returned.",
        responses={
            200: EmailTesterResponseSerializer,
            400: get_error_schema(["ERROR_REQUEST_BODY_VALIDATION"]),
        },
    )
    @validate_body(EmailTesterRequestSerializer, return_validated=True)
    def post(self, request: Request, data: Dict[str, Any]) -> Response:
        target_email = data["target_email"]
        try:
            HealthCheckHandler.send_test_email(target_email)
            return Response(EmailTesterResponseSerializer({"succeeded": True}).data)
        except Exception as e:
            full = traceback.format_exc()
            return Response(
                EmailTesterResponseSerializer(
                    {
                        "succeeded": False,
                        "error_type": e.__class__.__name__,
                        "error_stack": full,
                        "error": str(e),
                    }
                ).data
            )
