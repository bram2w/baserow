from __future__ import annotations

import csv
import hashlib
import io
import math
import os
import random
import re
import string
from collections import namedtuple
from decimal import Decimal
from itertools import islice
from typing import Dict, Iterable, List, Optional, Tuple

from django.db import transaction
from django.db.models import ForeignKey
from django.db.models.fields import NOT_PROVIDED

from baserow.contrib.database.db.schema import optional_atomic


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


def get_non_unique_values(values: List) -> List:
    """
    Assembles all values that are not unique in the provided list
    """

    unique_values = set()
    non_unique_values = set()
    for value in values:
        if value in unique_values:
            non_unique_values.add(value)
        unique_values.add(value)
    return list(non_unique_values)


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
    r"""
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


def list_to_comma_separated_string(value_list: List[str]) -> str:
    """
    Converts the given list to a CSV compatible value. The result string can be parsed
    by a proper CSV parser. This function does the reverse as the previous one.

    :param value_list: List of value to convert.
    :return: A comma separated string.
    """

    out = io.StringIO()

    # Use python csv handler to convert the list to a string
    csv_writer = csv.writer(out, delimiter=",", quotechar='"', escapechar="\\")
    csv_writer.writerow(value_list)

    out.seek(0)
    result = out.read()

    # Strip removes the extra end line
    return result.strip()


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


def remove_invalid_surrogate_characters(content: bytes) -> str:
    """
    Removes illegal unicode characters from the provided content. If you for example
    run something like `b"\uD83D".encode("utf-8")`, it will result in a
    UnicodeEncodeError. This function removed the illegal characters, it keeps the
    valid emoji's.

    :param content: The content where the illegal unicode characters must be removed
        from.
    :return: Decoded string where the unicode illegal unicode characters are removed
        from.
    """

    return re.sub(r"\\u(d|D)([a-z|A-Z|0-9]{3})", "", content.decode("utf-8", "ignore"))


def split_ending_number(name: str) -> Tuple[str, str]:
    """
    Splits a string into two parts, the first part is the string before the last
    number, the second part is the last number.

    :param string: The string to split.
    :return: A tuple with the first part and the second part.
    """

    match = re.search(r"(.+) (\d+)$", name)
    if match:
        return match.group(1), match.group(2)
    return name, ""


def find_unused_name(
    variants_to_try: Iterable[str],
    existing_names: Iterable[str],
    max_length: int = None,
    suffix: str = " {0}",
):
    """
    Finds an unused name among the existing names. If no names in the provided
    variants_to_try list are available then the last name in that list will
    have a number appended which ensures it is an available unique name.
    Respects the maximally allowed name length. In case the variants_to_try
    are longer than that, they will get truncated to the maximally allowed length.

    :param variants_to_try: An iterable of name variant we want to try.
    :param existing_names: An iterable of all pre existing values.
    :param max_length: Set this value if you have a length limit to the new name.
    :param suffix: The suffix you want to append to the name to avoid
      duplicate. The string is going to be formated with a number.
    :return: The first available unused name.
    """

    existing_names_set = set(existing_names)

    if max_length is not None:
        variants_to_try = [item[0:max_length] for item in variants_to_try]

    remaining_names = set(variants_to_try) - existing_names_set
    # Some variants to try remain, let's return the first one
    if remaining_names:
        # Loop over to ensure we maintain the ordering provided by
        # variant_to_try, so we always return the first available name and
        # not any.
        for name in variants_to_try:
            if name in remaining_names:
                return name

    # None of the names in the param list are available, now using the last one lets
    # append a number to the name until we find a free one.
    original_name = variants_to_try[-1]

    i = 2
    while True:
        suffix_to_append = suffix.format(i)
        suffix_length = len(suffix_to_append)
        length_of_original_name_with_suffix = len(original_name) + suffix_length

        # At this point we know, that the original_name can only
        # be maximally the length of max_length. Therefore
        # if the length_of_original_name_with_suffix is longer
        # we can further truncate the name by the length of the
        # suffix.
        if max_length is not None and length_of_original_name_with_suffix > max_length:
            name = f"{original_name[:-suffix_length]}{suffix_to_append}"
        else:
            name = f"{original_name}{suffix_to_append}"

        if name not in existing_names_set:
            return name

        i += 1


def grouper(n: int, iterable: Iterable):
    """
    Groups the iterable by `n` per chunk and yields it.

    Solution from: https://stackoverflow.com/questions/8991506/iterate-an-iterator-by
    -chunks-of-n-in-python

    :param n: The amount of items per chunk.
    :param iterable: The iterable that must be grouped
    """

    it = iter(iterable)
    while True:
        chunk = tuple(islice(it, n))
        if not chunk:
            return
        yield chunk


def unique_dicts_in_list(
    list_of_dicts: List[Dict[str, any]], unique_fields: List["str"] = None
) -> Tuple[List[Dict[str, any]], List[Dict[str, any]]]:
    """
    This function provides you with a list of unique dicts within a list, and also
    tells you what dicts are duplicates.
    If you don't provide a `unique_fields` param the function will check for uniqueness
    of all the fields of the first dict.
    Please make sure that the dicts all have any field specific in `unique_fields` and
    are all the exact same structure if None is provided for `unique_fields`

    :param list_of_dicts: The list of dicts being filtered for uniqueness
    :param unique_fields: The fields which combined function as the unique constraint
    :return: The list of unique dicts and the duplicate dicts which have been filtered
        out.
    """

    if len(list_of_dicts) == 0:
        return [], []

    if unique_fields is None:
        unique_fields = list_of_dicts[0].keys()

    duplicates = []
    unique_items_map = {}
    for item in list_of_dicts:
        unique_values = []

        for unique_field in unique_fields:
            if unique_field not in item:
                raise ValueError(f"unique field {unique_field} does no exist on {item}")

            unique_values.append(item[unique_field])

        unique_values_tuple = tuple(unique_values)

        if unique_values_tuple in unique_items_map:
            duplicates.append(item)
        else:
            unique_items_map[unique_values_tuple] = item

    return list(unique_items_map.values()), duplicates


class Progress:
    """
    This helper class can be used to easily track progress of certain tasks. It's
    possible to register a child progress and reserve a range in the current progress.

    Example:
        def callback(percentage, state):
            print(f'{percentage}% {state}')

        progress = Progress(100)
        progress.register_updated_event(callback)

        for i in range(0, 10):
            sleep(0.1)
            progress.increment(state="First")

        sleep(1)
        progress.increment("Second", by=10)

        sub_progress = progress.create_child(50, 2)
        sub_progress.increment(state="Sub first")
        sleep(1)
        sub_progress.increment(state="Sub second")

        progress.increment(by=40)

    Output:
        1% First
        2% First
        3% First
        4% First
        5% First
        6% First
        8% First
        8% First
        9% First
        10% First
        20% Second
        45% Sub first
        70% Sub second
        100% None
    """

    def __init__(
        self,
        total: int,
        parent: Optional[Progress] = None,
        represents_progress: Optional[int] = None,
    ):
        """
        :param total: The total amount representing 100%. This means that the
            progress can be increment `total` times before reaching 100%.
        """

        self.total = total
        self.progress = 0
        self.updated_events = []
        self.parent = parent
        self.represents_progress = represents_progress
        self.last_parent_progress = 0

    def reset_with_total(self, total):
        self.progress = 0
        self.total = total

    def register_updated_event(self, event):
        """
        Register another callback event. The callback is expected to have two
        parameters, one for the percentage and one for the state.

        :param event: A function that should accept the `progress` and `state`
            arguments.
        """

        self.updated_events.append(event)

    def increment(self, by: Optional[int] = 1, state: Optional[str] = None):
        """
        Increments the progress with a given amount.

        :param by: How much the progress should be increment by. If the total is
            `100` and we increment by `1`, it will add 1%, but if we increment by `10`,
            it will add 10%.
        :param state: A descriptive name of the state. This could for example be
            "Downloading files."
        """

        self.progress += by

        if self.parent is not None:
            if self.progress >= self.total:
                new_parent_progress = self.represents_progress
            else:
                new_parent_progress = math.ceil(
                    (Decimal(self.progress) / self.total) * self.represents_progress
                )
            diff = new_parent_progress - self.last_parent_progress
            self.last_parent_progress = new_parent_progress
            if diff > 0:
                self.parent.increment(diff, state)

        percentage = math.ceil(Decimal(self.progress) / self.total * 100)
        for event in self.updated_events:
            event(percentage, state)

    def create_child(self, represents_progress: int, total: int):
        """
        Creates a child progress. Everytime the child progress increment, it will
        also update the current progress to reflect the increment.

        :param represents_progress: How much the child progress represents in this
            progress when it is at 100%. If this value would be `40` and the total is
            `100` and the child progress reaches 100%, it will increment the progress
            by 40.
        :param total: The total amount representing 100% of the child. This means
            that the progress can be increment `total` times before reaching 100%.
        """

        child_progress = Progress(
            parent=self, represents_progress=represents_progress, total=total
        )

        if child_progress.progress >= child_progress.total:
            self.increment(represents_progress)

        return child_progress

    def create_child_builder(self, represents_progress: int):
        """
        Creates a child progress. Everytime the child progress increment, it will
        also update the current progress to reflect the increment.

        :param represents_progress: How much the child progress represents in this
            progress when it is at 100%. If this value would be `40` and the total is
            `100` and the child progress reaches 100%, it will increment the progress
            by 40.
        """

        return ChildProgressBuilder(self, represents_progress)

    def track(self, represents_progress: int, state, iterable):
        child_progress = self.create_child(represents_progress, total=len(iterable))
        for i in iterable:
            yield i
            child_progress.increment(state=state)


class ChildProgressBuilder:
    def __init__(self, parent: Progress, represents_progress: int):
        self.represents_progress = represents_progress
        self.parent = parent

    @classmethod
    def build(cls, builder: Optional[ChildProgressBuilder], child_total: int):
        if builder is not None:
            parent = builder.parent
            represents_progress = builder.represents_progress
            return parent.create_child(represents_progress, child_total)
        else:
            return Progress(child_total)


class MirrorDict(dict):
    """
    This dict will always return the same value as the key. It can be used to
    replicate non existing mapping that must return the same values

    d = MirrorDict()
    d['test'] == 'test'
    d[1] == 1
    d.get('test') == 'test'
    """

    def __getitem__(self, key):
        return key

    def get(self, key, default=None):
        return key


def atomic_if_not_already():
    """
    Returns the context manager in `optional_atomic`, passing in the `atomic`
    arg using `get_autocommit` as its value. It allows us to only call
    `transaction.atomic` if we're not already in one.
    """

    return optional_atomic(transaction.get_autocommit())


def generate_hash(value: str):
    """
    Generates a hexadecimal hash given an input value. The same function is replicated
    in the frontend as `generateHash` such that the front and backend can share the
    same hashing algorithm.
    :param value: The value used to generate the hash
    :return: The hexadecimal hash of the value provided using sha256
    """

    value_hashed = hashlib.sha256()
    value_hashed.update(str(value).encode("UTF-8"))
    return value_hashed.hexdigest()
