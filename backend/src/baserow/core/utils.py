import csv
import os
import re
import random
import string
import hashlib
import math

from collections import namedtuple
from typing import List

from django.db.models import ForeignKey
from django.db.models.fields import NOT_PROVIDED


def extract_allowed(values, allowed_fields):
    """
    Returns a new dict with the values of the key names that are in the allowed_fields.
    The other keys are ignored.

    Example:
        object_1 = {
            'value_1': 'value',
            'value_2': 'value'
        }

        extract_allowed(object_1, ['value_1'])
        >> {'value_1': 'value'}

    :param values: A dict containing the values.
    :type dict:
    :param allowed_fields: A list containing the keys of the values that need to be
        extracted from the values.
    :type allowed_fields: list
    :return: The extracted values.
    :rtype: dict
    """

    allowed_values = {}
    for field in allowed_fields:
        if field in values:
            allowed_values[field] = values[field]

    return allowed_values


def set_allowed_attrs(values, allowed_fields, instance):
    """
    Sets the attributes of the instance with the values of the key names that are in the
    allowed_fields. The other keys are ignored.

    Examples:
        class Tmp(object):
            value_1 = 'value'
            value_2 = 'value'

        object_1 = {
            'value_1': 'value_2',
            'value_2': 'value_2'
        }

        tmp = set_allowed_attrs(object_1, ['value_1'], Tmp())
        tmp.value_1
        >> 'value_2'
        tmp.value_2
        >> 'value'

    :param values: The dict containing the values.
    :type values: dict
    :param allowed_fields: A list containing the keys of the value that need to be set
        on the instance.
    :type allowed_fields: list
    :param instance: The instance of which the attributes must be updated.
    :type instance: object
    :return: The updated instance.
    """

    for field in allowed_fields:
        if field in values:
            setattr(instance, field, values[field])

    return instance


def to_pascal_case(value):
    """
    Converts the value string to PascalCase.

    :param value: The value that needs to be converted.
    :type value: str
    :return: The value in PascalCase.
    :rtype: str
    """

    return "".join(character for character in value.title() if not character.isspace())


def to_snake_case(value):
    """
    Converts the value string to snake_case.

    :param value: The value that needs to be converted.
    :type value: str
    :return: The value in snake_case.
    :rtype: str
    """

    return re.sub(" +", " ", value).lower().replace(" ", "_").strip()


def remove_special_characters(value, remove_spaces=True):
    """
    Removes all special characters from a string, so only [a-Z] and [0-9] stay.

    :param value: The value where the characters need to be removed from.
    :type value: str
    :param remove_spaces: If true the spaces are also going to be removed.
    :type remove_spaces: bool
    :return: The value in without special characters
    :rtype: str
    """

    return "".join(
        character
        for character in value
        if character.isalnum() or (character == " " and not remove_spaces)
    )


def model_default_values(model_class, not_provided=None):
    """
    Figures out which default values the fields of a model have and returns those
    as a dict.

    :param model_class: The model that contains the fields for which we need to get
        the default values.
    :type model_class: Model
    :return: A dict containing the field name as a key and the default value as value.
    :rtype: dict
    """

    return {
        field.name: (
            field.default if field.default is not NOT_PROVIDED else not_provided
        )
        for field in model_class._meta.get_fields()
        if hasattr(field, "default")
    }


def dict_to_object(values, name="Struct"):
    """
    Converts a dict to an object.

    :param values: The dict containing the values that need to be converted to an
        object.
    :type values:
    :param name: The name of the object.
    :type name: str
    :return: The object with the same attributes as the provided values.
    :rtype: object
    """

    return namedtuple(name, values.keys())(*values.values())


def random_string(length):
    """
    Generates a random string with a given length containing letters and digits.

    :param length: The amount of characters in the string.
    :type length: int
    :return: The randomly generated string
    :type: str
    """

    return "".join(
        random.SystemRandom().choice(string.ascii_letters + string.digits)
        for _ in range(length)
    )


def sha256_hash(stream, block_size=65536):
    """
    Calculates a sha256 hash for the contents of the provided stream.

    :param stream: The stream of the content where to calculate the hash for.
    :type stream: IOStream
    :param block_size: The amount of bytes that are read each time.
    :type block_size: int
    :return: The calculated hash.
    :rtype: str
    """

    stream.seek(0)
    hasher = hashlib.sha256()
    for stream_chunk in iter(lambda: stream.read(block_size), b""):
        hasher.update(stream_chunk)
    stream.seek(0)
    return hasher.hexdigest()


def stream_size(stream):
    """
    Calculates the total amount of bytes of the stream's content.

    :param stream: The stream of the content where to calculate the size for.
    :type stream: IOStream
    :return: The total size of the stream.
    :rtype: int
    """

    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    return size


def truncate_middle(content, max_length, middle="..."):
    """
    Truncates the middle part of the string if the total length if too long.

    For example:
    truncate_middle('testabcdecho', 8) == 'tes...ho'

    :param content: The string that must be truncated.
    :type: str
    :param max_length: The maximum amount of characters the string can have.
    :type max_length: int
    :param middle: The part that must be added in the middle if the provided
        content is too long.
    :type middle str
    :return: The truncated string.
    :rtype: str
    """

    if len(content) <= max_length:
        return content

    if max_length <= len(middle):
        raise ValueError(
            "The max_length cannot be lower than the length if the " "middle string."
        )

    total = max_length - len(middle)
    start = math.ceil(total / 2)
    end = math.floor(total / 2)

    left = content[:start]
    right = content[-end:] if end else ""

    return f"{left}{middle}{right}"


def split_comma_separated_string(comma_separated_string: str) -> List[str]:
    """
    Correctly splits a comma separated string which can contain quoted values to include
    commas in individual items like so: 'A,"B , C",D' -> ['A', 'B , C', 'D'] or using
    backslashes to escape double quotes like so: 'A,\"B,C' -> ['A', '"B', 'C'].

    :param comma_separated_string: The string to split
    :return: A list of split items from the provided string.
    """

    # Use python's csv handler as it knows how to handle quoted csv values etc.
    # csv.reader returns an iterator, we use next to get the first split row back.
    return next(
        csv.reader(
            [comma_separated_string], delimiter=",", quotechar='"', escapechar="\\"
        )
    )


def get_model_reference_field_name(lookup_model, target_model):
    """
    Figures out what the name of the field related to the `target_model` is in the
    `lookup_model`. So if the `lookup_model` has a ForeignKey pointing to the
    `target_model`, then the name of that field will be returned.

    :param lookup_model: The model that should contain the ForeignKey pointing at the
        `target_model`.
    :type lookup_model: Model
    :param target_model: The model that the ForeignKey in the `lookup_model` must be
        pointing to.
    :type target_model: Model
    :return: The name of the field.
    :rtype: str | None
    """

    # We have to loop over all the fields, check if it is a ForeignKey and check if
    # the related model is the `target_model`. We can't use isinstance to check if
    # the model is a child of View because that doesn't work with models, so we need
    # to create a tuple of parent classes and check if the `target_model` is in them.
    for field in lookup_model._meta.get_fields():
        if isinstance(field, ForeignKey) and field.related_model:
            classes = tuple(field.related_model._meta.parents.keys()) + (
                field.related_model,
            )
            if any([target_model == c for c in classes]):
                return field.name

    return None
