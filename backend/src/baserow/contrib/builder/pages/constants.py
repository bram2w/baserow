import re
import typing

from baserow.contrib.builder.pages.types import PAGE_PATH_PARAM_TYPE_CHOICES_LITERAL

# Every page param in a page path needs to be prefixed by the below symbol
PAGE_PATH_PARAM_PREFIX = ":"

PAGE_PATH_PARAM_TYPE_CHOICES = list(
    typing.get_args(PAGE_PATH_PARAM_TYPE_CHOICES_LITERAL)
)

PATH_PARAM_REGEX = re.compile("(:[A-Za-z0-9_]+)")
PATH_PARAM_EXACT_MATCH_REGEX = re.compile("(^:[A-Za-z0-9_]+)$")
