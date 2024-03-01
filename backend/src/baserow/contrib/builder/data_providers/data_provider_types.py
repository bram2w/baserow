from typing import List, Union

from baserow.contrib.builder.data_sources.builder_dispatch_context import (
    BuilderDispatchContext,
)
from baserow.contrib.builder.data_sources.exceptions import (
    DataSourceDoesNotExist,
    DataSourceImproperlyConfigured,
)
from baserow.contrib.builder.data_sources.handler import DataSourceHandler
from baserow.core.formula.exceptions import FormulaRecursion
from baserow.core.formula.registries import DataProviderType
from baserow.core.services.dispatch_context import DispatchContext
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


class FormDataProviderType(DataProviderType):
    type = "form_data"

    def get_data_chunk(self, dispatch_context: DispatchContext, path: List[str]):
        if len(path) != 1:
            return None

        first_part = path[0]

        return (
            dispatch_context.request.data.get("form_data", {})
            .get(first_part, {})
            .get("value", None)
        )

    def import_path(self, path, id_mapping, **kwargs):
        """
        Update the form element id of the path.

        :param path: the path part list.
        :param id_mapping: The id_mapping of the process import.
        :return: The updated path.
        """

        form_element_id, *rest = path

        if "builder_page_elements" in id_mapping:
            form_element_id = id_mapping["builder_page_elements"].get(
                int(form_element_id), form_element_id
            )

        return [str(form_element_id), *rest]


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

        if data_source.service.get_type().returns_list:
            dispatch_result = dispatch_result["results"]

        return get_nested_value_from_dict(dispatch_result, rest)

    def import_path(self, path, id_mapping, **kwargs):
        """
        Update the data_source_id of the path and also apply the data_source type
        update when importing a path.

        :param path: the path part list.
        :param id_mapping: The id_mapping of the process import.
        :return: The updated path.
        """

        data_source_id, *rest = path

        if "builder_data_sources" in id_mapping:
            try:
                data_source_id = id_mapping["builder_data_sources"][int(data_source_id)]
                data_source = DataSourceHandler().get_data_source(data_source_id)
            except (KeyError, DataSourceDoesNotExist):
                # The data source have probably been deleted so we return the
                # initial path
                return [str(data_source_id), *rest]

            service_type = data_source.service.specific.get_type()
            rest = service_type.import_path(rest, id_mapping)

        return [str(data_source_id), *rest]


class CurrentRecordDataProviderType(DataProviderType):
    """
    The frontend data provider to get the current row content
    """

    type = "current_record"

    def get_data_chunk(self, dispatch_context: BuilderDispatchContext, path: List[str]):
        """Doesn't make sense in the backend yet"""

        return None

    def import_path(self, path, id_mapping, data_source_id=None, **kwargs):
        """
        Applies the updates of the related data_source.

        :param path: the path part list.
        :param id_mapping: The id_mapping of the process import.
        :param data_source_id: The id of the data_source related to this data provider.
        :return: The updated path.
        """

        # We don't need to import the id
        if len(path) == 1 and path[0] == "id":
            return path

        data_source = DataSourceHandler().get_data_source(data_source_id)
        service_type = data_source.service.specific.get_type()
        # Here we add a fake row part to make it match the usual shape for this path
        _, *rest = service_type.import_path([0, *path], id_mapping)

        return rest


class UserDataProviderType(DataProviderType):
    """
    This data provider user the user in `request.user_source_user` to resolve formula
    paths. This property is injected into the request by the
    `baserow.api.user_sources.middleware.AddUserSourceUserMiddleware` django middleware.
    """

    type = "user"

    def get_data_chunk(self, dispatch_context: DispatchContext, path: List[str]):
        """
        Loads the user_source_user from the request object and expose it to the
        formulas.
        """

        user = dispatch_context.request.user_source_user

        is_authenticated = user.is_authenticated

        if is_authenticated:
            user = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            }
        else:
            user = {"id": 0, "username": "", "email": ""}

        return get_nested_value_from_dict(
            {"is_authenticated": is_authenticated, **user}, path
        )
