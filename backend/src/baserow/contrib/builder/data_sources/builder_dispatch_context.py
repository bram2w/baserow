from functools import cached_property
from typing import TYPE_CHECKING, Dict, List, Optional

from django.http import HttpRequest

from baserow.contrib.builder.data_providers.registries import (
    builder_data_provider_type_registry,
)
from baserow.contrib.builder.formula_property_extractor import get_formula_field_names
from baserow.contrib.builder.pages.models import Page
from baserow.core.feature_flags import feature_flag_is_enabled
from baserow.core.services.dispatch_context import DispatchContext

if TYPE_CHECKING:
    from baserow.core.workflow_actions.models import WorkflowAction

FEATURE_FLAG_EXCLUDE_UNUSED_FIELDS = "feature-exclude-unused-fields"


class BuilderDispatchContext(DispatchContext):
    own_properties = [
        "request",
        "page",
        "workflow_action",
        "offset",
        "count",
        "only_expose_public_formula_fields",
    ]

    def __init__(
        self,
        request: HttpRequest,
        page: Page,
        workflow_action: Optional["WorkflowAction"] = None,
        offset: Optional[int] = None,
        count: Optional[int] = None,
        only_expose_public_formula_fields: Optional[bool] = True,
    ):
        self.request = request
        self.page = page
        self.workflow_action = workflow_action

        # Overrides the `request` GET offset/count values.
        self.offset = offset
        self.count = count
        self.only_expose_public_formula_fields = only_expose_public_formula_fields

        super().__init__()

    @property
    def data_provider_registry(self):
        return builder_data_provider_type_registry

    @cached_property
    def public_formula_fields(self) -> Optional[Dict[str, Dict[int, List[str]]]]:
        """
        Return a Dict where keys are ["all", "external", "internal"] and values
        dicts. The internal dicts' keys are Service IDs and values are a list
        of Data Source field names.

        Returns None if field names shouldn't be included in the dispatch
        context. This is mainly to support a feature flag for this new feature.

        The field names are used to improve the security of the backend by
        ensuring only the minimum necessary data is exposed to the frontend.

        It is used to restrict the queryset as well as to discern which Data
        Source fields are external and safe (user facing) vs internal and
        sensitive (required only by the backend).
        """

        if self.only_expose_public_formula_fields and feature_flag_is_enabled(
            FEATURE_FLAG_EXCLUDE_UNUSED_FIELDS
        ):
            return get_formula_field_names(self.request.user, self.page)

        return None

    def range(self, service):
        """
        Return page range from the `offset`, `count` kwargs,
        or the GET parameters.
        """

        if self.offset is not None and self.count is not None:
            offset = self.offset
            count = self.count
        else:
            try:
                offset = int(self.request.GET.get("offset", 0))
            except ValueError:
                offset = 0

            try:
                count = int(self.request.GET.get("count", 20))
            except ValueError:
                count = 20

        # max prevent negative values
        return [
            max(0, offset),
            max(1, count),
        ]

    def search_query(self) -> Optional[str]:
        """
        In a `BuilderDispatchContext`, we will use the HTTP request
        to return the `search_query` provided by the frontend.

        :return: A search query string.
        """

        return self.request.GET.get("search_query", None)

    def filters(self) -> Optional[str]:
        """
        In a `BuilderDispatchContext`, we will use the HTTP request's
        serialized `filters`, pass it to the `AdHocFilters` class, and
        return the result.

        :return: A JSON serialized string.
        """

        return self.request.GET.get("filters", None)

    def sortings(self) -> Optional[str]:
        """
        In a `BuilderDispatchContext`, we will use the HTTP request
        to return the `order_by` provided by the frontend.

        :return: A sort string.
        """

        return self.request.GET.get("order_by", None)
