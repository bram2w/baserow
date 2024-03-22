from collections import defaultdict

import pytest
from rest_framework.exceptions import ValidationError

from baserow.contrib.builder.elements.element_types import (
    CheckboxElementType,
    ContainerElementType,
    DropdownElementType,
    FormElementType,
    IFrameElementType,
    InputTextElementType,
)
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.models import (
    CheckboxElement,
    DropdownElementOption,
    HeadingElement,
    IFrameElement,
    InputTextElement,
    LinkElement,
)
from baserow.contrib.builder.elements.registries import (
    ElementType,
    element_type_registry,
)
from baserow.contrib.builder.elements.service import ElementService
from baserow.contrib.builder.pages.service import PageService
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


@pytest.mark.django_db
def test_input_text_element_is_valid(data_fixture):
    validity_tests = [
        {"required": True, "type": "integer", "value": "", "result": False},
        {"required": True, "type": "integer", "value": 42, "result": True},
        {"required": True, "type": "integer", "value": "horse", "result": False},
        {"required": False, "type": "integer", "value": "", "result": True},
        {"required": True, "type": "email", "value": "foo@bar.com", "result": True},
        {"required": True, "type": "email", "value": "foobar.com", "result": False},
        {"required": False, "type": "email", "value": "", "result": True},
        {"required": True, "type": "any", "value": "", "result": False},
        {"required": True, "type": "any", "value": 42, "result": True},
        {"required": True, "type": "any", "value": "horse", "result": True},
        {"required": False, "type": "any", "value": "", "result": True},
    ]
    for test in validity_tests:
        assert (
            InputTextElementType().is_valid(
                InputTextElement(
                    validation_type=test["type"], required=test["required"]
                ),
                test["value"],
            )
        ) is test[
            "result"
        ], f"Failed InputTextElementType for validation_type={test['type']}, required={test['required']}, value={test['value']}"


@pytest.mark.django_db
def test_dropdown_element_import_serialized(data_fixture):
    parent = data_fixture.create_builder_page()
    dropdown_element = data_fixture.create_builder_dropdown_element(
        page=parent, label="'test'"
    )
    DropdownElementOption.objects.create(
        dropdown=dropdown_element, value="hello", name="there"
    )
    serialized_values = DropdownElementType().export_serialized(dropdown_element)
    id_mapping = {}

    dropdown_element_imported = DropdownElementType().import_serialized(
        parent, serialized_values, id_mapping
    )

    assert dropdown_element.id != dropdown_element_imported.id
    assert dropdown_element.label == dropdown_element_imported.label

    options = dropdown_element_imported.dropdownelementoption_set.all()

    assert DropdownElementOption.objects.count() == 2
    assert len(options) == 1
    assert options[0].value == "hello"
    assert options[0].name == "there"
    assert options[0].dropdown_id == dropdown_element_imported.id


@pytest.mark.django_db
def test_dropdown_element_is_valid(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    dropdown = ElementService().create_element(
        user=user,
        element_type=element_type_registry.get("dropdown"),
        page=page,
    )
    dropdown.dropdownelementoption_set.create(value="uk", name="United Kingdom")

    dropdown.required = True
    assert DropdownElementType().is_valid(dropdown, "") is False
    assert DropdownElementType().is_valid(dropdown, "uk") is True

    dropdown.required = False
    assert DropdownElementType().is_valid(dropdown, "") is True
    assert DropdownElementType().is_valid(dropdown, "uk") is True

    dropdown.dropdownelementoption_set.create(value="", name="Blank")
    dropdown.required = True
    assert DropdownElementType().is_valid(dropdown, "") is True
    dropdown.required = False
    assert DropdownElementType().is_valid(dropdown, "uk") is True


def test_element_type_import_element_priority():
    element_types = element_type_registry.get_all()
    container_element_types = [
        element_type
        for element_type in element_types
        if isinstance(element_type, ContainerElementType)
    ]
    form_element_types = [
        element_type
        for element_type in element_types
        if isinstance(element_type, FormElementType)
    ]
    other_element_types = [
        element_type
        for element_type in element_types
        if not isinstance(element_type, ContainerElementType)
        and not isinstance(element_type, FormElementType)
    ]
    manual_ordering = container_element_types + form_element_types + other_element_types
    expected_ordering = sorted(
        element_types,
        key=lambda element_type: element_type.import_element_priority,
        reverse=True,
    )
    assert manual_ordering == expected_ordering, (
        "The element types ordering are expected to be: "
        "containers first, then form elements, then everything else."
    )


@pytest.mark.django_db
def test_page_with_element_using_form_data_has_dependencies_import_first(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    form_container = data_fixture.create_builder_form_container_element(page=page)
    form_input = data_fixture.create_builder_input_text_element(
        page=page, parent_element=form_container
    )
    data_fixture.create_builder_heading_element(
        page=page, value=f"get('form_data.{form_input.id}')"
    )

    page_clone = PageService().duplicate_page(user, page)

    form_input_clone = InputTextElement.objects.get(page=page_clone)
    heading_clone = HeadingElement.objects.get(page=page_clone)
    assert heading_clone.value == f"get('form_data.{form_input_clone.id}')"


@pytest.mark.django_db
def test_checkbox_element_import_export_formula(data_fixture):
    page = data_fixture.create_builder_page()
    data_source_1 = data_fixture.create_builder_local_baserow_get_row_data_source()
    data_source_2 = data_fixture.create_builder_local_baserow_get_row_data_source()
    element_type = CheckboxElementType()

    exported_input_element = data_fixture.create_builder_element(
        CheckboxElement,
        label=f"get('data_source.{data_source_1.id}.field_1')",
        default_value=f"get('data_source.{data_source_1.id}.field_1')",
    )
    serialized = element_type.export_serialized(exported_input_element)

    # After applying the ID mapping the imported formula should have updated
    # the data source IDs
    id_mapping = {"builder_data_sources": {data_source_1.id: data_source_2.id}}
    imported_element = element_type.import_serialized(page, serialized, id_mapping)

    expected_formula = f"get('data_source.{data_source_2.id}.field_1')"
    assert imported_element.label == expected_formula
    assert imported_element.default_value == expected_formula


@pytest.mark.django_db
def test_checkbox_text_element_is_valid(data_fixture):
    assert (
        CheckboxElementType().is_valid(CheckboxElement(required=True), False) is False
    )
    assert CheckboxElementType().is_valid(CheckboxElement(required=True), True) is True
    assert (
        CheckboxElementType().is_valid(CheckboxElement(required=False), False) is True
    )
    assert CheckboxElementType().is_valid(CheckboxElement(required=False), True) is True


@pytest.mark.django_db
def test_iframe_element_import_export_formula(data_fixture):
    page = data_fixture.create_builder_page()
    data_source_1 = data_fixture.create_builder_local_baserow_get_row_data_source()
    data_source_2 = data_fixture.create_builder_local_baserow_get_row_data_source()
    element_type = IFrameElementType()

    exported_element = data_fixture.create_builder_element(
        IFrameElement,
        url=f"get('data_source.{data_source_1.id}.field_1')",
        embed=f"get('data_source.{data_source_1.id}.field_1')",
    )
    serialized = element_type.export_serialized(exported_element)

    # After applying the ID mapping the imported formula should have updated
    # the data source IDs
    id_mapping = {"builder_data_sources": {data_source_1.id: data_source_2.id}}
    imported_element = element_type.import_serialized(page, serialized, id_mapping)

    expected_formula = f"get('data_source.{data_source_2.id}.field_1')"
    assert imported_element.url == expected_formula
    assert imported_element.embed == expected_formula
