from typing import NewType, TypedDict, TypeVar

from .models import Service


class ServiceDict(TypedDict):
    id: int
    integration_id: int
    type: str


ServiceDictSubClass = TypeVar("ServiceDictSubClass", bound="ServiceDict")

ServiceSubClass = TypeVar("ServiceSubClass", bound="Service")

ServiceForUpdate = NewType("ServiceForUpdate", Service)
