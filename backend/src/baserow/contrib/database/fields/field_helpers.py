from typing import Dict, Any, List

from baserow.contrib.database.fields.registries import field_type_registry


def construct_all_possible_field_kwargs(
    link_table, decimal_link_table, file_link_table
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Some baserow field types have multiple different 'modes' which result in
    different different database columns and modes of operation being
    created. This function creates a dictionary of field type to a list of
    kwarg dicts, one for each interesting possible 'subtype' of the field.
    """
    all_interesting_field_kwargs = {
        "text": [{"name": "text"}],
        "long_text": [{"name": "long_text"}],
        "url": [{"name": "url"}],
        "email": [{"name": "email"}],
        "number": [
            {"name": "negative_int", "number_type": "INTEGER", "number_negative": True},
            {
                "name": "positive_int",
                "number_type": "INTEGER",
                "number_negative": False,
            },
            {
                "name": "negative_decimal",
                "number_type": "DECIMAL",
                "number_negative": "True",
            },
            {
                "name": "positive_decimal",
                "number_type": "DECIMAL",
                "number_negative": False,
            },
        ],
        "boolean": [{"name": "boolean"}],
        "date": [
            {"name": "datetime_us", "date_include_time": True, "date_format": "US"},
            {"name": "date_us", "date_include_time": False, "date_format": "US"},
            {"name": "datetime_eu", "date_include_time": True, "date_format": "EU"},
            {"name": "date_eu", "date_include_time": False, "date_format": "EU"},
        ],
        "last_modified": [
            {
                "name": "last_modified_datetime_us",
                "date_include_time": True,
                "date_format": "US",
                "timezone": "Europe/Berlin",
            },
            {
                "name": "last_modified_date_us",
                "date_include_time": False,
                "date_format": "US",
                "timezone": "Europe/Berlin",
            },
            {
                "name": "last_modified_datetime_eu",
                "date_include_time": True,
                "date_format": "EU",
                "timezone": "Europe/Berlin",
            },
            {
                "name": "last_modified_date_eu",
                "date_include_time": False,
                "date_format": "EU",
                "timezone": "Europe/Berlin",
            },
        ],
        "created_on": [
            {
                "name": "created_on_datetime_us",
                "date_include_time": True,
                "date_format": "US",
                "timezone": "Europe/Berlin",
            },
            {
                "name": "created_on_date_us",
                "date_include_time": False,
                "date_format": "US",
                "timezone": "Europe/Berlin",
            },
            {
                "name": "created_on_datetime_eu",
                "date_include_time": True,
                "date_format": "EU",
                "timezone": "Europe/Berlin",
            },
            {
                "name": "created_on_date_eu",
                "date_include_time": False,
                "date_format": "EU",
                "timezone": "Europe/Berlin",
            },
        ],
        "link_row": [
            {"name": "link_row", "link_row_table": link_table},
            {"name": "decimal_link_row", "link_row_table": decimal_link_table},
            {"name": "file_link_row", "link_row_table": file_link_table},
        ],
        "file": [{"name": "file"}],
        "single_select": [
            {
                "name": "single_select",
                "select_options": [
                    {"id": 0, "value": "A", "color": "red"},
                    {"id": 1, "value": "B", "color": "blue"},
                ],
            }
        ],
        "multiple_select": [
            {
                "name": "multiple_select",
                "select_options": [
                    {"id": 2, "value": "C", "color": "orange"},
                    {"id": 3, "value": "D", "color": "yellow"},
                    {"id": 4, "value": "E", "color": "green"},
                ],
            }
        ],
        "phone_number": [{"name": "phone_number"}],
    }
    # If you have added a new field please add an entry into the dict above with any
    # test worthy combinations of kwargs
    assert set(field_type_registry.get_types()) == set(
        all_interesting_field_kwargs.keys()
    ), "Please add the new field type to the testing dictionary of interesting kwargs"
    return all_interesting_field_kwargs
