from django.db.models import Q

from baserow.core.services.exceptions import (
    ServiceImproperlyConfiguredDispatchException,
)

from .exceptions import DashboardFilterInvalidBinding
from .field_types import get_text_field_type, text_field_expression
from .models import DashboardFilter, DashboardFilterBinding


def get_binding_field(binding, service):
    field = binding.field
    if (
        field is None
        or field.trashed
        or field.table_id != getattr(service, "table_id", None)
    ):
        raise DashboardFilterInvalidBinding(
            "An associated field is missing or belongs to a different table."
        )
    field = field.specific
    get_text_field_type(field)
    return field


def apply_widget_filters(widget, service, queryset, applied_filters):
    """Apply server-owned associations and operators only to this widget's service."""

    if service.id != widget.data_source.service_id:
        return queryset
    selections = {
        selection["filter_id"]: selection["values"] for selection in applied_filters
    }
    bindings = DashboardFilterBinding.objects.filter(
        widget=widget, filter__trashed=False
    ).select_related("filter", "field")
    for binding in bindings:
        try:
            field = get_binding_field(binding, service)
        except DashboardFilterInvalidBinding as exc:
            raise ServiceImproperlyConfiguredDispatchException(str(exc)) from exc
        configuration = binding.filter
        values = selections.get(configuration.id, [])
        if configuration.mode == DashboardFilter.Mode.INPUT:
            values = [value.strip() for value in values[:1]]
        elif not configuration.multiple:
            values = values[:1]
        values = [value for value in values if value]
        if not values:
            continue

        alias = f"dashboard_filter_{configuration.id}"
        queryset = queryset.alias(**{alias: text_field_expression(field)})
        contains = configuration.operator in (
            DashboardFilter.Operator.CONTAINS,
            DashboardFilter.Operator.CONTAINS_NOT,
        )
        lookup = "icontains" if contains else "exact"
        predicate = Q()
        for value in values:
            predicate |= Q(**{f"{alias}__{lookup}": value})
        if configuration.operator in (
            DashboardFilter.Operator.NOT_EQUAL,
            DashboardFilter.Operator.CONTAINS_NOT,
        ):
            predicate = Q(**{f"{alias}__isnull": True}) | ~predicate
        queryset = queryset.filter(predicate)
    return queryset
