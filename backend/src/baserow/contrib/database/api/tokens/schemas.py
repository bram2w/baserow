token_permissions_field_value_schema = {
    "anyOf": [
        {
            "type": "boolean",
            "description": "Indicating if the API token has permissions to all tables.",
            "example": True,
        },
        {
            "type": "array",
            "items": {
                "type": "array",
                "minItems": 2,
                "maxItems": 2,
                "items": {
                    "anyOf": [
                        {
                            "type": "string",
                            "example": "database",
                            "description": "First element should indicate the "
                            "reference type `database` or `table`.",
                        },
                        {
                            "type": "number",
                            "example": 1,
                            "description": "Second element should indicate the ID of "
                            "the reference.",
                        },
                    ]
                },
            },
        },
    ]
}

token_permissions_field_schema = {
    "type": "object",
    "description": (
        "Indicates per operation which permissions the API token has within the whole "
        "group. If the value of for example `create` is `true`, then the token can "
        "create rows in all tables related to the group. If a list is provided with "
        'for example `[["table", 1]]` then the token only has create permissions for '
        "the table with id 1. Same goes for if a database references is provided. "
        '`[["database", 1]]` means create permissions for all tables in the database '
        "with id 1.\n\n"
        "Example:\n"
        "```json\n"
        "{\n"
        '  "create": true// Allows creating rows in all tables.\n'
        "  // Allows reading rows from database 1 and table 10.\n"
        '  "read": [["database", 1], ["table", 10]],\n'
        '  "update": false  // Denies updating rows in all tables.\n'
        '  "delete": []  // Denies deleting rows in all tables.\n '
        "}\n"
        "```"
    ),
    "properties": {
        "create": token_permissions_field_value_schema,
        "read": token_permissions_field_value_schema,
        "update": token_permissions_field_value_schema,
        "delete": token_permissions_field_value_schema,
    },
}
