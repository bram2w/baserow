from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from django.db.models import Q

from baserow.contrib.database.fields.exceptions import FilterFieldNotFound
from baserow.contrib.database.fields.field_filters import (
    FILTER_TYPE_AND,
    FILTER_TYPE_OR,
    AnnotatedQ,
    GroupedFiltersAdapter,
)
from baserow.contrib.database.table.models import GeneratedTableModel
from baserow.contrib.database.views.exceptions import (
    InvalidAPIGroupedFiltersFormatException,
    ViewFilterTypeNotAllowedForField,
)
from baserow.contrib.database.views.models import ViewFilter

from .models import View
from .registries import view_filter_type_registry


def get_q_from_view_filter(
    view_filter: ViewFilter, table_model: GeneratedTableModel
) -> Union[Q, AnnotatedQ]:
    """
    Returns a Q or an AnnotatedQ object based on the provided view filter.

    :param view_filter: The view filter to convert to a Q object.
    :param table_model: The table model for which the view filter should be
        generated.
    :return: A Q or AnnotatedQ object based on the provided view filter.
    """

    if view_filter.field_id not in table_model._field_objects:
        raise FilterFieldNotFound(
            view_filter.field_id, f"Field {view_filter.field_id} does not exist."
        )

    field_object = table_model._field_objects[view_filter.field_id]
    field_name = field_object["name"]
    field_type = field_object["type"]
    field_instance = field_object["field"]
    model_field = table_model._meta.get_field(field_name)
    view_filter_type = view_filter_type_registry.get(view_filter.type)

    if not view_filter_type.field_is_compatible(field_instance):
        raise ViewFilterTypeNotAllowedForField(view_filter.type, field_type.type)

    return view_filter_type.get_filter(
        field_name, view_filter.value, model_field, field_object["field"]
    )


class ViewGroupedFiltersAdapter(GroupedFiltersAdapter):
    def __init__(self, instance: View, model: GeneratedTableModel, **kwargs):
        super().__init__(instance, model)

    @property
    def filters(self):
        return self.instance.viewfilter_set.all()

    @property
    def groups(self):
        return self.instance.filter_groups.all()

    def get_q_from_filter(self, _filter) -> Union[Q, AnnotatedQ]:
        return get_q_from_view_filter(_filter, self.model)


class APIViewFilter:
    """
    Provides an interface similar to the original `ViewFilter` for the
    AdvancedFilterBuilder. This class is useful for temporary filters that are
    not stored in the db but need the same capabilities of the django model. For
    example, this is used by public views to create filters on the fly.
    """

    def __init__(self, field_id, type, value, group_id, pk=None):
        self.pk = pk or uuid4()
        self.field_id = field_id
        self.type = type
        self.value = value
        self.group_id = group_id

    @property
    def id(self):
        return self.pk


class APIFilterGroup:
    """
    Provides an interface similar to the original `ViewFilterGroup` for the
    AdvancedFilterBuilder. This class is useful for temporary filter groups that
    are not stored in the db but need the same capabilities of the django model.
    For example, this is used by public views to create filters on the fly.
    """

    def __init__(self, filter_type, parent_group_id=None, pk=None):
        self.pk = pk or uuid4()
        self.parent_group_id = parent_group_id
        self.filter_type = filter_type
        if filter_type not in [FILTER_TYPE_AND, FILTER_TYPE_OR]:
            raise ValueError(f"Unknown filter type {filter_type}.")

    @property
    def id(self):
        return self.pk


class APIGroupedFiltersAdapter(GroupedFiltersAdapter):
    """
    This adapter is used to get a list of filters and groups from a serialized
    filter tree. For example, this is used by public views to create filters on
    the fly.
    """

    def __init__(
        self,
        filter_type: str,
        filters: List[APIViewFilter],
        groups: List[APIFilterGroup],
        model: GeneratedTableModel,
        **kwargs,
    ):
        self._filter_type = filter_type
        self.model = model
        self._filters = filters
        self._groups = groups

    @property
    def filter_type(self):
        return self._filter_type

    @property
    def filters(self):
        return self._filters

    @property
    def groups(self):
        return self._groups

    def get_q_from_filter(self, _filter) -> Union[Q, AnnotatedQ]:
        return get_q_from_view_filter(_filter, self.model)

    @staticmethod
    def from_serialized_filter_tree(
        serialized_filter_tree: Dict[str, Any],
        model: GeneratedTableModel,
        only_filter_by_field_ids: Optional[List[int]] = None,
    ) -> "APIGroupedFiltersAdapter":
        """
        Create a PublicViewGroupedFiltersAdapter from a serialized
        tree of filters. The format of the serialized filter tree is:
        {
          "filter_type": "AND",
          "filters": [{"field": 1, "type": "contains", "value": "a"}],
          "groups": [{
            "filter_type": "OR",
            "filters": [
                {"field": 1, "type": "contains", "value": "b"},
                {"field": 1, "type": "contains", "value": "c"}
            ],
            "groups": [],
          }],
        }
        So we need to extract and create a flat list of all the filters and the groups
        in the correct order to make the adapter work with the AdvancedFilterBuilder.
        """

        filters = []
        groups = []

        def extract_filters_and_groups(
            filter_tree: Dict[str, Any], parent_group_id: Optional[int] = None
        ):
            """
            Extract filters and groups from the nested filter tree in order to
            create an adapter compatible with the AdvancedFilterBuilder.
            """

            for filter in filter_tree.get("filters", []):
                field_id = filter["field"]

                if (
                    only_filter_by_field_ids
                    and field_id not in only_filter_by_field_ids
                ):
                    raise FilterFieldNotFound(
                        field_id, f"Field {field_id} does not exist."
                    )
                temp_filter = APIViewFilter(
                    field_id=field_id,
                    type=filter["type"],
                    value=filter["value"],
                    group_id=parent_group_id,
                )
                filters.append(temp_filter)

            for group in filter_tree.get("groups", []):
                temp_group = APIFilterGroup(
                    filter_type=group["filter_type"],
                    parent_group_id=parent_group_id,
                )
                groups.append(temp_group)
                extract_filters_and_groups(group, parent_group_id=temp_group.id)

        try:
            root_node = APIFilterGroup(
                filter_type=serialized_filter_tree["filter_type"]
            )
            extract_filters_and_groups(serialized_filter_tree)

        except (KeyError, AttributeError, ValueError, TypeError):
            raise InvalidAPIGroupedFiltersFormatException()

        return APIGroupedFiltersAdapter(
            filter_type=root_node.filter_type,
            filters=filters,
            groups=groups,
            model=model,
        )
