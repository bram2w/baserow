from collections import defaultdict

import pytest
from rest_framework.exceptions import ValidationError

from baserow.contrib.builder.elements.element_types import InputTextElementType
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.models import InputTextElement, LinkElement
from baserow.contrib.builder.elements.registries import (
    ElementType,
    element_type_registry,
)
from baserow.core.utils import MirrorDict


def pytest_generate_tests(metafunc):
    if "element_type" in metafunc.fixturenames:
        metafunc.parametrize(
            "element_type",
            [pytest.param(e, id=e.type) for e in element_type_registry.get_all()],
        )


@pytest.mark.django_db
def test_export_element(data_fixture, element_type: ElementType):
    page = data_fixture.create_builder_page()
    pytest_params = element_type.get_pytest_params(data_fixture)
    element = data_fixture.create_builder_element(
        element_type.model_class, page=page, order=17, **pytest_params
    )

    exported = element_type.export_serialized(element)

    assert exported["id"] == element.id
    assert exported["type"] == element_type.type
    assert exported["order"] == str(element.order)

    for key, value in pytest_params.items():
        assert exported[key] == value


@pytest.mark.django_db
def test_import_element(data_fixture, element_type: ElementType):
    page = data_fixture.create_builder_page()
    pytest_params = element_type.get_pytest_params(data_fixture)

    serialized = {"id": 9999, "order": 42, "type": element_type.type}
    serialized.update(element_type.get_pytest_params(data_fixture))

    id_mapping = defaultdict(lambda: MirrorDict())
    element = element_type.import_serialized(page, serialized, id_mapping)

    assert element.id != 9999
    assert element.order == element.order
    assert isinstance(element, element_type.model_class)

    for key, value in pytest_params.items():
        assert getattr(element, key) == value


@pytest.mark.django_db
def test_link_element_path_parameter_does_not_exist(data_fixture):
    builder = data_fixture.create_builder_application()
    page = data_fixture.create_builder_page(builder=builder)
    page_with_params = data_fixture.create_builder_page(
        builder=builder,
        path="/test/:id",
        path_params=[{"name": "id", "type": "numeric"}],
    )

    link_element = data_fixture.create_builder_link_element(
        page=page,
        navigation_type=LinkElement.NAVIGATION_TYPES.PAGE,
        navigate_to_page=page_with_params,
    )

    with pytest.raises(ValidationError):
        ElementHandler().update_element(
            link_element, page_parameters=[{"name": "invalid", "value": "something"}]
        )


@pytest.mark.django_db
def test_link_element_path_parameter_does_not_exist_new_page(data_fixture):
    builder = data_fixture.create_builder_application()
    page = data_fixture.create_builder_page(builder=builder)
    page_with_params = data_fixture.create_builder_page(
        builder=builder,
        path="/test/:id",
        path_params=[{"name": "id", "type": "numeric"}],
    )

    link_element = data_fixture.create_builder_link_element(
        page=page,
    )

    with pytest.raises(ValidationError):
        ElementHandler().update_element(
            link_element,
            navigation_type=LinkElement.NAVIGATION_TYPES.PAGE,
            navigate_to_page_id=page_with_params.id,
            page_parameters=[{"name": "invalid", "value": "something"}],
        )


@pytest.mark.django_db
def test_input_text_element_import_export_formula(data_fixture):
    page = data_fixture.create_builder_page()
    data_source_1 = data_fixture.create_builder_local_baserow_get_row_data_source()
    data_source_2 = data_fixture.create_builder_local_baserow_get_row_data_source()
    element_type = InputTextElementType()

    exported_input_text_element = data_fixture.create_builder_element(
        InputTextElement,
        label=f"get('data_source.{data_source_1.id}.field_1')",
        default_value=f"get('data_source.{data_source_1.id}.field_1')",
        placeholder=f"get('data_source.{data_source_1.id}.field_1')",
    )
    serialized = element_type.export_serialized(exported_input_text_element)

    # After applying the ID mapping the imported formula should have updated
    # the data source IDs
    id_mapping = {"builder_data_sources": {data_source_1.id: data_source_2.id}}
    imported_element = element_type.import_serialized(page, serialized, id_mapping)

    expected_formula = f"get('data_source.{data_source_2.id}.field_1')"
    assert imported_element.label == expected_formula
    assert imported_element.default_value == expected_formula
    assert imported_element.placeholder == expected_formula
