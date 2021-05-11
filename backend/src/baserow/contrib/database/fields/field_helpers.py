import itertools
from typing import Dict, Any, List, Union, Tuple

from baserow.contrib.database.fields.models import NUMBER_TYPE_CHOICES
from baserow.contrib.database.fields.registries import field_type_registry

FieldKeywordArgPossibilities = Dict[str, Union[List[str], str]]


def map_dict_key_into_values(
    field_type_kwargs: FieldKeywordArgPossibilities,
) -> Dict[str, List[Tuple[str, str]]]:
    """
    Given a dictionary in the form of::

        {
            'key': 'value',
            'key2': ['value1', 'value2']
        }

    this function will convert the value of each key to be a list of tuples of the
    key and the value returning in the case of the above example::

        {
            'key': [('key', 'value')],
            'key2': [('key2', 'value1'), ('key2', 'value2')]
        }

    """
    pairs_dict = {}
    for name, options in field_type_kwargs.items():
        pairs_dict[name] = []
        if not isinstance(options, list):
            options = [options]
        for option in options:
            pairs_dict[name].append((name, option))
    return pairs_dict


def construct_all_possible_kwargs_for_field(
    field_type_kwargs: FieldKeywordArgPossibilities,
) -> List[Dict[str, Any]]:
    """
    Given a dictionary containing for each field type a dictionary of that
    field types kwargs and all of their associated possible values::

        {
            'field_type_name' : {
                'a_kwarg_for_this_field_type' : ['optionOne', 'optionTwo'],
                'other_kwarg_for_this_field_type' : [True, False],
                'final_kwarg_for_this_field_type' : 'constant'
            }
        }

    This function will create a list of instantiated kwargs per field type, the list
    will contain every possible combination of the supplied possible values for the
    fields kwargs. For example given the dict above this would be the result::

        {
            'field_type_name' : [
                {
                    'a_kwarg_for_this_field_type' : 'optionOne'
                    'other_kwarg_for_this_field_type' : True,
                    'final_kwarg_for_this_field_type' : 'constant'
                },
                {
                    'a_kwarg_for_this_field_type' : 'optionTwo'
                    'other_kwarg_for_this_field_type' : True,
                    'final_kwarg_for_this_field_type' : 'constant'
                },
                {
                    'a_kwarg_for_this_field_type' : 'optionOne'
                    'other_kwarg_for_this_field_type' : False,
                    'final_kwarg_for_this_field_type' : 'constant'
                },
                {
                    'a_kwarg_for_this_field_type' : 'optionTwo'
                    'other_kwarg_for_this_field_type' : False,
                    'final_kwarg_for_this_field_type' : 'constant'
                },
            ]
        }

    """
    dict_of_kwarg_value_pairs = map_dict_key_into_values(field_type_kwargs)
    all_possible_kwargs = [
        dict(pairwise_args)
        for pairwise_args in itertools.product(*dict_of_kwarg_value_pairs.values())
    ]

    return all_possible_kwargs


def construct_all_possible_field_kwargs(link_table) -> Dict[str, List[Dict[str, Any]]]:
    """
    Some baserow field types have multiple different 'modes' which result in
    different different database columns and modes of operation being
    created. This function creates a dictionary of field type to a list of
    kwarg dicts, one for each interesting possible 'subtype' of the field.
    """
    extra_kwargs_for_type = {
        "date": {
            "date_include_time": [True, False],
        },
        "number": {
            "number_type": [number_type for number_type, _ in NUMBER_TYPE_CHOICES],
            "number_negative": [True, False],
        },
        "link_row": {"link_row_table": link_table},
    }

    all_possible_kwargs_per_type = {}
    for field_type_name in field_type_registry.get_types():
        extra_kwargs = extra_kwargs_for_type.get(field_type_name, {})
        all_possible_kwargs = construct_all_possible_kwargs_for_field(extra_kwargs)
        all_possible_kwargs_per_type[field_type_name] = all_possible_kwargs

    return all_possible_kwargs_per_type
