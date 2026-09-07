from typing import Literal, Optional, Tuple

TEXT_FORMAT_PLAIN: Literal["plain"] = "plain"
TEXT_FORMAT_MARKDOWN: Literal["markdown"] = "markdown"
TextFormat = Literal["plain", "markdown"]

# A stored text value (a formula string, or a plain string such as a collection
# field name) that begins with this sentinel is rendered as Markdown by the
# frontend. The sentinel is part of the *stored* value only: it must be stripped
# before the value is parsed, resolved, validated or displayed. Every consumer
# goes through `split_format` / `strip_format` below, nothing else should
# compare against the literal.
MARKDOWN_PREFIX = "__markdown__"


def split_format(value: Optional[str]) -> Tuple[TextFormat, Optional[str]]:
    """
    Splits a stored text value into its text format and the bare value.

    :param value: The stored value, with or without the Markdown sentinel.
    :return: A `(format, bare_value)` tuple. Non-string values are returned
        unchanged with the `plain` format.
    """

    if isinstance(value, str) and value.startswith(MARKDOWN_PREFIX):
        return TEXT_FORMAT_MARKDOWN, value[len(MARKDOWN_PREFIX) :]
    return TEXT_FORMAT_PLAIN, value


def strip_format(value: Optional[str]) -> Optional[str]:
    """
    Returns the bare value without the Markdown sentinel, if it has one.

    :param value: The stored value.
    :return: The value without its text format marker.
    """

    return split_format(value)[1]


def add_prefix(bare_value: str, text_format: TextFormat = TEXT_FORMAT_MARKDOWN) -> str:
    """
    Marks a bare value with the given text format.

    :param bare_value: The value without any text format marker.
    :param text_format: The text format the value should be rendered with.
    :return: The stored representation of the value.
    """

    if text_format == TEXT_FORMAT_MARKDOWN:
        return f"{MARKDOWN_PREFIX}{bare_value}"
    return bare_value
