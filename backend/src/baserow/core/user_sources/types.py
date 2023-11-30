from typing import NewType, TypedDict, TypeVar

from baserow.core.user_sources.models import UserSource


class UserSourceDict(TypedDict):
    id: int
    name: str
    order: int
    type: str
    integration_id: int


UserSourceDictSubClass = TypeVar("UserSourceDictSubClass", bound="UserSourceDict")

UserSourceSubClass = TypeVar("UserSourceSubClass", bound="UserSource")

UserSourceForUpdate = NewType("UserSourceForUpdate", UserSource)
