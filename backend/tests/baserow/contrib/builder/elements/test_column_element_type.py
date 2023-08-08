import pytest
from rest_framework.exceptions import ValidationError

from baserow.contrib.builder.elements.element_types import ColumnElementType
from baserow.contrib.builder.elements.models import Element


@pytest.mark.django_db
def test_get_new_place_in_container(data_fixture):
    column_element = data_fixture.create_builder_column_element(column_amount=3)

    assert ColumnElementType().get_new_place_in_container(column_element, ["2"]) == 1
    assert (
        ColumnElementType().get_new_place_in_container(column_element, ["2", "1"]) == 0
    )
    assert ColumnElementType().get_new_place_in_container(column_element, []) == 2


@pytest.mark.django_db
def test_get_places_in_container_removed(data_fixture):
    column_element = data_fixture.create_builder_column_element(column_amount=3)

    assert ColumnElementType().get_places_in_container_removed(
        {"column_amount": 2}, column_element
    ) == ["2"]
    assert ColumnElementType().get_places_in_container_removed(
        {"column_amount": 1}, column_element
    ) == ["1", "2"]
    assert (
        ColumnElementType().get_places_in_container_removed(
            {"column_amount": 3}, column_element
        )
        == []
    )
    assert ColumnElementType().get_places_in_container_removed(
        {"column_amount": 0}, column_element
    ) == ["0", "1", "2"]


@pytest.mark.django_db
def test_apply_order_by_children(data_fixture):
    column_element = data_fixture.create_builder_column_element(column_amount=20)
    first_element = data_fixture.create_builder_heading_element(
        parent_element=column_element, place_in_container="0"
    )
    last_element = data_fixture.create_builder_paragraph_element(
        parent_element=column_element, place_in_container="11"
    )
    middle_element = data_fixture.create_builder_paragraph_element(
        parent_element=column_element, place_in_container="5"
    )

    queryset = Element.objects.filter(parent_element=column_element)
    queryset_ordered = ColumnElementType().apply_order_by_children(queryset)

    ids_ordered = [element.id for element in queryset_ordered]

    assert ids_ordered == [first_element.id, middle_element.id, last_element.id]


@pytest.mark.django_db
def test_validate_place_in_container(data_fixture):
    column_element = data_fixture.create_builder_column_element(column_amount=2)

    with pytest.raises(ValidationError):
        ColumnElementType().validate_place_in_container("5", column_element)

    try:
        ColumnElementType().validate_place_in_container("1", column_element)
    except ValidationError:
        pytest.fail("Should not have raised since 1 is between 0-1")
