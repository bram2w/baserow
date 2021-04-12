from drf_spectacular.plumbing import build_object_type


group_user_schema = build_object_type(
    {
        "order": {
            "type": "int",
            "description": "The order of the group, lowest first.",
            "example": 0,
        },
        "id": {
            "type": "int",
            "description": "The unique identifier of the group.",
            "example": 1,
        },
        "name": {
            "type": "string",
            "description": "The name given to the group.",
            "example": "Bram's group",
        },
    }
)
