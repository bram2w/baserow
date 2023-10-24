from typing import List, Union

from baserow.contrib.builder.data_sources.builder_dispatch_context import (
    BuilderDispatchContext,
)
from baserow.contrib.builder.data_sources.exceptions import (
    DataSourceImproperlyConfigured,
)
from baserow.contrib.builder.data_sources.handler import DataSourceHandler
from baserow.core.formula.exceptions import FormulaRecursion
from baserow.core.formula.registries import DataProviderType
from baserow.core.utils import get_nested_value_from_dict


class PageParameterDataProviderType(DataProviderType):
    """
    This data provider reads page parameter information from the data sent by the
    frontend during the dispatch. The data are then available for the formulas.
    """

    type = "page_parameter"

    def get_data_chunk(
        self, dispatch_context: BuilderDispatchContext, path: List[str]
    ) -> Union[int, str]:
        """
        When a page parameter is read, returns the value previously saved from the
        request object.
        """

        if len(path) != 1:
            return None

        first_part = path[0]

        return dispatch_context.request.data.get("page_parameter", {}).get(
            first_part, None
        )


class DataSourceDataProviderType(DataProviderType):
    """
    The data source provider can read data from registered page data sources.
    """

    type = "data_source"

    def get_data_source_by_id(
        self, dispatch_context: BuilderDispatchContext, data_source_id: int
    ):
        """
        Helper to get data source from a name from the cache or populate the cache
        if not populated.
        """

        if "data_sources" not in dispatch_context.cache:
            dispatch_context.cache[
                "data_sources"
            ] = DataSourceHandler().get_data_sources(dispatch_context.page)

        for data_source in dispatch_context.cache["data_sources"]:
            if data_source.id == data_source_id:
                return data_source

        raise DataSourceImproperlyConfigured(
            f"Data source with id {data_source_id} doesn't exist"
        )

    def get_data_chunk(self, dispatch_context: BuilderDispatchContext, path: List[str]):
        """Load a data chunk from a datasource of the page in context."""

        data_source_id, *rest = path

        data_source = self.get_data_source_by_id(dispatch_context, int(data_source_id))

        # Declare the call and check for recursion
        try:
            dispatch_context.add_call(data_source.id)
        except FormulaRecursion:
            raise DataSourceImproperlyConfigured("Recursion detected.")

        dispatch_result = DataSourceHandler().dispatch_data_source(
            data_source, dispatch_context
        )

        return get_nested_value_from_dict(dispatch_result, rest)
