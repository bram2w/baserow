from typing import List, NewType, TypedDict, TypeVar

from baserow.contrib.builder.types import ElementDict

from ..workflow_actions.models import BuilderWorkflowAction
from .models import Element

ElementDictSubClass = TypeVar("ElementDictSubClass", bound=ElementDict)
ElementSubClass = TypeVar("ElementSubClass", bound=Element)

ElementForUpdate = NewType("ElementForUpdate", Element)


class ElementsAndWorkflowActions(TypedDict):
    elements: List[Element]
    workflow_actions: List[BuilderWorkflowAction]
