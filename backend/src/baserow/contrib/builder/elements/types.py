from typing import TypeVar

from baserow.contrib.builder.types import ElementDict

from .models import Element

Expression = str

ElementDictSubClass = TypeVar("ElementDictSubClass", bound=ElementDict)
ElementSubClass = TypeVar("ElementSubClass", bound=Element)
