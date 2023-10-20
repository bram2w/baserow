from typing import NewType, Optional, TypedDict, TypeVar

from .models import Service


class ServiceDict(TypedDict):
    id: int
    integration_id: int
    type: str


class ServiceFilterDict(TypedDict):
    id: Optional[int]
    service: int
    type: str
    value: str


ServiceDictSubClass = TypeVar("ServiceDictSubClass", bound="ServiceDict")

ServiceFilterDictSubClass = TypeVar(
    "ServiceFilterDictSubClass", bound="ServiceFilterDict"
)

ServiceSubClass = TypeVar("ServiceSubClass", bound="Service")

ServiceForUpdate = NewType("ServiceForUpdate", Service)
