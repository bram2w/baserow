import pytest

from baserow.contrib.builder.application_types import BuilderApplicationType
from baserow.contrib.builder.elements.models import HeadingElement, ParagraphElement
from baserow.contrib.builder.pages.models import Page
from baserow.core.db import specific_iterator


@pytest.mark.django_db
def test_builder_application_type_init_application(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)

    assert Page.objects.count() == 0

    BuilderApplicationType().init_application(user, builder)

    assert Page.objects.count() == 1


@pytest.mark.django_db
def test_builder_application_export(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)

    page1 = data_fixture.create_builder_page(builder=builder)
    page2 = data_fixture.create_builder_page(builder=builder)

    element1 = data_fixture.create_builder_heading_element(
        page=page1, level=2, value="foo"
    )
    element2 = data_fixture.create_builder_paragraph_element(page=page1)
    element3 = data_fixture.create_builder_heading_element(page=page2)

    serialized = BuilderApplicationType().export_serialized(builder)

    assert serialized == {
        "pages": [
            {
                "id": page1.id,
                "name": page1.name,
                "order": page1.order,
                "elements": [
                    {
                        "id": element1.id,
                        "type": "heading",
                        "order": element1.order,
                        "value": element1.value,
                        "level": element1.level,
                    },
                    {
                        "id": element2.id,
                        "type": "paragraph",
                        "order": element2.order,
                        "value": element2.value,
                    },
                ],
            },
            {
                "id": page2.id,
                "name": page2.name,
                "order": page2.order,
                "elements": [
                    {
                        "id": element3.id,
                        "type": "heading",
                        "order": element3.order,
                        "value": element3.value,
                        "level": element3.level,
                    },
                ],
            },
        ],
        "id": builder.id,
        "name": builder.name,
        "order": builder.order,
        "type": "builder",
    }


IMPORT_REFERENCE = {
    "pages": [
        {
            "id": 999,
            "name": "Tammy Hall",
            "order": 1,
            "elements": [
                {
                    "id": 998,
                    "type": "heading",
                    "order": 1,
                    "value": "foo",
                    "level": 2,
                },
                {
                    "id": 999,
                    "type": "paragraph",
                    "order": 2,
                    "value": "",
                },
            ],
        },
        {
            "id": 998,
            "name": "Megan Clark",
            "order": 2,
            "elements": [
                {
                    "id": 997,
                    "type": "heading",
                    "order": 1,
                    "value": "",
                    "level": 1,
                }
            ],
        },
    ],
    "id": 999,
    "name": "Holly Sherman",
    "order": 0,
    "type": "builder",
}


@pytest.mark.django_db
def test_builder_application_import(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)

    builder = BuilderApplicationType().import_serialized(
        workspace, IMPORT_REFERENCE, {}
    )

    assert builder.id != IMPORT_REFERENCE["id"]
    assert builder.page_set.count() == 2

    assert builder.page_set.count() == 2

    [page1, page2] = builder.page_set.all()

    assert page1.element_set.count() == 2
    assert page2.element_set.count() == 1

    [element1, element2] = specific_iterator(page1.element_set.all())

    assert isinstance(element1, HeadingElement)
    assert isinstance(element2, ParagraphElement)

    assert element1.order == 1
    assert element1.level == 2
