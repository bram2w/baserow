from drf_spectacular.plumbing import build_object_type

row_names_response_schema = build_object_type(
    {
        "{table_id}*": {
            "type": "object",
            "description": "An object containing the row names of table `table_id`.",
            "properties": {
                "{row_id}*": {
                    "type": "string",
                    "description": (
                        "the name of the row with id `row_id` from table "
                        "with id `table_id`."
                    ),
                }
            },
        },
    },
)
