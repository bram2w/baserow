import pytest

from baserow.api.exceptions import RequestBodyValidationException
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.elements.service import ElementService
from baserow_enterprise.builder.elements.element_types import AuthFormElementType
from baserow_enterprise.builder.elements.models import AuthFormElement


@pytest.mark.django_db
def test_auth_form_element_import_export_data_source(data_fixture):
    page = data_fixture.create_builder_page()
    user_source_1 = data_fixture.create_user_source_with_first_type(
        application=page.builder
    )
    user_source_2 = data_fixture.create_user_source_with_first_type(
        application=page.builder
    )
    element_type = AuthFormElementType()

    exported_element = data_fixture.create_builder_element(
        AuthFormElement, user_source=user_source_1
    )

    id_mapping = {"user_sources": {user_source_1.id: user_source_2.id}}
    serialized = element_type.export_serialized(exported_element)

    imported_element = element_type.import_serialized(page, serialized, id_mapping)

    assert imported_element.user_source.id == user_source_2.id


@pytest.mark.django_db
def test_create_auth_form_with_user_source(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    user_source_1 = data_fixture.create_user_source_with_first_type(
        application=page.builder
    )

    ElementService().create_element(
        user,
        element_type_registry.get("auth_form"),
        page=page,
        user_source_id=user_source_1.id,
    )


@pytest.mark.django_db
def test_create_auth_form_with_user_source_another_app(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    user_source_other_app = data_fixture.create_user_source_with_first_type(user=user)

    with pytest.raises(RequestBodyValidationException):
        ElementService().create_element(
            user,
            element_type_registry.get("auth_form"),
            page=page,
            user_source_id=user_source_other_app.id,
        )
