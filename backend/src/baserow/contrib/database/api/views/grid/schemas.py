from drf_spectacular.plumbing import build_object_type

field_aggregation_response_schema = build_object_type(
    {
        "value": {
            "anyOf": [
                {
                    "type": "number",
                    "description": "The aggregation result for the specified field.",
                    "example": 5,
                },
                {
                    "type": "string",
                    "description": "The aggregation result for the specified field.",
                },
                {
                    "type": "array",
                    "items": {},
                    "description": "The aggregation result for the specified field.",
                },
                {
                    "type": "object",
                    "description": "The aggregation result for the specified field.",
                },
            ]
        },
        "total": {
            "type": "integer",
            "description": (
                "The total value count. Only returned if `include=total` "
                "is specified as GET parameter."
            ),
            "example": 7,
        },
    },
    required=["value"],
)


field_aggregations_response_schema = build_object_type(
    {
        "field_{id}": {
            "anyOf": [
                {
                    "type": "number",
                    "description": "The aggregation result for the field with id {id}.",
                    "example": 5,
                },
                {
                    "type": "string",
                    "description": "The aggregation result for the field with id {id}.",
                },
                {
                    "type": "array",
                    "items": {},
                    "description": "The aggregation result for the field with id {id}.",
                },
                {
                    "type": "object",
                    "description": "The aggregation result for the field with id {id}.",
                },
            ]
        },
        "total": {
            "type": "integer",
            "description": (
                "The total value count. Only returned if `include=total` "
                "is specified as GET parameter."
            ),
            "example": 7,
        },
    },
)
