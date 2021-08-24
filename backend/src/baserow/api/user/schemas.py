from drf_spectacular.plumbing import build_object_type


create_user_response_schema = build_object_type(
    {
        "user": {
            "type": "object",
            "description": "An object containing information related to the user.",
            "properties": {
                "first_name": {
                    "type": "string",
                    "description": "The first name of related user.",
                },
                "username": {
                    "type": "string",
                    "format": "email",
                    "description": "The username of the related user. This is always "
                    "an email address.",
                },
                "language": {
                    "type": "string",
                    "description": "An ISO 639 language code (with optional variant) "
                    "selected by the user. Ex: en-GB.",
                },
            },
        },
        "token": {"type": "string"},
    }
)
authenticate_user_schema = create_user_response_schema
