grid_view_field_options_schema = {
    'type': 'object',
    'description': 'An object containing the field id as key and the '
                   'properties related to view as value.',
    'properties': {
        '1': {
            'type': 'object',
            'description': 'Properties of field with id 1 of the related view.',
            'properties': {
                'width': {
                    'type': 'integer',
                    'example': 200,
                    'description': 'The width of the table field in the related view.'
                }
            }
        },
    }
}
