import re

from baserow.contrib.dashboard.filters.models import DashboardFilter
from baserow.core.formula.exceptions import InvalidRuntimeFormula
from baserow.core.formula.parser.exceptions import BaserowFormulaSyntaxError
from baserow.core.formula.registries import DataProviderType, DataProviderTypeRegistry
from baserow.core.utils import get_value_at_path


class DashboardFilterDataProviderType(DataProviderType):
    type = "dashboard_filter"

    def is_valid(self, path):
        if not (
            1 <= len(path) <= 2
            and re.fullmatch(r"[1-9][0-9]*", path[0])
            and (len(path) == 1 or path[1] == "*" or re.fullmatch(r"[0-9]+", path[1]))
        ):
            raise BaserowFormulaSyntaxError(
                "The dashboard filter reference is invalid."
            )

    def get_data_chunk(self, dispatch_context, path):
        self.is_valid(path)
        if dispatch_context.dashboard is None:
            raise InvalidRuntimeFormula("The dashboard filter reference is invalid.")

        cache_key = ("dashboard_filters", dispatch_context.dashboard.id)
        if cache_key not in dispatch_context.cache:
            dispatch_context.cache[cache_key] = {
                str(item.id): item
                for item in DashboardFilter.objects.filter(
                    dashboard=dispatch_context.dashboard
                )
            }
        configuration = dispatch_context.cache[cache_key].get(path[0])
        if configuration is None:
            raise InvalidRuntimeFormula("The dashboard filter no longer exists.")

        selections = {
            str(selection["filter_id"]): selection["values"]
            for selection in dispatch_context.applied_filters
        }
        values = selections.get(path[0], [])
        if configuration.mode == DashboardFilter.Mode.INPUT:
            values = [value.strip() for value in values[:1]]
        value = (
            values
            if configuration.mode == DashboardFilter.Mode.DROPDOWN
            and configuration.multiple
            else next(iter(values), "")
        )
        return get_value_at_path(value, path[1:])

    def import_path(self, path, id_mapping, **kwargs):
        filter_id, *rest = path
        mapped_id = id_mapping.get("dashboard_filters", {}).get(
            int(filter_id), filter_id
        )
        return [str(mapped_id), *rest]


class DashboardDataSourceDataProviderType(DataProviderType):
    type = "data_source"

    def is_valid(self, path):
        if not path or not re.fullmatch(r"[1-9][0-9]*", path[0]):
            raise BaserowFormulaSyntaxError("The data source reference is invalid.")

    def get_data_chunk(self, dispatch_context, path):
        from baserow.contrib.dashboard.data_sources.exceptions import (
            DashboardDataSourceDoesNotExist,
        )
        from baserow.contrib.dashboard.data_sources.service import (
            DashboardDataSourceService,
        )

        self.is_valid(path)
        if dispatch_context.dashboard is None:
            raise InvalidRuntimeFormula("The data source reference is invalid.")
        service = DashboardDataSourceService()
        try:
            data_source = service.get_data_source(
                dispatch_context.request.user, int(path[0])
            )
        except DashboardDataSourceDoesNotExist as exc:
            raise InvalidRuntimeFormula("The data source no longer exists.") from exc
        if data_source.dashboard_id != dispatch_context.dashboard.id:
            raise InvalidRuntimeFormula("The data source belongs to another dashboard.")

        result = service.dispatch_data_source(
            dispatch_context.request.user, data_source.id, dispatch_context
        )
        source_service = data_source.service.specific
        service_type = source_service.get_type()
        rest = path[1:]
        if service_type.returns_list:
            result = result["results"]
            prepared_path = (
                [rest[0], *service_type.prepare_value_path(source_service, rest[1:])]
                if len(rest) >= 2
                else rest
            )
        else:
            prepared_path = service_type.prepare_value_path(source_service, rest)
        return get_value_at_path(result, prepared_path)

    def import_path(self, path, id_mapping, **kwargs):
        from baserow.contrib.dashboard.data_sources.handler import (
            DashboardDataSourceHandler,
        )

        source_id, *rest = path
        mapped_id = id_mapping.get("dashboard_data_sources", {}).get(int(source_id))
        if mapped_id is None:
            return path
        source = DashboardDataSourceHandler().get_data_source(mapped_id)
        if source.service_id:
            rest = source.service.specific.get_type().import_path(rest, id_mapping)
        return [str(mapped_id), *rest]


dashboard_data_provider_type_registry = DataProviderTypeRegistry()
dashboard_data_provider_type_registry.register(DashboardFilterDataProviderType())
dashboard_data_provider_type_registry.register(DashboardDataSourceDataProviderType())
