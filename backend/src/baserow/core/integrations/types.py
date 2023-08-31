from typing import NewType, TypedDict, TypeVar

from baserow.core.integrations.models import Integration


class IntegrationDict(TypedDict):
    id: int
    name: str
    order: int
    type: str


IntegrationDictSubClass = TypeVar("IntegrationDictSubClass", bound="IntegrationDict")

IntegrationSubClass = TypeVar("IntegrationSubClass", bound="Integration")

IntegrationForUpdate = NewType("IntegrationForUpdate", Integration)
