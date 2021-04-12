grid_view_field_options_schema = {
    "type": "object",
    "description": "An object containing the field id as key and the "
    "properties related to view as value.",
    "properties": {
        "1": {
            "type": "object",
            "description": "Properties of field with id 1 of the related view.",
            "properties": {
                "width": {
                    "type": "integer",
                    "example": 200,
                    "description": "The width of the table field in the related view.",
                },
                "hidden": {
                    "type": "boolean",
                    "example": True,
                    "description": "Whether or not the field should be hidden in the "
                    "current view.",
                },
                "order": {
                    "type": "integer",
                    "example": 0,
                    "description": "The position that the field has within the view, "
                    "lowest first. If there is another field with the "
                    "same order value then the field with the lowest "
                    "id must be shown first.",
                },
            },
        },
    },
}
