from typing import Dict, Any, Union

from django.db.models import Q, BooleanField
from django.db.models.expressions import RawSQL

FILTER_TYPE_AND = "AND"
FILTER_TYPE_OR = "OR"


class AnnotatedQ:
    """
    A simple wrapper class combining a params for a Queryset.annotate call with a
    django Q object to be used in combination with FilterBuilder to dynamically build up
    filters which also require annotations.
    """

    def __init__(self, annotation: Dict[str, Any], q: Union[Q, Dict[str, Any]]):
        """
        :param annotation: A dictionary which can be unpacked into a django
            Queryset.annotate call. This will only happen when using
            FilterBuilder.apply_to_queryset.
        :param q: a Q object or kwargs which will used to create a Q object.
        """

        self.annotation = annotation or {}
        if isinstance(q, Q):
            self.q = q
        else:
            self.q = Q(**q)

    def __invert__(self):
        return AnnotatedQ(self.annotation, ~self.q)


OptionallyAnnotatedQ = Union[Q, AnnotatedQ]


class FilterBuilder:
    """
    Combines together multiple Q or AnnotatedQ filters into a single filter which
    will AND or OR the provided filters together based on the filter_type
    parameter. When applied to a queryset it will also annotate the queryset
    prior to filtering with the merged annotations from AnnotatedQ filters.
    """

    def __init__(self, filter_type: str):
        """

        :param filter_type: Either field_filters.FILTER_TYPE_AND or
            field_filters.FILTER_TYPE_OR which dictates how provided Q or AnnotatedQ
            filters will be combined together.
            For type OR they will be ORed together when applied to a filter set,
            for type AND they will be ANDed together.
        """

        if filter_type not in [FILTER_TYPE_AND, FILTER_TYPE_OR]:
            raise ValueError(f"Unknown filter type {filter_type}.")

        self._annotation = {}
        self._q_filters = Q()
        self._filter_type = filter_type

    def filter(self, q: OptionallyAnnotatedQ) -> "FilterBuilder":
        """
        Adds a Q or AnnotatedQ filter into this builder to be joined together with
        existing filters based on the builders `filter_type`.

        Annotations on provided AnnotatedQ's are merged together with any previously
        supplied annotations via dict unpacking and merging.

        :param q: A Q or Annotated Q
        :return: The updated FilterBuilder with the provided filter applied.
        """

        if isinstance(q, AnnotatedQ):
            self._annotate(q.annotation)
            self._filter(q.q)
        else:
            self._filter(q)
        return self

    def apply_to_queryset(self, queryset):
        """
        Applies all of the Q and AnnotatedQ filters previously given to this
        FilterBuilder by first applying all annotations from AnnotatedQ's and then
        filtering with a Q filter resulting from the combination of all filters ANDed or
        ORed depending on the filter_type attribute.

        :param queryset: The queryset to annotate and filter.
        :return: The annotated and filtered queryset.
        """

        return queryset.annotate(**self._annotation).filter(self._q_filters)

    def _annotate(self, annotation_dict: Dict[str, Any]) -> "FilterBuilder":
        self._annotation = {**self._annotation, **annotation_dict}

    def _filter(self, q_filter: Q) -> "FilterBuilder":
        if self._filter_type == FILTER_TYPE_AND:
            self._q_filters &= q_filter
        elif self._filter_type == FILTER_TYPE_OR:
            self._q_filters |= q_filter
        else:
            raise ValueError(f"Unknown filter type {self._filter_type}.")


def contains_filter(field_name, value, model_field, _) -> OptionallyAnnotatedQ:
    value = value.strip()
    # If an empty value has been provided we do not want to filter at all.
    if value == "":
        return Q()
    # Check if the model_field accepts the value.
    try:
        model_field.get_prep_value(value)
        return Q(**{f"{field_name}__icontains": value})
    except Exception:
        pass
    return Q()


def filename_contains_filter(field_name, value, _, field) -> OptionallyAnnotatedQ:
    value = value.strip()
    # If an empty value has been provided we do not want to filter at all.
    if value == "":
        return Q()
    # Check if the model_field has a file which matches the provided filter value.
    annotation_query = _build_filename_contains_raw_query(field, value)
    return AnnotatedQ(
        annotation={f"{field_name}_matches_visible_names": annotation_query},
        q={f"{field_name}_matches_visible_names": True},
    )


def _build_filename_contains_raw_query(field, value):
    # It is not possible to use Django's ORM to query for if one item in a JSONB
    # list has has a key which contains a specified value.
    #
    # The closest thing the Django ORM provides is:
    #   queryset.filter(your_json_field__contains=[{"key":"value"}])
    # However this is an exact match, so in the above example [{"key":"value_etc"}]
    # would not match the filter.
    #
    # Instead we have to resort to RawSQL to use various built in PostgreSQL JSON
    # Array manipulation functions to be able to 'iterate' over a JSONB list
    # performing `like` on individual keys in said list.
    num_files_with_name_like_value = f"""
    EXISTS(
        SELECT attached_files ->> 'visible_name'
        FROM JSONB_ARRAY_ELEMENTS("field_{field.id}") as attached_files
        WHERE UPPER(attached_files ->> 'visible_name') LIKE UPPER(%s)
    )
"""
    return RawSQL(
        num_files_with_name_like_value,
        params=[f"%{value}%"],
        output_field=BooleanField(),
    )
