from typing import TYPE_CHECKING, List, Optional, Type

from django.db.models import OrderBy

from baserow.contrib.database.views.handler import ViewHandler

if TYPE_CHECKING:
    from baserow.contrib.database.fields.field_filters import FilterBuilder
    from baserow.contrib.database.table.models import GeneratedTableModel
    from baserow.core.services.types import ServiceSubClass


class LocalBaserowFilterableViewServiceMixin:
    """
    A mixin for LocalBaserow service types so that when they dispatch, filters
    applied to their service's view are applied to the queryset.
    """

    def get_dispatch_filters(
        self,
        service: "ServiceSubClass",
        model: Optional[Type["GeneratedTableModel"]] = None,
    ) -> "FilterBuilder":
        """
        Responsible for defining how the `LocalBaserowViewService` services should be
        filtered. All the integration's services point to a Baserow `View`, which
        can have zero or more `ViewFilter` records related to it. We'll use the
        `FilterBuilder` to return a set of filters we can apply to the base queryset.

        :param service: The `LocalBaserow` service we're dispatching.
        :param model: The `service.view.table`'s `GeneratedTableModel`.
        :return: A `FilterBuilder` applicable to the service's view.
        """

        view = service.view
        if model is None:
            model = view.table.get_model()
        return ViewHandler().get_filter_builder(view, model)


class LocalBaserowSortableViewServiceMixin:
    """
    A mixin for LocalBaserow service types so that when they dispatch, sortings
    applied to their service's view are applied to the queryset.
    """

    def get_dispatch_sorts(
        self,
        service: "ServiceSubClass",
        model: Optional[Type["GeneratedTableModel"]] = None,
    ) -> List[OrderBy]:
        """
        Responsible for defining how `LocalBaserowViewService` services should be
        sorted. All the integration's services point to a Baserow `View`, which
        can have zero or more `ViewSort` records related to it. We'll use the
        `ViewHandler.get_view_sorts` method to return a set of `OrderBy` and
         field name string which we can apply to the base queryset.

        :param service: The `LocalBaserow` service we're dispatching.
        :param model: The `service.view.table`'s `GeneratedTableModel`.
        :return: A list of `OrderBy` expressions.
        """

        view = service.view
        if model is None:
            model = view.table.get_model()
        service_sorts, _ = ViewHandler().get_view_sorts(view, model)
        return service_sorts


class LocalBaserowSearchableViewServiceMixin:
    """
    A mixin for LocalBaserow service types so that when they dispatch, search
    queries applied to their service's view are applied to the queryset.
    """

    def get_dispatch_search(self, service: "ServiceSubClass") -> str:
        """
        Returns this service's search query, which can be applied to the dispatch
        queryset.

        :param service: The `LocalBaserow` service we're dispatching.
        :return: string
        """

        return service.search_query
