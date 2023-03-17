from typing import List, Optional, cast

from django.contrib.auth.models import AbstractUser

from baserow.contrib.builder.elements.exceptions import ElementNotInPage
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.models import Element
from baserow.contrib.builder.elements.operations import (
    CreateElementOperationType,
    DeleteElementOperationType,
    ListElementsPageOperationType,
    OrderElementsPageOperationType,
    ReadElementOperationType,
    UpdateElementOperationType,
)
from baserow.contrib.builder.elements.registries import ElementType
from baserow.contrib.builder.elements.signals import (
    element_created,
    element_deleted,
    element_orders_recalculated,
    element_updated,
    elements_reordered,
)
from baserow.contrib.builder.pages.models import Page
from baserow.core.exceptions import CannotCalculateIntermediateOrder
from baserow.core.handler import CoreHandler


class ElementService:
    def __init__(self):
        self.handler = ElementHandler()

    def get_element(self, user: AbstractUser, element_id: int) -> Element:
        """
        Returns an element instance from the database. Also checks the user permissions.

        :param user: The user trying to get the element
        :param element_id: The ID of the element
        :return: The element instance
        """

        element = self.handler.get_element(element_id)

        CoreHandler().check_permissions(
            user,
            ReadElementOperationType.type,
            workspace=element.page.builder.workspace,
            context=element,
        )

        return element

    def get_elements(self, user: AbstractUser, page: Page) -> List[Element]:
        """
        Gets all the elements of a given page visible to the given user.

        :param user: The user trying to get the elements.
        :param page: The page that holds the elements.
        :return: The elements of that page.
        """

        CoreHandler().check_permissions(
            user,
            ListElementsPageOperationType.type,
            workspace=page.builder.workspace,
            context=page,
        )

        user_elements = CoreHandler().filter_queryset(
            user,
            ListElementsPageOperationType.type,
            Element.objects.all(),
            workspace=page.builder.workspace,
            context=page,
        )

        return self.handler.get_elements(page, base_queryset=user_elements)

    def create_element(
        self,
        user: AbstractUser,
        element_type: ElementType,
        page: Page,
        before: Optional[Element] = None,
        **kwargs,
    ) -> Element:
        """
        Creates a new element for a page given the user permissions.

        :param user: The user trying to create the element.
        :param element_type: The type of the element.
        :param page: The page the element exists in.
        :param before: If set, the new element is inserted before this element.
        :param kwargs: Additional attributes of the element.
        :return: The created element.
        """

        CoreHandler().check_permissions(
            user,
            CreateElementOperationType.type,
            workspace=page.builder.workspace,
            context=page,
        )

        model_class = cast(Element, element_type.model_class)

        if before:
            try:
                element_order = model_class.get_unique_order_before_element(
                    page, before
                )
            except CannotCalculateIntermediateOrder:
                # If the `find_intermediate_order` fails with a
                # `CannotCalculateIntermediateOrder`, it means that it's not possible
                # calculate an intermediate fraction. Therefore, must reset all the
                # orders of the elements (while respecting their original order),
                # so that we can then can find the fraction any many more after.
                self.recalculate_full_orders(user, page)
                # Refresh the before element as the order might have changed.
                before.refresh_from_db()
                element_order = model_class.get_unique_order_before_element(
                    page, before
                )
        else:
            element_order = model_class.get_last_order(page)

        new_element = self.handler.create_element(
            element_type, page, order=element_order, **kwargs
        )

        element_created.send(self, element=new_element, user=user)

        return new_element

    def update_element(self, user: AbstractUser, element: Element, **kwargs) -> Element:
        """
        Updates and element with values. Will also check if the values are allowed
        to be set on the element first.

        :param user: The user trying to update the element.
        :param element: The element that should be updated.
        :param values: The values that should be set on the element.
        :param kwargs: Additional attributes of the element.
        :return: The updated element.
        """

        CoreHandler().check_permissions(
            user,
            UpdateElementOperationType.type,
            workspace=element.page.builder.workspace,
            context=element,
        )

        element = self.handler.update_element(element, **kwargs)

        element_updated.send(self, element=element, user=user)

        return element

    def delete_element(self, user: AbstractUser, element: Element):
        """
        Deletes an element.

        :param user: The user trying to delete the element.
        :param element: The to-be-deleted element.
        """

        page = element.page

        CoreHandler().check_permissions(
            user,
            DeleteElementOperationType.type,
            workspace=element.page.builder.workspace,
            context=element,
        )

        self.handler.delete_element(element)

        element_deleted.send(self, element_id=element.id, page=page, user=user)

    def order_elements(
        self, user: AbstractUser, page: Page, new_order: List[int]
    ) -> List[int]:
        """
        Orders the elements of a page in a new order. The user must have the permissions
        over all elements matching the given ids.

        :param user: The user trying to re-order the elements.
        :param page: The page the elements exist on.
        :param new_order: The new order which they should have.
        :return: The full order of all elements after they have been ordered.
        """

        CoreHandler().check_permissions(
            user,
            OrderElementsPageOperationType.type,
            workspace=page.builder.workspace,
            context=page,
        )

        all_elements = Element.objects.filter(page=page)

        user_elements = CoreHandler().filter_queryset(
            user,
            OrderElementsPageOperationType.type,
            all_elements,
            workspace=page.builder.workspace,
            context=page,
        )

        element_ids = set(user_elements.values_list("id", flat=True))

        # Check if all ids belong to the page and if the user has access to it
        for element_id in new_order:
            if element_id not in element_ids:
                raise ElementNotInPage(element_id)

        full_order = self.handler.order_elements(page, new_order)

        elements_reordered.send(self, page=page, order=full_order, user=user)

        return full_order

    def recalculate_full_orders(self, user: AbstractUser, page: Page):
        """
        Recalculates the order to whole numbers of all elements of the given page and
        send a signal.
        """

        self.handler.recalculate_full_orders(page)

        element_orders_recalculated.send(self, page=page, user=user)
