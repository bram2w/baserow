from drf_spectacular.plumbing import build_object_type


field_aggregation_response_schema = build_object_type(
    {
        "value": {
            "type": "any",
            "description": "The aggregation result for the specified field.",
            "example": 5,
        },
        "total": {
            "type": "int",
            "description": (
                "The total value count. Only returned if `include=total` "
                "is specified as GET parameter."
            ),
            "example": 7,
        },
    },
    required=["value"],
)
