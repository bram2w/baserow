from typing import TYPE_CHECKING, Any, Dict, Generator, List, Tuple, Type

from django.core.exceptions import ValidationError
from django.db.models import OrderBy, QuerySet

from baserow.contrib.builder.data_providers.exceptions import (
    DataProviderChunkInvalidException,
)
from baserow.contrib.database.fields.field_filters import FilterBuilder
from baserow.contrib.database.search.handler import SearchHandler
from baserow.contrib.database.views.filters import AdHocFilters
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.registries import view_filter_type_registry
from baserow.contrib.integrations.local_baserow.api.serializers import (
    LocalBaserowTableServiceFilterSerializer,
    LocalBaserowTableServiceSortSerializer,
)
from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowTableServiceFilter,
    LocalBaserowTableServiceSort,
    LocalBaserowViewService,
)
from baserow.core.formula import BaserowFormula, resolve_formula
from baserow.core.formula.registries import formula_runtime_function_registry
from baserow.core.formula.serializers import FormulaSerializerField
from baserow.core.formula.validator import ensure_integer, ensure_string
from baserow.core.registry import Instance
from baserow.core.services.dispatch_context import DispatchContext
from baserow.core.services.exceptions import ServiceImproperlyConfigured
from baserow.core.services.types import ServiceDict, ServiceSubClass

if TYPE_CHECKING:
    from baserow.contrib.database.table.models import GeneratedTableModel, Table


class LocalBaserowTableServiceFilterableMixin:
    """
    A mixin for LocalBaserow{Table,View}Service services so that when they dispatch,
    filters applied to their service's table, and possibly view, are applied to
    the queryset.
    """

    mixin_allowed_fields = ["filter_type"]
    mixin_serializer_field_names = ["filters", "filter_type"]
    mixin_serializer_field_overrides = {
        "filters": LocalBaserowTableServiceFilterSerializer(
            many=True, source="service_filters", required=False
        ),
    }

    class SerializedDict(ServiceDict):
        filter_type: str
        filters: List[Dict]

    def serialize_filters(self, service: ServiceSubClass):
        """
        Responsible for serializing the service `filters`.

        :param service: the service instance.
        :return: A list of serialized filter dictionaries.
        """

        return [
            {
                "field_id": f.field_id,
                "type": f.type,
                "value": f.value,
                "value_is_formula": f.value_is_formula,
            }
            for f in service.service_filters.all()
        ]

    def deserialize_filters(self, value, id_mapping):
        """
        Deserializes the filters by mapping the field_id to the new field_id if it
        exists in the id_mapping. If the value is a digit, try and map the value to
        the new field select option id.

        :param value: the value of this property.
        :param id_mapping: the id mapping dict.
        :return: the deserialized version for the filter.
        """

        return [
            {
                **f,
                "field_id": (
                    id_mapping["database_fields"][f["field_id"]]
                    if "database_fields" in id_mapping
                    else f["field_id"]
                ),
                "value": (
                    id_mapping["database_field_select_options"].get(
                        int(f["value"]), f["value"]
                    )
                    if "database_field_select_options" in id_mapping
                    and f["value"].isdigit()
                    else f["value"]
                ),
            }
            for f in value
        ]

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

    def formula_generator(
        self, service: "LocalBaserowTableServiceFilterableMixin"
    ) -> Generator[str | Instance, str, None]:
        """
        Generator that iterates over formula fields for LocalBaserow Services.

        Some formula fields are in service filters.
        """

        yield from super().formula_generator(service)

        for service_filter in service.service_filters.all():
            if service_filter.value_is_formula:
                # Service types like LocalBaserowGetRow do not have a value attribute.
                new_formula = yield service_filter.value
                if new_formula is not None:
                    # Set the new formula for the Service Filter
                    service_filter.value = new_formula
                    yield service_filter

    def get_queryset(
        self,
        service: ServiceSubClass,
        table: "Table",
        dispatch_context: DispatchContext,
        model: Type["GeneratedTableModel"],
    ) -> QuerySet:
        """
        Responsible for applying the filters to the queryset. If the dispatch
        context contains any adhoc-filters, they are applied ontop of existing
        service and view filters.

        :param service: the service instance.
        :param table: the table instance.
        :param dispatch_context: the dispatch context.
        :param model: the table's generated table model
        :return: the queryset with filters applied.
        """

        queryset = super().get_queryset(service, table, dispatch_context, model)
        queryset = self.get_dispatch_filters(service, queryset, model, dispatch_context)
        dispatch_filters = dispatch_context.filters()
        if dispatch_filters is not None:
            deserialized_filters = AdHocFilters.deserialize_dispatch_filters(
                dispatch_filters
            )
            adhoc_filters = AdHocFilters.from_dict(deserialized_filters)
            queryset = adhoc_filters.apply_to_queryset(model, queryset)
        return queryset


class LocalBaserowTableServiceSortableMixin:
    """
    A mixin for LocalBaserowTableService services so that when they dispatch, sortings
    applied to their service's table or view are applied to the queryset.
    """

    mixin_serializer_field_names = ["sortings"]
    mixin_serializer_field_overrides = {
        "sortings": LocalBaserowTableServiceSortSerializer(
            many=True, source="service_sorts", required=False
        ),
    }

    class SerializedDict(ServiceDict):
        sortings: List[Dict]

    def serialize_sortings(self, service: ServiceSubClass):
        """
        Responsible for serializing the service `sortings`.

        :param service: the service instance.
        :return: A list of serialized sort dictionaries.
        """

        return [
            {
                "field_id": s.field_id,
                "order_by": s.order_by,
            }
            for s in service.service_sorts.all()
        ]

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

    def get_queryset(
        self,
        service: ServiceSubClass,
        table: "Table",
        dispatch_context: DispatchContext,
        model: Type["GeneratedTableModel"],
    ) -> QuerySet:
        """
        Responsible for applying the sortings to the queryset. If the dispatch
        context contains any adhoc-sortings, they replace any existing service
        and/or view sorts.

        :param service: the service instance.
        :param table: the table instance.
        :param dispatch_context: the dispatch context.
        :param model: the table's generated table model
        :return: the queryset with sortings applied.
        """

        queryset = super().get_queryset(service, table, dispatch_context, model)

        adhoc_sort = dispatch_context.sortings()
        if adhoc_sort is not None:
            queryset = queryset.order_by_fields_string(adhoc_sort, False)
        else:
            view_sorts, queryset = self.get_dispatch_sorts(service, queryset, model)
            if view_sorts:
                queryset = queryset.order_by(*view_sorts)
        return queryset


class LocalBaserowTableServiceSearchableMixin:
    """
    A mixin for `LocalBaserowTable` service types so that when they dispatch,
    search queries applied to their service's table are applied to the queryset.
    """

    mixin_simple_formula_fields = ["search_query"]
    mixin_allowed_fields = ["search_query"]
    mixin_serializer_field_names = ["search_query"]

    class SerializedDict(ServiceDict):
        search_query: str

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

    def get_queryset(
        self,
        service: ServiceSubClass,
        table: "Table",
        dispatch_context: DispatchContext,
        model: Type["GeneratedTableModel"],
    ):
        """
        Responsible for applying the search query to the queryset. If the dispatch
        context contains an adhoc-search-query, it is applied ontop of the existing
        service search query.

        :param service: the service instance.
        :param table: the table instance.
        :param dispatch_context: the dispatch context.
        :param model: the table's generated table model
        :return: the queryset with the search query applied.
        """

        queryset = super().get_queryset(service, table, dispatch_context, model)
        search_mode = SearchHandler.get_default_search_mode_for_table(table)
        service_search_query = self.get_dispatch_search(service, dispatch_context)
        if service_search_query:
            queryset = queryset.search_all_fields(
                service_search_query, search_mode=search_mode
            )
        adhoc_search_query = dispatch_context.search_query()
        if adhoc_search_query is not None:
            queryset = queryset.search_all_fields(
                adhoc_search_query, search_mode=search_mode
            )
        return queryset


class LocalBaserowTableServiceSpecificRowMixin:
    mixin_simple_formula_fields = ["row_id"]
    mixin_allowed_fields = ["row_id"]
    mixin_serializer_field_names = ["row_id"]
    mixin_serializer_field_overrides = {
        "row_id": FormulaSerializerField(
            required=False,
            allow_blank=True,
            help_text="A formula for defining the intended row.",
        ),
    }

    class SerializedDict(ServiceDict):
        row_id: BaserowFormula

    def resolve_row_id(
        self, resolved_values, service, dispatch_context
    ) -> Dict[str, Any]:
        """
        Responsible for resolving the `row_id` formula for the service.

        :param resolved_values: The resolved values for the service.
        :param service: The service instance.
        :param dispatch_context: The dispatch context.
        :return: The resolved values with the `row_id` formula resolved.
        """

        # Ignore validation for empty formulas
        if not service.row_id:
            return resolved_values

        try:
            dispatch_context.reset_call_stack()
            resolved_values["row_id"] = ensure_integer(
                resolve_formula(
                    service.row_id,
                    formula_runtime_function_registry,
                    dispatch_context,
                )
            )
        except ValidationError:
            raise ServiceImproperlyConfigured(
                "The result of the `row_id` formula must be an integer or convertible "
                "to an integer."
            )
        except DataProviderChunkInvalidException as e:
            message = f"Formula for row {service.row_id} could not be resolved."
            raise ServiceImproperlyConfigured(message) from e
        except Exception as e:
            raise ServiceImproperlyConfigured(
                f"The `row_id` formula can't be resolved: {e}"
            )

        return resolved_values
