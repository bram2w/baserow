import re
from baserow.core.utils import split_comma_separated_string
from baserow.contrib.database.fields.models import Field


def get_include_exclude_field_ids(table, include=None, exclude=None):
    """
    Returns a list containing the field ids based on the value
    of the include and exclude parameters.

    :param table: The table where to select the fields from. Field id's that are
        not in the table won't be included.
    :type table: Table
    :param include: The field ids that must be included. Only the provided ones
        are going to be in the returned queryset. Multiple can be provided
        separated by comma
    :type include: Optional[str]
    :param exclude: The field ids that must be excluded. Only the ones that are not
        provided are going to be in the returned queryset. Multiple can be provided
        separated by comma.
    :type exclude: Optional[str]
    :rtype: None or List[str]
    """

    fields = get_include_exclude_fields(table, include, exclude)
    field_ids = None

    if include is not None or exclude is not None:
        if fields:
            field_ids = [field.get("id") for field in fields.values()]
        else:
            field_ids = []

    return field_ids


def get_include_exclude_fields(
    table, include=None, exclude=None, user_field_names=False
):
    """
    Returns a field queryset containing the requested fields based on the value
    and exclude parameter.

    :param table: The table where to select the fields from. Field id's that are
        not in the table won't be included.
    :type table: Table
    :param include: The field ids that must be included. Only the provided ones
        are going to be in the returned queryset. Multiple can be provided
        separated by comma
    :type include: Optional[str]
    :param exclude: The field ids that must be excluded. Only the ones that are not
        provided are going to be in the returned queryset. Multiple can be provided
        separated by comma.
    :type exclude: Optional[str]
    :return: A Field's QuerySet containing the allowed fields based on the provided
        input.
    :param user_field_names: If true then the value and exclude parameters are
        retreated as a comma separated list of user field names instead of id's
    :type user_field_names: bool
    :rtype: QuerySet
    """

    queryset = Field.objects.filter(table=table)

    if user_field_names:
        includes = extract_field_names_from_string(include)
        excludes = extract_field_names_from_string(exclude)
        filter_type = "name__in"
    else:
        includes = extract_field_ids_from_string(include)
        excludes = extract_field_ids_from_string(exclude)
        filter_type = "id__in"

    if len(includes) == 0 and len(excludes) == 0:
        return None

    if len(includes) > 0:
        queryset = queryset.filter(**{filter_type: includes})

    if len(excludes) > 0:
        queryset = queryset.exclude(**{filter_type: excludes})

    return queryset


# noinspection PyMethodMayBeStatic
def extract_field_names_from_string(value):
    """
    Given a comma separated string of field names this function will split the
    string into a list of individual field names. For weird field names containing
    commas etc the field should be escaped with quotes.
    :param value: The string to split into a list of field names.
    :return: A list of field names.
    """

    if not value:
        return []

    return split_comma_separated_string(value)


def extract_field_ids_from_string(value):
    """
    Extracts the field ids from a string. Multiple ids can be separated by a comma.
    For example if you provide 'field_1,field_2' then [1, 2] is returned.

    :param value: A string containing multiple ids separated by comma.
    :type value: str
    :return: A list containing the field ids as integers.
    :rtype: list
    """

    if not value:
        return []

    return [
        int(re.sub("[^0-9]", "", str(v)))
        for v in value.split(",")
        if any(c.isdigit() for c in v)
    ]
