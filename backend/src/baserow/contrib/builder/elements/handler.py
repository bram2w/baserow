from typing import Iterable, List, Optional, Union, cast

from django.db.models import QuerySet

from baserow.contrib.builder.elements.exceptions import (
    ElementDoesNotExist,
    ElementNotInSamePage,
)
from baserow.contrib.builder.elements.models import ContainerElement, Element
from baserow.contrib.builder.elements.registries import (
    ElementType,
    element_type_registry,
)
from baserow.contrib.builder.pages.models import Page
from baserow.core.db import specific_iterator
from baserow.core.exceptions import IdDoesNotExist
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
        self,
        element_type: ElementType,
        page: Page,
        before: Optional[Element] = None,
        order: Optional[int] = None,
        **kwargs
    ) -> Element:
        """
        Creates a new element for a page.

        :param element_type: The type of the element.
        :param page: The page the element exists in.
        :param order: If set, the new element is inserted at this order ignoring before.
        :param before: If provided and no order is provided, will place the new element
            before the given element.
        :param kwargs: Additional attributes of the element.
        :raises CannotCalculateIntermediateOrder: If it's not possible to find an
            intermediate order. The full order of the element of the page must be
            recalculated in this case before calling this method again.
        :return: The created element.
        """

        parent_element_id = kwargs.get("parent_element_id", None)
        place_in_container = kwargs.get("place_in_container", None)

        if order is None:
            if before:
                order = Element.get_unique_order_before_element(
                    before, parent_element_id, place_in_container
                )
            else:
                order = Element.get_last_order(
                    page, parent_element_id, place_in_container
                )

        shared_allowed_fields = [
            "type",
            "parent_element_id",
            "place_in_container",
            "style_padding_top",
            "style_padding_bottom",
        ]
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

        shared_allowed_fields = [
            "parent_element_id",
            "place_in_container",
            "style_padding_top",
            "style_padding_bottom",
        ]
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
        self,
        element: ElementForUpdate,
        parent_element: Optional[Element],
        place_in_container: str,
        before: Optional[Element] = None,
    ) -> Element:
        """
        Moves the given element before the specified `before` element in the same page.

        :param element: The element to move.
        :param before: The element before which to move the `element`. If before is not
            specified, the element is moved at the end of the list.
        :param parent_element: The new parent element of the element.
        :param place_in_container: The new place in container of the element.
        :raises CannotCalculateIntermediateOrder: If it's not possible to find an
            intermediate order. The full order of the element of the page must be
            recalculated in this case before calling this method again.
        :return: The moved element.
        """

        parent_element_id = getattr(parent_element, "id", None)

        if parent_element is not None and place_in_container is not None:
            parent_element = parent_element.specific
            parent_element_type = element_type_registry.get_by_model(parent_element)
            parent_element_type.validate_place_in_container(
                place_in_container, parent_element
            )

        if before:
            element.order = Element.get_unique_order_before_element(
                before, parent_element_id, place_in_container
            )
        else:
            element.order = Element.get_last_order(
                element.page, parent_element_id, place_in_container
            )

        element.parent_element = parent_element
        element.place_in_container = place_in_container

        element.save()

        return element

    def order_elements(self, page: Page, order: List[int], base_qs=None) -> List[int]:
        """
        Assigns a new order to the elements on a page.
        You can provide a base_qs for pre-filter the elements affected by this change

        :param page: The page that the elements belong to
        :param order: The new order of the elements
        :param base_qs: A QS that can have filters already applied
        :raises ElementNotInSamePage: If the element is not part of the provided page
        :return: The new order of the elements
        """

        if base_qs is None:
            base_qs = Element.objects.filter(page=page)

        try:
            full_order = Element.order_objects(base_qs, order)
        except IdDoesNotExist:
            raise ElementNotInSamePage()

        return full_order

    def before_places_in_container_removed(
        self, container_element: ContainerElement, places: List[str]
    ) -> List[Element]:
        """
        This should be called before places in a container have been removed to make
        sure that all the elements that used to be in the removed containers are moved
        somewhere else.

        :param container_element: The container element affected
        :param places: The places that were removed
        :return: The elements that received a new order
        """

        element_type = element_type_registry.get_by_model(container_element)

        elements_being_moved = Element.objects.filter(
            parent_element=container_element,
            place_in_container__in=places,
        )

        element_count = elements_being_moved.count()

        if element_count == 0:
            return []

        new_place_in_container = element_type.get_new_place_in_container(
            container_element, places
        )

        new_order_values = Element.get_last_orders(
            container_element.page,
            container_element.id,
            new_place_in_container,
            amount=element_count,
        )

        elements_being_moved = element_type.apply_order_by_children(
            elements_being_moved
        )
        elements_being_moved = list(elements_being_moved)

        to_update = []
        for element in elements_being_moved:
            # Add order values in the same order
            element.order = new_order_values.pop(0)
            element.place_in_container = new_place_in_container
            to_update.append(element)

        Element.objects.bulk_update(to_update, ["order", "place_in_container"])

        return elements_being_moved

    def recalculate_full_orders(
        self,
        page: Page,
    ):
        """
        Recalculates the order to whole numbers of all elements of the given page.
        """

        Element.recalculate_full_orders(queryset=Element.objects.filter(page=page))
