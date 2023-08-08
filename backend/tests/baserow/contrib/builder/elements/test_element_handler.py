from decimal import Decimal

import pytest

from baserow.contrib.builder.elements.element_types import (
    ColumnElementType,
    ParagraphElementType,
)
from baserow.contrib.builder.elements.exceptions import (
    ElementDoesNotExist,
    ElementNotInSamePage,
)
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.models import (
    Element,
    HeadingElement,
    ParagraphElement,
)
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.core.exceptions import CannotCalculateIntermediateOrder


def pytest_generate_tests(metafunc):
    if "element_type" in metafunc.fixturenames:
        metafunc.parametrize(
            "element_type",
            [pytest.param(e, id=e.type) for e in element_type_registry.get_all()],
        )


@pytest.mark.django_db
def test_create_element(data_fixture, element_type):
    page = data_fixture.create_builder_page()

    sample_params = element_type.get_sample_params()

    element = ElementHandler().create_element(element_type, page=page, **sample_params)

    assert element.page.id == page.id

    for key, value in sample_params.items():
        assert getattr(element, key) == value

    assert element.order == 1
    assert Element.objects.count() == 1


@pytest.mark.django_db
def test_get_element(data_fixture):
    element = data_fixture.create_builder_heading_element()
    assert ElementHandler().get_element(element.id).id == element.id


@pytest.mark.django_db
def test_get_element_does_not_exist(data_fixture):
    with pytest.raises(ElementDoesNotExist):
        assert ElementHandler().get_element(0)


@pytest.mark.django_db
def test_get_elements(data_fixture):
    page = data_fixture.create_builder_page()
    element1 = data_fixture.create_builder_heading_element(page=page)
    element2 = data_fixture.create_builder_heading_element(page=page)
    element3 = data_fixture.create_builder_paragraph_element(page=page)

    elements = ElementHandler().get_elements(page)

    assert [e.id for e in elements] == [
        element1.id,
        element2.id,
        element3.id,
    ]

    assert isinstance(elements[0], HeadingElement)
    assert isinstance(elements[2], ParagraphElement)


@pytest.mark.django_db
def test_delete_element(data_fixture):
    element = data_fixture.create_builder_heading_element()

    ElementHandler().delete_element(element)

    assert Element.objects.count() == 0


@pytest.mark.django_db
def test_update_element(data_fixture):
    user = data_fixture.create_user()
    element = data_fixture.create_builder_heading_element(user=user)

    element_updated = ElementHandler().update_element(element, value="newValue")

    assert element_updated.value == "newValue"


@pytest.mark.django_db
def test_update_element_invalid_values(data_fixture):
    element = data_fixture.create_builder_heading_element()

    element_updated = ElementHandler().update_element(element, nonsense="hello")

    assert not hasattr(element_updated, "nonsense")


@pytest.mark.django_db
def test_move_element_end_of_page(data_fixture):
    page = data_fixture.create_builder_page()
    element1 = data_fixture.create_builder_heading_element(page=page)
    element2 = data_fixture.create_builder_heading_element(page=page)
    element3 = data_fixture.create_builder_heading_element(page=page)

    element_moved = ElementHandler().move_element(
        element1, element1.parent_element, element1.place_in_container
    )

    assert Element.objects.filter(page=page).last().id == element_moved.id


@pytest.mark.django_db
def test_move_element_before(data_fixture):
    page = data_fixture.create_builder_page()
    element1 = data_fixture.create_builder_heading_element(page=page)
    element2 = data_fixture.create_builder_heading_element(page=page)
    element3 = data_fixture.create_builder_heading_element(page=page)

    ElementHandler().move_element(
        element3, element3.parent_element, element3.place_in_container, before=element2
    )

    assert [e.id for e in Element.objects.filter(page=page).all()] == [
        element1.id,
        element3.id,
        element2.id,
    ]


@pytest.mark.django_db
def test_move_element_before_fails(data_fixture):
    page = data_fixture.create_builder_page()
    element1 = data_fixture.create_builder_heading_element(
        page=page, order="2.99999999999999999998"
    )
    element2 = data_fixture.create_builder_heading_element(
        page=page, order="2.99999999999999999999"
    )
    element3 = data_fixture.create_builder_heading_element(page=page, order="3.0000")

    with pytest.raises(CannotCalculateIntermediateOrder):
        ElementHandler().move_element(
            element3,
            element3.parent_element,
            element3.place_in_container,
            before=element2,
        )


@pytest.mark.django_db
def test_creating_element_in_container_starts_its_own_order_sequence(data_fixture):
    page = data_fixture.create_builder_page()
    container = ElementHandler().create_element(ColumnElementType(), page=page)
    root_element = ElementHandler().create_element(ParagraphElementType(), page=page)
    element_inside_container_one = ElementHandler().create_element(
        ParagraphElementType(),
        page=page,
        parent_element_id=container.id,
        place_in_container="1",
    )
    element_inside_container_two = ElementHandler().create_element(
        ParagraphElementType(),
        page=page,
        parent_element_id=container.id,
        place_in_container="1",
    )

    # Irrespective of the order the elements were created, we need to assert that a new
    # order has started inside the container
    assert container.order < root_element.order
    assert element_inside_container_one.order < element_inside_container_two.order
    assert element_inside_container_one.order < root_element.order


@pytest.mark.django_db
def test_moving_elements_inside_container(data_fixture):
    page = data_fixture.create_builder_page()
    container = ElementHandler().create_element(ColumnElementType(), page=page)
    root_element = ElementHandler().create_element(ParagraphElementType(), page=page)
    element_inside_container_one = ElementHandler().create_element(
        ParagraphElementType(),
        page=page,
        parent_element_id=container.id,
        place_in_container="1",
    )
    element_inside_container_two = ElementHandler().create_element(
        ParagraphElementType(),
        page=page,
        parent_element_id=container.id,
        place_in_container="1",
    )

    ElementHandler().move_element(
        element_inside_container_two,
        element_inside_container_two.parent_element,
        element_inside_container_two.place_in_container,
        before=element_inside_container_one,
    )

    assert element_inside_container_two.order < element_inside_container_one.order
    assert element_inside_container_two.order < root_element.order
    assert element_inside_container_one.order < root_element.order


@pytest.mark.django_db
def test_recalculate_full_orders(data_fixture):
    page = data_fixture.create_builder_page()
    element1 = data_fixture.create_builder_heading_element(
        page=page, order="1.99999999999999999999"
    )
    element2 = data_fixture.create_builder_heading_element(
        page=page, order="2.00000000000000000000"
    )
    element3 = data_fixture.create_builder_heading_element(
        page=page, order="1.99999999999999999999"
    )
    element4 = data_fixture.create_builder_heading_element(
        page=page, order="2.10000000000000000000"
    )
    element5 = data_fixture.create_builder_heading_element(
        page=page, order="3.00000000000000000000"
    )
    element6 = data_fixture.create_builder_heading_element(
        page=page, order="1.00000000000000000001"
    )
    element7 = data_fixture.create_builder_heading_element(
        page=page, order="3.99999999999999999999"
    )
    element8 = data_fixture.create_builder_heading_element(
        page=page, order="4.00000000000000000001"
    )

    page2 = data_fixture.create_builder_page()

    elementA = data_fixture.create_builder_heading_element(
        page=page2, order="1.99999999999999999999"
    )
    elementB = data_fixture.create_builder_heading_element(
        page=page2, order="2.00300000000000000000"
    )

    ElementHandler().recalculate_full_orders(page)

    elements = Element.objects.filter(page=page)
    assert elements[0].id == element6.id
    assert elements[0].order == Decimal("1.00000000000000000000")

    assert elements[1].id == element1.id
    assert elements[1].order == Decimal("2.00000000000000000000")

    assert elements[2].id == element3.id
    assert elements[2].order == Decimal("3.00000000000000000000")

    assert elements[3].id == element2.id
    assert elements[3].order == Decimal("4.00000000000000000000")

    assert elements[4].id == element4.id
    assert elements[4].order == Decimal("5.00000000000000000000")

    assert elements[5].id == element5.id
    assert elements[5].order == Decimal("6.00000000000000000000")

    assert elements[6].id == element7.id
    assert elements[6].order == Decimal("7.00000000000000000000")

    assert elements[7].id == element8.id
    assert elements[7].order == Decimal("8.00000000000000000000")

    # Other page elements shouldn't be reordered
    elements = Element.objects.filter(page=page2)
    assert elements[0].id == elementA.id
    assert elements[0].order == Decimal("1.99999999999999999999")

    assert elements[1].id == elementB.id
    assert elements[1].order == Decimal("2.00300000000000000000")


@pytest.mark.django_db
def test_order_elements(data_fixture):
    page = data_fixture.create_builder_page()
    element_one = data_fixture.create_builder_heading_element(
        order="1.00000000000000000000", page=page
    )
    element_two = data_fixture.create_builder_heading_element(
        order="2.00000000000000000000", page=page
    )

    ElementHandler().order_elements(page, [element_two.id, element_one.id])

    element_one.refresh_from_db()
    element_two.refresh_from_db()

    assert element_one.order > element_two.order


@pytest.mark.django_db
def test_order_elements_not_in_page(data_fixture):
    page = data_fixture.create_builder_page()
    element_one = data_fixture.create_builder_heading_element(
        order="1.00000000000000000000", page=page
    )
    element_two = data_fixture.create_builder_heading_element(
        order="2.00000000000000000000"
    )

    with pytest.raises(ElementNotInSamePage):
        ElementHandler().order_elements(page, [element_two.id, element_one.id])


@pytest.mark.django_db
def test_before_places_in_container_removed(data_fixture):
    column_element = data_fixture.create_builder_column_element(column_amount=3)

    element_one = data_fixture.create_builder_heading_element(
        parent_element=column_element, place_in_container="2"
    )
    element_two = data_fixture.create_builder_heading_element(
        parent_element=column_element, place_in_container="1"
    )

    result = ElementHandler().before_places_in_container_removed(
        column_element, ["1", "2"]
    )
    result_specific = [element.specific for element in result]

    element_one.refresh_from_db()
    element_two.refresh_from_db()

    assert element_one.place_in_container == "0"
    assert element_two.place_in_container == "0"
    assert element_one.order > element_two.order
    assert result_specific == [element_two, element_one]


@pytest.mark.django_db
def test_before_places_in_container_removed_no_change(data_fixture):
    column_element = data_fixture.create_builder_column_element(column_amount=3)

    element_one = data_fixture.create_builder_heading_element(
        parent_element=column_element, place_in_container="0"
    )
    element_two = data_fixture.create_builder_heading_element(
        parent_element=column_element, place_in_container="0"
    )

    result = ElementHandler().before_places_in_container_removed(
        column_element, ["1", "2"]
    )

    element_one.refresh_from_db()
    element_two.refresh_from_db()

    assert element_one.place_in_container == "0"
    assert element_two.place_in_container == "0"
    assert result == []
