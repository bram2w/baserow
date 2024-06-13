import json
from collections import defaultdict
from io import BytesIO
from tempfile import tempdir
from zipfile import ZIP_DEFLATED, ZipFile

from django.core.files.storage import FileSystemStorage

import pytest
from rest_framework.exceptions import ValidationError

from baserow.contrib.builder.data_providers.exceptions import (
    FormDataProviderChunkInvalidException,
)
from baserow.contrib.builder.elements.element_types import (
    CheckboxElementType,
    ChoiceElementType,
    IFrameElementType,
    ImageElementType,
    InputTextElementType,
)
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.mixins import (
    ContainerElementTypeMixin,
    FormElementTypeMixin,
)
from baserow.contrib.builder.elements.models import (
    CheckboxElement,
    ChoiceElement,
    ChoiceElementOption,
    HeadingElement,
    IFrameElement,
    ImageElement,
    InputTextElement,
    LinkElement,
)
from baserow.contrib.builder.elements.registries import (
    ElementType,
    element_type_registry,
)
from baserow.contrib.builder.elements.service import ElementService
from baserow.contrib.builder.pages.service import PageService
from baserow.core.user_files.handler import UserFileHandler
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

    serialized = {
        "id": 9999,
        "order": 42,
        "type": element_type.type,
        "parent_element_id": None,
    }
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
        {"required": True, "type": "integer", "value": 42, "result": 42},
        {"required": True, "type": "integer", "value": "42", "result": 42},
        {"required": True, "type": "integer", "value": "horse", "result": False},
        {"required": False, "type": "integer", "value": "", "result": ""},
        {
            "required": True,
            "type": "email",
            "value": "foo@bar.com",
            "result": "foo@bar.com",
        },
        {"required": True, "type": "email", "value": "foobar.com", "result": False},
        {"required": False, "type": "email", "value": "", "result": ""},
        {"required": True, "type": "any", "value": "", "result": False},
        {"required": True, "type": "any", "value": 42, "result": 42},
        {"required": True, "type": "any", "value": "42", "result": "42"},
        {"required": True, "type": "any", "value": "horse", "result": "horse"},
        {"required": False, "type": "any", "value": "", "result": ""},
    ]
    for test in validity_tests:
        if test["result"] is not False:
            assert (
                InputTextElementType().is_valid(
                    InputTextElement(
                        validation_type=test["type"], required=test["required"]
                    ),
                    test["value"],
                )
                == test["result"]
            ), repr(test["value"])
        else:
            with pytest.raises(FormDataProviderChunkInvalidException):
                InputTextElementType().is_valid(
                    InputTextElement(
                        validation_type=test["type"], required=test["required"]
                    ),
                    test["value"],
                )


@pytest.mark.django_db
def test_choice_element_import_serialized(data_fixture):
    parent = data_fixture.create_builder_page()
    choice_element = data_fixture.create_builder_choice_element(
        page=parent, label="'test'"
    )
    ChoiceElementOption.objects.create(
        choice=choice_element, value="hello", name="there"
    )
    serialized_values = ChoiceElementType().export_serialized(choice_element)
    id_mapping = {}

    choice_element_imported = ChoiceElementType().import_serialized(
        parent, serialized_values, id_mapping
    )

    assert choice_element.id != choice_element_imported.id
    assert choice_element.label == choice_element_imported.label

    options = choice_element_imported.choiceelementoption_set.all()

    assert ChoiceElementOption.objects.count() == 2
    assert len(options) == 1
    assert options[0].value == "hello"
    assert options[0].name == "there"
    assert options[0].choice_id == choice_element_imported.id


@pytest.mark.django_db
def test_choice_element_is_valid(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    choice = ElementService().create_element(
        user=user,
        element_type=element_type_registry.get("choice"),
        page=page,
    )
    choice.choiceelementoption_set.create(value="uk", name="United Kingdom")
    choice.choiceelementoption_set.create(value="it", name="Italy")

    choice.required = True

    with pytest.raises(FormDataProviderChunkInvalidException):
        ChoiceElementType().is_valid(choice, "")

    assert ChoiceElementType().is_valid(choice, "uk") == "uk"

    choice.multiple = True

    with pytest.raises(FormDataProviderChunkInvalidException):
        ChoiceElementType().is_valid(choice, [])

    with pytest.raises(FormDataProviderChunkInvalidException):
        ChoiceElementType().is_valid(choice, [""])

    assert ChoiceElementType().is_valid(choice, ["uk"]) == ["uk"]
    assert ChoiceElementType().is_valid(choice, "uk") == ["uk"]
    assert ChoiceElementType().is_valid(choice, ["uk", "it"]) == ["uk", "it"]
    assert ChoiceElementType().is_valid(choice, "uk,it") == ["uk", "it"]

    with pytest.raises(FormDataProviderChunkInvalidException):
        ChoiceElementType().is_valid(choice, ["uk", "it", "pt"])

    with pytest.raises(FormDataProviderChunkInvalidException):
        ChoiceElementType().is_valid(choice, "uk,it,pt")

    choice.multiple = False
    choice.required = False

    assert ChoiceElementType().is_valid(choice, "") == ""
    assert ChoiceElementType().is_valid(choice, "uk") == "uk"

    choice.multiple = True

    assert ChoiceElementType().is_valid(choice, []) == []
    assert ChoiceElementType().is_valid(choice, "") == []

    with pytest.raises(FormDataProviderChunkInvalidException):
        ChoiceElementType().is_valid(choice, [""])

    assert ChoiceElementType().is_valid(choice, ["uk"]) == ["uk"]
    assert ChoiceElementType().is_valid(choice, ["uk", "it"]) == ["uk", "it"]
    assert ChoiceElementType().is_valid(choice, "uk,it") == ["uk", "it"]

    with pytest.raises(FormDataProviderChunkInvalidException):
        ChoiceElementType().is_valid(choice, ["uk", "it", "pt"])

    choice.choiceelementoption_set.create(value="", name="Blank")
    choice.multiple = False
    choice.required = True

    assert ChoiceElementType().is_valid(choice, "") == ""

    choice.multiple = True
    with pytest.raises(FormDataProviderChunkInvalidException):
        ChoiceElementType().is_valid(choice, [])
    with pytest.raises(FormDataProviderChunkInvalidException):
        ChoiceElementType().is_valid(choice, "")

    assert ChoiceElementType().is_valid(choice, [""]) == [""]
    assert ChoiceElementType().is_valid(choice, ["uk"]) == ["uk"]
    assert ChoiceElementType().is_valid(choice, "uk") == ["uk"]
    assert ChoiceElementType().is_valid(choice, ["uk", "it"]) == ["uk", "it"]
    assert ChoiceElementType().is_valid(choice, "uk,it") == ["uk", "it"]
    assert ChoiceElementType().is_valid(choice, ["uk", "it", ""]) == [
        "uk",
        "it",
        "",
    ]

    with pytest.raises(FormDataProviderChunkInvalidException):
        ChoiceElementType().is_valid(choice, ["uk", "it", "", "pt"])

    choice.multiple = False
    choice.required = False

    assert ChoiceElementType().is_valid(choice, "uk") == "uk"

    choice.multiple = True

    assert ChoiceElementType().is_valid(choice, []) == []
    assert ChoiceElementType().is_valid(choice, [""]) == [""]
    assert ChoiceElementType().is_valid(choice, ["uk"]) == ["uk"]
    assert ChoiceElementType().is_valid(choice, ["uk", "it"]) == ["uk", "it"]
    assert ChoiceElementType().is_valid(choice, ["uk", "it", ""]) == [
        "uk",
        "it",
        "",
    ]

    with pytest.raises(FormDataProviderChunkInvalidException):
        ChoiceElementType().is_valid(choice, ["uk", "it", "", "pt"])


def test_element_type_import_element_priority():
    element_types = element_type_registry.get_all()
    container_element_types = [
        element_type
        for element_type in element_types
        if isinstance(element_type, ContainerElementTypeMixin)
    ]
    form_element_types = [
        element_type
        for element_type in element_types
        if isinstance(element_type, FormElementTypeMixin)
    ]
    other_element_types = [
        element_type
        for element_type in element_types
        if not isinstance(element_type, ContainerElementTypeMixin)
        and not isinstance(element_type, FormElementTypeMixin)
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
    with pytest.raises(FormDataProviderChunkInvalidException):
        CheckboxElementType().is_valid(CheckboxElement(required=True), False)

    with pytest.raises(FormDataProviderChunkInvalidException):
        CheckboxElementType().is_valid(CheckboxElement(required=True), 0)

    assert CheckboxElementType().is_valid(CheckboxElement(required=True), True) is True

    assert CheckboxElementType().is_valid(CheckboxElement(required=True), 1) is True
    assert (
        CheckboxElementType().is_valid(CheckboxElement(required=True), "true") is True
    )
    assert (
        CheckboxElementType().is_valid(CheckboxElement(required=False), False) is False
    )
    assert (
        CheckboxElementType().is_valid(CheckboxElement(required=False), "false")
        is False
    )
    assert CheckboxElementType().is_valid(CheckboxElement(required=False), 0) is False
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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "storage",
    [None, FileSystemStorage(location=str(tempdir), base_url="http://localhost")],
)
def test_image_element_import_export(data_fixture, fake, storage):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page()
    data_source_1 = data_fixture.create_builder_local_baserow_get_row_data_source()
    data_source_2 = data_fixture.create_builder_local_baserow_get_row_data_source()
    element_type = ImageElementType()

    zip_buffer = BytesIO()
    image_file = UserFileHandler().upload_user_file(
        user, "test.jpg", BytesIO(fake.image()), storage=storage
    )

    element_to_export = data_fixture.create_builder_element(
        ImageElement,
        image_source_type="upload",
        image_file=image_file,
        image_url=f"get('data_source.{data_source_1.id}.field_1')",
    )

    with ZipFile(zip_buffer, "a", ZIP_DEFLATED, False) as zip_file:
        serialized = element_type.export_serialized(
            element_to_export, files_zip=zip_file, storage=storage
        )

    # After applying the ID mapping the imported formula should have updated
    # the data source IDs
    id_mapping = {"builder_data_sources": {data_source_1.id: data_source_2.id}}

    # Let check if the file is actually imported from the zip_file
    image_file.delete()

    with ZipFile(zip_buffer, "r", ZIP_DEFLATED, False) as files_zip:
        imported_element = element_type.import_serialized(
            page, serialized, id_mapping, files_zip=files_zip, storage=storage
        )

    expected_formula = f"get('data_source.{data_source_2.id}.field_1')"
    assert imported_element.image_url == expected_formula
    assert (
        imported_element.image_file_id is not None
        and imported_element.image_file_id != element_to_export.image_file_id
    )


@pytest.mark.django_db
def test_choice_element_import_export(data_fixture):
    page = data_fixture.create_builder_page()
    data_source_2 = data_fixture.create_builder_local_baserow_get_row_data_source()
    element_type = ChoiceElementType()

    exported_element = data_fixture.create_builder_element(
        ChoiceElement,
        label=f"get('data_source.42.field_1')",
        default_value=f"get('data_source.42.field_1')",
        placeholder=f"get('data_source.42.field_1')",
        multiple=True,
    )
    serialized = element_type.export_serialized(exported_element)

    # Just check that the serialization works properly
    json.dumps(serialized)

    # After applying the ID mapping the imported formula should have updated
    # the data source IDs
    id_mapping = {"builder_data_sources": {42: data_source_2.id}}

    imported_element = element_type.import_serialized(page, serialized, id_mapping)

    expected_formula = f"get('data_source.{data_source_2.id}.field_1')"
    assert imported_element.label == expected_formula
    assert imported_element.default_value == expected_formula
    assert imported_element.placeholder == expected_formula

    assert imported_element.multiple is True


@pytest.mark.django_db
def test_choice_element_import_old_format(data_fixture):
    page = data_fixture.create_builder_page()
    element_type = ChoiceElementType()

    serialized = {
        "id": 1,
        "order": "1.00000000000000000000",
        "type": "dropdown",  # Element type is the old one
        "parent_element_id": None,
        "place_in_container": None,
        "visibility": "all",
        "style_border_top_color": "border",
        "style_border_top_size": 0,
        "style_padding_top": 10,
        "style_border_bottom_color": "border",
        "style_border_bottom_size": 0,
        "style_padding_bottom": 10,
        "style_border_left_color": "border",
        "style_border_left_size": 0,
        "style_padding_left": 20,
        "style_border_right_color": "border",
        "style_border_right_size": 0,
        "style_padding_right": 20,
        "style_background": "none",
        "style_background_color": "#ffffffff",
        "style_width": "normal",
        "label": "'label'",
        "required": False,
        "placeholder": "'test'",
        "default_value": "'default'",
        "options": [
            {"value": "Option 1", "name": "option1"},
            {"value": "Option 2", "name": "option2"},
        ],
        # multiple property is missing
        # show_as_dropdown property is  missing
    }

    imported_element = element_type.import_serialized(page, serialized, {})

    assert isinstance(imported_element.specific, ChoiceElement)
    assert imported_element.multiple is False
    assert imported_element.show_as_dropdown is True
    assert len(imported_element.choiceelementoption_set.all()) == 2
