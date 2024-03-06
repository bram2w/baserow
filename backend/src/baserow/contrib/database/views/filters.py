from dataclasses import dataclass
from typing import Iterable, Literal, Optional

from baserow.contrib.database.api.views.serializers import validate_api_grouped_filters
from baserow.contrib.database.fields.field_filters import (
    FILTER_TYPE_AND,
    FILTER_TYPE_OR,
)
from baserow.contrib.database.views.view_filter_groups import (
    construct_filter_builder_from_grouped_api_filters,
)


def sanitize_filter_value(value: str):
    return value.replace("\x00", "")


def sanitize_filter_values(values: Iterable[str]):
    return [sanitize_filter_value(val) for val in values]


@dataclass
class AdHocFilters:
    """Dataclass that can hold data for basic and grouped filters at the same time."""

    # grouped filters
    api_filters: Optional[dict[str, any]] = None

    # simple filters
    filter_type: Literal["OR", "AND"] = "OR"
    filter_object: Optional[dict] = None

    # optional params
    user_field_names: bool = False
    only_filter_by_field_ids: Optional[Iterable[int]] = None

    @classmethod
    def from_request(
        cls,
        request,
        user_field_names: bool = False,
        only_filter_by_field_ids: Optional[list[int]] = None,
    ):
        filter_type = (
            FILTER_TYPE_OR
            if request.GET.get("filter_type", "AND").upper() == "OR"
            else FILTER_TYPE_AND
        )
        filter_object = {
            key: sanitize_filter_values(request.GET.getlist(key))
            for key in request.GET.keys()
        }

        api_filters = None
        if (filters := filter_object.get("filters", None)) and len(filters) > 0:
            api_filters = validate_api_grouped_filters(
                filters[0], user_field_names=user_field_names
            )

        return AdHocFilters(
            api_filters=api_filters,
            filter_type=filter_type,
            filter_object=filter_object,
            user_field_names=user_field_names,
            only_filter_by_field_ids=only_filter_by_field_ids,
        )

    @property
    def has_simple_filters(self):
        return (
            any(param for param in self.filter_object if param.startswith("filter__"))
            if self.filter_object
            else False
        )

    @property
    def has_any_filters(self):
        return self.api_filters or self.has_simple_filters

    def apply_to_queryset(self, model, queryset):
        if self.api_filters and len(self.api_filters):
            filter_builder = construct_filter_builder_from_grouped_api_filters(
                self.api_filters,
                model,
                user_field_names=self.user_field_names,
                only_filter_by_field_ids=self.only_filter_by_field_ids,
            )
            return filter_builder.apply_to_queryset(queryset)

        if self.filter_object:
            return queryset.filter_by_fields_object(
                self.filter_object,
                self.filter_type,
                user_field_names=self.user_field_names,
                only_filter_by_field_ids=self.only_filter_by_field_ids,
            )

        return queryset
