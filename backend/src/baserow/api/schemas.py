from django.conf import settings
from drf_spectacular.plumbing import build_object_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter


def get_error_schema(errors=None):
    return build_object_type(
        {
            "error": {
                "type": "string",
                "description": "Machine readable error indicating what went wrong.",
                "enum": errors,
            },
            "detail": {
                "oneOf": [
                    {
                        "type": "string",
                        "format": "string",
                        "description": "Human readable details about what went wrong.",
                    },
                    {
                        "type": "object",
                        "format": "object",
                        "description": "Machine readable object about what went wrong.",
                    },
                ]
            },
        }
    )


CLIENT_SESSION_ID_SCHEMA_PARAMETER = OpenApiParameter(
    name=settings.CLIENT_SESSION_ID_HEADER,
    location=OpenApiParameter.HEADER,
    type=OpenApiTypes.UUID,
    required=False,
    description="An optional header that marks the action performed by this request "
    "as having occurred in a particular client session. Then using the undo/redo "
    f"endpoints with the same {settings.CLIENT_SESSION_ID_HEADER} header this action "
    "can be undone/redone.",
)
