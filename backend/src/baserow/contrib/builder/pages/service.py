from typing import List

from django.contrib.auth.models import AbstractUser

from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.operations import OrderPagesBuilderOperationType
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.pages.operations import (
    CreatePageOperationType,
    DeletePageOperationType,
    ReadPageOperationType,
    UpdatePageOperationType,
)
from baserow.contrib.builder.pages.signals import (
    page_created,
    page_deleted,
    page_updated,
    pages_reordered,
)
from baserow.core.handler import CoreHandler
from baserow.core.utils import extract_allowed


class PageService:
    def __init__(self):
        self.handler = PageHandler()

    def get_page(self, user: AbstractUser, page_id: int) -> Page:
        """
        Gets a page by ID

        :param user: The user requesting the page
        :param page_id: The ID of the page
        :return: The model instance of the Page
        """

        base_queryset = Page.objects.select_related("builder", "builder__group")
        page = self.handler.get_page(page_id, base_queryset=base_queryset)

        CoreHandler().check_permissions(
            user,
            ReadPageOperationType.type,
            group=page.builder.group,
            context=page,
        )

        return page

    def create_page(self, user: AbstractUser, builder: Builder, name: str) -> Page:
        """
        Creates a new page

        :param user: The user trying to create the page
        :param builder: The builder the page belongs to
        :param name: The name of the page
        :return: The newly created page instance
        """

        CoreHandler().check_permissions(
            user,
            CreatePageOperationType.type,
            group=builder.group,
            context=builder,
        )

        page = self.handler.create_page(builder, name)

        page_created.send(self, page=page, user=user)

        return page

    def delete_page(self, user: AbstractUser, page: Page):
        """
        Deletes the page provided

        :param user: The user trying to delete the page
        :param page: The page that must be deleted
        """

        CoreHandler().check_permissions(
            user,
            DeletePageOperationType.type,
            group=page.builder.group,
            context=page,
        )

        self.handler.delete_page(page)

        page_deleted.send(self, builder=page.builder, page_id=page.id, user=user)

    def update_page(self, user: AbstractUser, page: Page, **kwargs) -> Page:
        """
        Updates fields of a page

        :param user: The user trying to update the page
        :param page: The page that should be updated
        :param values: The fields that should be updated with their corresponding value
        :return: The updated page
        """

        CoreHandler().check_permissions(
            user,
            UpdatePageOperationType.type,
            group=page.builder.group,
            context=page,
        )

        allowed_updates = extract_allowed(kwargs, ["name"])

        self.handler.update_page(page, **allowed_updates)

        page_updated.send(self, page=page, user=user)

        return page

    def order_pages(
        self, user: AbstractUser, builder: Builder, order: List[int]
    ) -> List[int]:
        """
        Assigns a new order to the pages in a builder application.

        :param user: The user trying to order the pages
        :param builder: The builder that the pages belong to
        :param order: The new order of the pages
        :return: The new order of the pages
        """

        CoreHandler().check_permissions(
            user,
            OrderPagesBuilderOperationType.type,
            group=builder.group,
            context=builder,
        )

        all_pages = Page.objects.filter(builder_id=builder.id)
        user_pages = CoreHandler().filter_queryset(
            user,
            OrderPagesBuilderOperationType.type,
            all_pages,
            group=builder.group,
            context=builder,
        )

        full_order = self.handler.order_pages(builder, order, user_pages)

        pages_reordered.send(self, builder=builder, order=full_order, user=user)

        return full_order
