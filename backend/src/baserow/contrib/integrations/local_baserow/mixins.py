from typing import TYPE_CHECKING, List, Optional, Type

from django.db.models import OrderBy, Q

from baserow.contrib.database.fields.field_filters import FILTER_TYPE_AND, FilterBuilder
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowTableServiceFilter,
    LocalBaserowTableServiceSort,
)

if TYPE_CHECKING:
    from baserow.contrib.database.table.models import GeneratedTableModel
    from baserow.core.services.types import ServiceSubClass


class LocalBaserowTableServiceFilterableMixin:
    """
    A mixin for LocalBaserowTableService services so that when they dispatch, filters
    applied to their service's table, and possibly view, are applied to the queryset.
    """

    def get_dispatch_filters(
        self,
        service: "ServiceSubClass",
        model: Type["GeneratedTableModel"],
    ) -> FilterBuilder:
        """
        Responsible for defining how the `LocalBaserow` services are filtered. To issue
        a `dispatch`, a `LocalBaserow` service must be pointing to a table.

        If we only have a `table` and no `view`, then we will query for, and apply,
        any `LocalBaserowTableServiceFilter` found for this service.

        If we also have a `view`, then we will query for, and apply, any `ViewFilter`
        found for this view.

        :param service: The `LocalBaserow` service we're dispatching.
        :param model: The `service.view.table`'s `GeneratedTableModel`.
        :return: A `FilterBuilder` filtered with view and/or service filters.
        """

        filter_builder = FilterBuilder(filter_type=FILTER_TYPE_AND)

        if service.view:
            view_filter_expressions = ViewHandler().get_view_filter_expressions(
                service.view, model
            )
            for view_filter_expression in view_filter_expressions:
                filter_builder.filter(view_filter_expression)

        service_filters = LocalBaserowTableServiceFilter.objects.filter(service=service)
        for service_filter in service_filters:
            filter_builder.filter(
                Q(**{service_filter.field.db_column: service_filter.value})
            )

        return filter_builder


class LocalBaserowTableServiceSortableMixin:
    """
    A mixin for LocalBaserowTableService services so that when they dispatch, sortings
    applied to their service's table or view are applied to the queryset.
    """

    def get_dispatch_sorts(
        self,
        service: "ServiceSubClass",
        model: Type["GeneratedTableModel"],
    ) -> Optional[List[OrderBy]]:
        """
        Responsible for defining how the `LocalBaserow` services are sorted. To issue
        a `dispatch`, a `LocalBaserow` service must be pointing to a table.

        If we find any `LocalBaserowTableServiceSort` applied to this service, we will
        *only* sort on their `OrderBy` expressions.

        If we find no `LocalBaserowTableServiceSort`, then we will attempt to find any
        `ViewSort` applied to the view, and use that for sorting the queryset.

        :param service: The `LocalBaserow` service we're dispatching.
        :param model: The `service.view.table`'s `GeneratedTableModel`.
        :return: A list of `OrderBy` expressions.
        """

        service_sorts = LocalBaserowTableServiceSort.objects.filter(service=service)
        sort_ordering = [service_sort.get_order() for service_sort in service_sorts]

        if not sort_ordering and service.view:
            sort_ordering, _ = ViewHandler().get_view_sorts(service.view, model)

        return sort_ordering


class LocalBaserowTableServiceSearchableMixin:
    """
    A mixin for LocalBaserow service types so that when they dispatch, search
    queries applied to their service's table are applied to the queryset.
    """

    def get_dispatch_search(self, service: "ServiceSubClass") -> str:
        """
        Returns this service's search query, which can be applied to the dispatch
        queryset.

        :param service: The `LocalBaserow` service we're dispatching.
        :return: string
        """

        return service.search_query
