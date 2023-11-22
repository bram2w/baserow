from collections import defaultdict

import pytest
from rest_framework.exceptions import ValidationError

from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.models import LinkElement
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
    sample_params = element_type.get_sample_params()
    element = data_fixture.create_builder_element(
        element_type.model_class, page=page, order=17, **sample_params
    )

    exported = element_type.export_serialized(element)

    assert exported["id"] == element.id
    assert exported["type"] == element_type.type
    assert exported["order"] == str(element.order)

    for key, value in sample_params.items():
        assert exported[key] == value


@pytest.mark.django_db
def test_import_element(data_fixture, element_type: ElementType):
    page = data_fixture.create_builder_page()
    sample_params = element_type.get_sample_params()

    serialized = {"id": 9999, "order": 42, "type": element_type.type}
    serialized.update(element_type.get_sample_params())

    id_mapping = defaultdict(lambda: MirrorDict())
    element = element_type.import_serialized(page, serialized, id_mapping)

    assert element.id != 9999
    assert element.order == element.order
    assert isinstance(element, element_type.model_class)

    for key, value in sample_params.items():
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
