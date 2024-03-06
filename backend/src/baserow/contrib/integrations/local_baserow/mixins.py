from typing import TYPE_CHECKING, List, Tuple, Type

from django.db.models import OrderBy, QuerySet

from baserow.contrib.database.fields.field_filters import FilterBuilder
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.registries import view_filter_type_registry
from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowTableServiceFilter,
    LocalBaserowTableServiceSort,
    LocalBaserowViewService,
)
from baserow.core.formula import resolve_formula
from baserow.core.formula.registries import formula_runtime_function_registry
from baserow.core.formula.validator import ensure_string
from baserow.core.services.dispatch_context import DispatchContext
from baserow.core.services.exceptions import ServiceImproperlyConfigured

if TYPE_CHECKING:
    from baserow.contrib.database.table.models import GeneratedTableModel
    from baserow.core.services.types import ServiceSubClass


class LocalBaserowTableServiceFilterableMixin:
    """
    A mixin for LocalBaserow{Table,View}Service services so that when they dispatch,
    filters applied to their service's table, and possibly view, are applied to
    the queryset.
    """

    def get_dispatch_filters(
        self,
        service: "ServiceSubClass",
        queryset: QuerySet,
        model: Type["GeneratedTableModel"],
        dispatch_context: DispatchContext,
    ) -> QuerySet:
        """
        Responsible for defining how the `LocalBaserow` services are filtered. To issue
        a `dispatch`, a `LocalBaserow` service must be pointing to a table.

        If we only have a `table` and no `view`, then we will query for, and apply,
        any `LocalBaserowTableServiceFilter` found for this service.

        If we also have a `view`, then we will query for, and apply, any `ViewFilter`
        found for this view.

        :param service: The `LocalBaserow` service we're dispatching.
        :param queryset: The queryset we want to filter upon.
        :param model: The `service.table`'s `GeneratedTableModel`.
        :return: A queryset with any applicable view/service filters applied to it.
        """

        if isinstance(service, LocalBaserowViewService) and service.view_id:
            view_filter_builder = ViewHandler().get_filter_builder(service.view, model)
            queryset = view_filter_builder.apply_to_queryset(queryset)

        service_filter_builder = FilterBuilder(filter_type=service.filter_type)
        service_filters = LocalBaserowTableServiceFilter.objects.filter(service=service)
        for service_filter in service_filters:
            field_object = model._field_objects[service_filter.field_id]
            field_name = field_object["name"]
            model_field = model._meta.get_field(field_name)
            view_filter_type = view_filter_type_registry.get(service_filter.type)

            if service_filter.value_is_formula:
                try:
                    resolved_value = str(
                        resolve_formula(
                            service_filter.value,
                            formula_runtime_function_registry,
                            dispatch_context,
                        )
                    )
                except Exception as exc:
                    raise ServiceImproperlyConfigured(
                        f"The {field_name} service filter formula can't be resolved: {exc}"
                    ) from exc
            else:
                resolved_value = service_filter.value

            service_filter_builder.filter(
                view_filter_type.get_filter(
                    field_name, resolved_value, model_field, field_object["field"]
                )
            )

        return service_filter_builder.apply_to_queryset(queryset)


class LocalBaserowTableServiceSortableMixin:
    """
    A mixin for LocalBaserowTableService services so that when they dispatch, sortings
    applied to their service's table or view are applied to the queryset.
    """

    def get_dispatch_sorts(
        self,
        service: "ServiceSubClass",
        queryset: QuerySet,
        model: Type["GeneratedTableModel"],
    ) -> Tuple[List[OrderBy], QuerySet]:
        """
        Responsible for defining how the `LocalBaserow` services are sorted. To issue
        a `dispatch`, a `LocalBaserow` service must be pointing to a table.

        If we find any `LocalBaserowTableServiceSort` applied to this service, we will
        *only* sort on their `OrderBy` expressions.

        If we find no `LocalBaserowTableServiceSort`, then we will attempt to find any
        `ViewSort` applied to the view, and use that for sorting the queryset.

        :param service: The `LocalBaserow` service we're dispatching.
        :param queryset: The Django queryset we want to apply our sort annotations to.
        :param model: The `service.view.table`'s `GeneratedTableModel`.
        :return: A list of `OrderBy` expressions.
        """

        service_sorts = LocalBaserowTableServiceSort.objects.filter(service=service)
        sort_ordering = [service_sort.get_order_by() for service_sort in service_sorts]

        if not sort_ordering and service.view:
            sort_ordering, queryset = ViewHandler().get_view_order_bys(
                service.view, model, queryset
            )

        return sort_ordering, queryset


class LocalBaserowTableServiceSearchableMixin:
    """
    A mixin for `LocalBaserowTable` service types so that when they dispatch,
    search queries applied to their service's table are applied to the queryset.
    """

    def get_dispatch_search(
        self, service: "ServiceSubClass", dispatch_context: DispatchContext
    ) -> str:
        """
        Returns this service's search query, which can be applied to the dispatch
        queryset.

        :param service: The `LocalBaserow` service we're dispatching.
        :return: string
        """

        try:
            return ensure_string(
                resolve_formula(
                    service.search_query,
                    formula_runtime_function_registry,
                    dispatch_context,
                ),
                allow_empty=True,
            )
        except Exception as exc:
            raise ServiceImproperlyConfigured(
                f"The `search_query` formula can't be resolved: {exc}"
            ) from exc
