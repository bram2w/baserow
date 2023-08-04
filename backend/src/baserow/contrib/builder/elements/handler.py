from typing import Iterable, Optional, Union, cast

from django.db.models import QuerySet

from baserow.contrib.builder.elements.exceptions import ElementDoesNotExist
from baserow.contrib.builder.elements.models import Element
from baserow.contrib.builder.elements.registries import ElementType
from baserow.contrib.builder.pages.models import Page
from baserow.core.db import specific_iterator
from baserow.core.utils import extract_allowed

from .types import ElementForUpdate


class ElementHandler:
    def get_element(
        self, element_id: int, base_queryset: Optional[QuerySet] = None
    ) -> Element:
        """
        Returns an element instance from the database.

        :param element_id: The ID of the element.
        :param base_queryset: The base queryset to use to build the query.
        :raises ElementDoesNotExist: If the element can't be found.
        :return: The element instance.
        """

        queryset = base_queryset if base_queryset is not None else Element.objects.all()

        try:
            element = (
                queryset.select_related(
                    "page", "page__builder", "page__builder__workspace"
                )
                .get(id=element_id)
                .specific
            )
        except Element.DoesNotExist:
            raise ElementDoesNotExist()

        return element

    def get_element_for_update(
        self, element_id: int, base_queryset: Optional[QuerySet] = None
    ) -> ElementForUpdate:
        """
        Returns an element instance from the database that can be safely updated.

        :param element_id: The ID of the element.
        :param base_queryset: The base queryset to use to build the query.
        :raises ElementDoesNotExist: If the element can't be found.
        :return: The element instance.
        """

        queryset = base_queryset if base_queryset is not None else Element.objects.all()

        queryset = queryset.select_for_update(of=("self",))

        return self.get_element(
            element_id,
            base_queryset=queryset,
        )

    def get_elements(
        self,
        page: Page,
        base_queryset: Optional[QuerySet] = None,
        specific: bool = True,
    ) -> Union[QuerySet[Element], Iterable[Element]]:
        """
        Gets all the specific elements of a given page.

        :param page: The page that holds the elements.
        :param base_queryset: The base queryset to use to build the query.
        :param specific: Whether to return the generic elements or the specific
            instances.
        :return: The elements of that page.
        """

        queryset = base_queryset if base_queryset is not None else Element.objects.all()

        queryset = queryset.filter(page=page)

        if specific:
            queryset = queryset.select_related("content_type")
            return specific_iterator(queryset)
        else:
            return queryset

    def create_element(
        self, element_type: ElementType, page: Page, before=None, **kwargs
    ) -> Element:
        """
        Creates a new element for a page.

        :param element_type: The type of the element.
        :param page: The page the element exists in.
        :param kwargs: Additional attributes of the element.
        :raises CannotCalculateIntermediateOrder: If it's not possible to find an
            intermediate order. The full order of the element of the page must be
            recalculated in this case before calling this method again.
        :return: The created element.
        """

        if before:
            order = Element.get_unique_order_before_element(before)
        else:
            order = Element.get_last_order(page)

        shared_allowed_fields = ["type", "style_padding_top", "style_padding_bottom"]
        allowed_values = extract_allowed(
            kwargs, shared_allowed_fields + element_type.allowed_fields
        )

        allowed_values = element_type.prepare_value_for_db(allowed_values)

        model_class = cast(Element, element_type.model_class)

        element = model_class(page=page, order=order, **allowed_values)
        element.save()

        return element

    def delete_element(self, element: Element):
        """
        Deletes an element.

        :param element: The to-be-deleted element.
        """

        element.delete()

    def update_element(self, element: ElementForUpdate, **kwargs) -> Element:
        """
        Updates and element with values. Will also check if the values are allowed
        to be set on the element first.

        :param element: The element that should be updated.
        :param kwargs: The values that should be set on the element.
        :return: The updated element.
        """

        shared_allowed_fields = ["style_padding_top", "style_padding_bottom"]
        allowed_updates = extract_allowed(
            kwargs, shared_allowed_fields + element.get_type().allowed_fields
        )

        allowed_updates = element.get_type().prepare_value_for_db(
            allowed_updates, instance=element
        )

        for key, value in allowed_updates.items():
            setattr(element, key, value)

        element.save()

        return element

    def move_element(
        self, element: ElementForUpdate, before: Optional[Element] = None
    ) -> Element:
        """
        Moves the given element before the specified `before` element in the same page.

        :param element: The element to move.
        :param before: The element before which to move the `element`. If before is not
            specified, the element is moved at the end of the list.
        :raises CannotCalculateIntermediateOrder: If it's not possible to find an
            intermediate order. The full order of the element of the page must be
            recalculated in this case before calling this method again.
        :return: The moved element.
        """

        if before:
            element.order = Element.get_unique_order_before_element(before)
        else:
            element.order = Element.get_last_order(element.page)

        element.save()

        return element

    def recalculate_full_orders(
        self,
        page: Page,
    ):
        """
        Recalculates the order to whole numbers of all elements of the given page.
        """

        Element.recalculate_full_orders(queryset=Element.objects.filter(page=page))
