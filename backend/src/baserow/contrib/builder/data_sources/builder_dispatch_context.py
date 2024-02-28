from rest_framework.request import Request

from baserow.contrib.builder.data_providers.registries import (
    builder_data_provider_type_registry,
)
from baserow.contrib.builder.pages.models import Page
from baserow.core.services.dispatch_context import DispatchContext


class BuilderDispatchContext(DispatchContext):
    def __init__(self, request: Request, page: Page):
        self.request = request
        self.page = page

        super().__init__()

    @property
    def data_provider_registry(self):
        return builder_data_provider_type_registry

    def range(self, service):
        """Return page range from the GET parameters."""

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
