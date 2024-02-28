from typing import List, NewType, TypedDict, TypeVar

from baserow.core.app_auth_providers.models import AppAuthProvider
from baserow.core.user_sources.models import UserSource


class UserSourceDict(TypedDict):
    id: int
    name: str
    order: int
    type: str
    uid: str
    integration_id: int
    auth_providers: List[AppAuthProvider]


UserSourceDictSubClass = TypeVar("UserSourceDictSubClass", bound="UserSourceDict")

UserSourceSubClass = TypeVar("UserSourceSubClass", bound="UserSource")

UserSourceForUpdate = NewType("UserSourceForUpdate", UserSource)
