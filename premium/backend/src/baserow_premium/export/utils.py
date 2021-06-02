from typing import Union

from xml.sax.saxutils import escape


def get_unique_name(
    data: dict, base_name: str, count: Union[int, None] = None, separator: str = "_"
) -> str:
    """
    Check if the given `base_name` already exists as data key, if so it will keep
    trying to generate a new name based on the separator and count. If `name` for
    example is already taken, then `name_2` will be checked, if that is taken `name_3`
    and so forth.

    :param data: The object where the existence of the name as a key will be checked in.
    :param base_name: The name that will be checked in the data dict.
    :param count: The recursive count that must be checked.
    :param separator: The character that is placed between the `base_name` and the
        `count`.
    :return: The name that does not exist as key in the data dict.
    """

    keys = data.keys()

    new_name = f"{base_name}{separator}{count}" if count else base_name

    if new_name not in keys:
        return new_name

    return get_unique_name(data, base_name, count + 1 if count else 2, separator)


def safe_xml_tag_name(
    name: str, numeric_prefix: str = "tag-", empty_fallback: str = "empty-tag"
) -> str:
    """
    Returns a safe xml tag name by replacing invalid characters with a dash.

    :param name: The name that must be converted to a safe xml tag name.
    :param numeric_prefix: An xml tag name can't start with a number, so if that is
        the case, then this value will be prepended.
    :param empty_fallback: An xml tag name can't be empty, so if that is the case,
        then this fallback value will be returned.
    :return: A safe name that can be used as xml tag.
    """

    safe_name = ""

    for char in name:
        if char.isalnum():
            safe_name += char
        else:
            safe_name += "-"

    while "--" in safe_name:
        safe_name = safe_name.replace("--", "-")

    if safe_name.startswith("-"):
        safe_name = safe_name[1:]

    if safe_name.endswith("-"):
        safe_name = safe_name[:-1]

    if len(safe_name) > 0 and safe_name[0].isnumeric():
        safe_name = f"{numeric_prefix}{safe_name}"

    if len(safe_name) == 0:
        return empty_fallback

    return safe_name


def to_xml(val):
    """
    Encodes the given python value into an xml string. Does not return an entire
    xml document but instead a fragment just representing this value.

    :return: A string containing an xml fragment for the provided value.
    """

    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, dict):
        return "".join([to_xml_elem(key, to_xml(val)) for key, val in val.items()])
    if isinstance(val, list):
        return "".join([to_xml_elem("item", to_xml(item)) for item in val])
    return escape(str(val))


def to_xml_elem(key, val):
    """
    Returns an xml element of type key containing the val, unless val is the
    empty string when it returns a closed xml element.

    :param key: The xml tag of the element to generate. This must be a valid xml tag
        name because it is not escaped.
    :param val: The value of the element to generate.
    :return: An xml element string.
    """

    if val == "":
        return f"<{key}/>"
    else:
        return f"<{key}>{val}</{key}>"
