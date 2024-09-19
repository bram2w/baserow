from typing import TYPE_CHECKING, Optional

from django.http import HttpRequest

from baserow.contrib.builder.data_providers.registries import (
    builder_data_provider_type_registry,
)
from baserow.contrib.builder.pages.models import Page
from baserow.core.services.dispatch_context import DispatchContext

if TYPE_CHECKING:
    from baserow.core.workflow_actions.models import WorkflowAction


class BuilderDispatchContext(DispatchContext):
    own_properties = ["request", "page", "workflow_action", "offset", "count"]

    def __init__(
        self,
        request: HttpRequest,
        page: Page,
        workflow_action: Optional["WorkflowAction"] = None,
        offset: Optional[int] = None,
        count: Optional[int] = None,
    ):
        self.request = request
        self.page = page
        self.workflow_action = workflow_action

        # Overrides the `request` GET offset/count values.
        self.offset = offset
        self.count = count

        super().__init__()

    @property
    def data_provider_registry(self):
        return builder_data_provider_type_registry

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
