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


class ServiceSortDict(TypedDict):
    id: Optional[int]
    service: int
    field: int
    order: str


ServiceDictSubClass = TypeVar("ServiceDictSubClass", bound="ServiceDict")

ServiceFilterDictSubClass = TypeVar(
    "ServiceFilterDictSubClass", bound="ServiceFilterDict"
)

ServiceSortDictSubClass = TypeVar("ServiceSortDictSubClass", bound="ServiceSortDict")

ServiceSubClass = TypeVar("ServiceSubClass", bound="Service")

ServiceForUpdate = NewType("ServiceForUpdate", Service)
