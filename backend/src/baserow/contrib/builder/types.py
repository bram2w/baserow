from typing import List, TypedDict

from baserow.contrib.builder.pages.types import PagePathParams


class ElementDict(TypedDict):
    id: int
    order: int
    type: str


class PageDict(TypedDict):
    id: int
    name: str
    order: int
    path: str
    path_params: PagePathParams
    elements: List[ElementDict]


class BuilderDict(TypedDict):
    id: int
    name: str
    order: int
    type: str
    pages: List[PageDict]
