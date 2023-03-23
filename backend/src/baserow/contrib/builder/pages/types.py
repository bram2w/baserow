from typing import Dict, Literal, TypedDict

PAGE_PATH_PARAM_TYPE_CHOICES_LITERAL = Literal["text", "numeric"]


class PagePathParam(TypedDict):
    param_type: Literal[PAGE_PATH_PARAM_TYPE_CHOICES_LITERAL]


param_name = str
PagePathParams = Dict[param_name, PagePathParam]
