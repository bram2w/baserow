from typing import Dict, List, Optional

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.transaction import Atomic
from django.urls import include, path
from django.utils import translation
from django.utils.translation import gettext as _

from baserow.contrib.builder.api.serializers import BuilderSerializer
from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.pages.service import PageService
from baserow.core.models import Application
from baserow.core.registries import ApplicationType
from baserow.core.utils import ChildProgressBuilder


class BuilderApplicationType(ApplicationType):
    type = "builder"
    model_class = Builder
    instance_serializer_class = BuilderSerializer

    def get_api_urls(self):
        from .api import urls as api_urls

        return [
            path("builder/", include(api_urls, namespace=self.type)),
        ]

    def export_safe_transaction_context(self, application: Application) -> Atomic:
        return transaction.atomic()

    def init_application(self, user: AbstractUser, application: Application) -> None:
        with translation.override(user.profile.language):
            first_page_name = _("Page")

        PageService().create_page(user, application.specific, first_page_name)

    def export_pages_serialized(self, pages: List[Page]):
        """
        Exports all the pages given to a format that can be imported again to baserow
        via `import_pages_serialized`

        :param pages: The pages that are supposed to be exported
        :return:
        """

        from baserow.contrib.builder.api.pages.serializers import PageSerializer

        return [PageSerializer(page).data for page in pages]

    def import_pages_serialized(
        self,
        builder: Builder,
        serialized_pages: List[Dict[str, any]],
        progress_builder: Optional[ChildProgressBuilder] = None,
    ):
        """
        Import pages to builder. This method has to be compatible with the output
        of `export_pages_serialized`

        :param builder: The builder the pages where exported from
        :param serialized_pages: The pages that are supposed to be imported
        :param progress_builder: A progress builder that allows for publishing progress
        :return: The created page instances
        """

        progress = ChildProgressBuilder.build(
            progress_builder, child_total=len(serialized_pages)
        )

        pages = []

        for page in serialized_pages:
            page = PageHandler().create_page(builder, page["name"])
            pages.append(page)
            progress.increment(1)

        return pages
