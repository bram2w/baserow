from django.conf import settings

from drf_spectacular.plumbing import build_object_type
from rest_framework_simplejwt.settings import api_settings as jwt_settings

access_token_schema = {
    "access_token": {
        "type": "string",
        "description": "'access_token' can be used to authorize for other endpoints that require authorization. "
        "This token will be valid for {valid} minutes.".format(
            valid=int(
                settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds() / 60
            ),
        ),
    },
}

refresh_token_schema = {
    "refresh_token": {
        "type": "string",
        "description": "'refresh_token' can be used to get a new valid 'access_token'. "
        "This token will be valid for {valid} hours.".format(
            valid=int(
                settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds() / 3600
            ),
        ),
    }
}

authenticate_schema = build_object_type(
    {
        **access_token_schema,
        **refresh_token_schema,
    }
)

if jwt_settings.ROTATE_REFRESH_TOKENS:
    refresh_schema = build_object_type(
        {
            **access_token_schema,
            **refresh_token_schema,
        }
    )
else:
    refresh_schema = build_object_type(
        {
            **access_token_schema,
        }
    )
