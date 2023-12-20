from typing import List, Optional, TypedDict

from baserow.contrib.builder.pages.types import PagePathParams
from baserow.core.integrations.types import IntegrationDictSubClass
from baserow.core.services.types import ServiceDictSubClass
from baserow.core.user_sources.types import UserSourceDictSubClass
from baserow.core.workflow_actions.models import WorkflowAction


class ElementDict(TypedDict):
    id: int
    order: int
    type: str
    parent_element_id: int
    place_in_container: str
    style_border_top_color: str
    style_border_top_size: int
    style_padding_top: int
    style_border_bottom_color: str
    style_border_bottom_size: int
    style_padding_bottom: int
    style_background: str
    style_background_color: str
    style_width: str


class DataSourceDict(TypedDict):
    id: int
    name: str
    order: int
    service: Optional[ServiceDictSubClass]


class PageDict(TypedDict):
    id: int
    name: str
    order: int
    path: str
    path_params: PagePathParams
    elements: List[ElementDict]
    data_sources: List[DataSourceDict]
    workflow_actions: List[WorkflowAction]


class BuilderDict(TypedDict):
    id: int
    name: str
    order: int
    type: str
    pages: List[PageDict]
    integrations: List[IntegrationDictSubClass]
    user_sources: List[UserSourceDictSubClass]
    theme: object
