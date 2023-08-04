import pytest

from baserow.contrib.builder.pages.constants import ILLEGAL_PATH_SAMPLE_CHARACTER
from baserow.contrib.builder.pages.exceptions import (
    DuplicatePathParamsInPath,
    PageDoesNotExist,
    PageNameNotUnique,
    PageNotInBuilder,
    PagePathNotUnique,
    PathParamNotDefined,
    PathParamNotInPath,
)
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.pages.models import Page


@pytest.mark.django_db
def test_get_page(data_fixture):
    page = data_fixture.create_builder_page()
    assert PageHandler().get_page(page.id).id == page.id


@pytest.mark.django_db
def test_get_page_page_does_not_exist(data_fixture):
    with pytest.raises(PageDoesNotExist):
        PageHandler().get_page(9999)


@pytest.mark.django_db
def test_get_page_base_queryset(data_fixture, django_assert_num_queries):
    page = data_fixture.create_builder_page()

    # With selecting related
    base_queryset = Page.objects.exclude(id=page.id)

    with pytest.raises(PageDoesNotExist):
        PageHandler().get_page(page.id, base_queryset=base_queryset)


@pytest.mark.django_db
def test_create_page(data_fixture):
    builder = data_fixture.create_builder_application()
    expected_order = Page.get_last_order(builder)

    page = PageHandler().create_page(builder, "test", path="/test")

    assert page.order == expected_order
    assert page.name == "test"


@pytest.mark.django_db
def test_create_page_page_name_not_unique(data_fixture):
    page = data_fixture.create_builder_page(name="test", path="/test")

    with pytest.raises(PageNameNotUnique):
        PageHandler().create_page(page.builder, name="test", path="/new")


@pytest.mark.django_db
def test_create_page_page_path_not_unique(data_fixture):
    page = data_fixture.create_builder_page(path="/test/test")

    with pytest.raises(PagePathNotUnique):
        PageHandler().create_page(page.builder, name="test", path="/test/test")


@pytest.mark.django_db
def test_create_page_duplicate_params_in_path(data_fixture):
    builder = data_fixture.create_builder_application()

    with pytest.raises(DuplicatePathParamsInPath):
        PageHandler().create_page(
            builder,
            name="test",
            path="/test/:test/:test",
            path_params=[{"name": "test", "param_type": "text"}],
        )


@pytest.mark.django_db
def test_delete_page(data_fixture):
    page = data_fixture.create_builder_page()

    PageHandler().delete_page(page)

    assert Page.objects.count() == 0


@pytest.mark.django_db
def test_update_page(data_fixture):
    page = data_fixture.create_builder_page(name="test")

    PageHandler().update_page(page, name="new")

    page.refresh_from_db()

    assert page.name == "new"


@pytest.mark.django_db
def test_update_page_page_name_not_unique(data_fixture):
    page = data_fixture.create_builder_page(name="test")
    page_two = data_fixture.create_builder_page(builder=page.builder, name="test2")

    with pytest.raises(PageNameNotUnique):
        PageHandler().update_page(page_two, name=page.name)


@pytest.mark.django_db
def test_update_page_page_path_not_unique(data_fixture):
    page = data_fixture.create_builder_page()
    page_two = data_fixture.create_builder_page(builder=page.builder)

    with pytest.raises(PagePathNotUnique):
        PageHandler().update_page(page_two, path=page.path)


@pytest.mark.django_db
def test_order_pages(data_fixture):
    builder = data_fixture.create_builder_application()
    page_one = data_fixture.create_builder_page(builder=builder, order=1)
    page_two = data_fixture.create_builder_page(builder=builder, order=2)

    assert PageHandler().order_pages(builder, [page_two.id, page_one.id]) == [
        page_two.id,
        page_one.id,
    ]

    page_one.refresh_from_db()
    page_two.refresh_from_db()

    assert page_one.order == 2
    assert page_two.order == 1


@pytest.mark.django_db
def test_order_pages_page_not_in_builder(data_fixture):
    builder = data_fixture.create_builder_application()
    page_one = data_fixture.create_builder_page(builder=builder, order=1)
    page_two = data_fixture.create_builder_page(builder=builder, order=2)

    base_qs = Page.objects.filter(id=page_two.id)

    with pytest.raises(PageNotInBuilder):
        PageHandler().order_pages(builder, [page_two.id, page_one.id], base_qs=base_qs)


@pytest.mark.django_db
def test_duplicate_page(data_fixture):
    page = data_fixture.create_builder_page()

    page_clone = PageHandler().duplicate_page(page)

    assert Page.objects.count() == 2
    assert page_clone.id != page.id
    assert page_clone.name != page.name
    assert page_clone.order != page.order


def test_is_page_path_valid():
    assert PageHandler().is_page_path_valid("test/", []) is True
    assert PageHandler().is_page_path_valid("test/:id", []) is False
    assert (
        PageHandler().is_page_path_valid(
            "test/", [{"name": "id", "param_type": "text"}]
        )
        is False
    )
    assert (
        PageHandler().is_page_path_valid(
            "test/:", [{"name": "id", "param_type": "text"}]
        )
        is False
    )
    assert PageHandler().is_page_path_valid("test/:", {}) is True
    assert (
        PageHandler().is_page_path_valid(
            "test/::id", [{"name": "id", "param_type": "text"}]
        )
        is True
    )
    assert (
        PageHandler().is_page_path_valid(
            "product/:id-:slug",
            [
                {"name": "id", "param_type": "text"},
                {"name": "slug", "param_type": "text"},
            ],
        )
        is True
    )
    assert (
        PageHandler().is_page_path_valid(
            "product/:test/:test", [{"name": "test", "param_type": "text"}]
        )
        is False
    )


def test_is_page_path_valid_raises():
    with pytest.raises(PathParamNotInPath):
        PageHandler().is_page_path_valid(
            "test", [{"name": "id", "param_type": "text"}], raises=True
        )

    with pytest.raises(PathParamNotDefined):
        PageHandler().is_page_path_valid("test/:id", [], raises=True)


@pytest.mark.django_db
def test_find_unused_page_path(data_fixture):
    page = data_fixture.create_builder_page(path="/test")

    assert PageHandler().find_unused_page_path(page.builder, "/test") == "/test2"


@pytest.mark.django_db
def test_is_page_path_unique(data_fixture):
    builder = data_fixture.create_builder_application()

    data_fixture.create_builder_page(builder=builder, path="/test/:id")

    assert PageHandler().is_page_path_unique(builder, "/new") is True
    assert PageHandler().is_page_path_unique(builder, "/test/:id") is False
    assert PageHandler().is_page_path_unique(builder, "/test/:id/:hello") is True
    assert PageHandler().is_page_path_unique(builder, "/test/:id-:hello") is True


@pytest.mark.django_db
def test_is_page_path_unique_different_param_position(data_fixture):
    builder = data_fixture.create_builder_application()

    data_fixture.create_builder_page(builder=builder, path="/test/:id/hello/:new")

    assert PageHandler().is_page_path_unique(builder, "/test/:new/hello/:id") is False
    assert PageHandler().is_page_path_unique(builder, "/test/:new/:id/hello") is True


@pytest.mark.django_db
def test_is_page_path_unique_raises(data_fixture):
    builder = data_fixture.create_builder_application()

    data_fixture.create_builder_page(builder=builder, path="/test/:id")

    with pytest.raises(PagePathNotUnique):
        PageHandler().is_page_path_unique(builder, "/test/:id", raises=True)


def test_generalise_path():
    assert PageHandler().generalise_path("/test") == "/test"
    assert (
        PageHandler().generalise_path("/test/:id")
        == f"/test/{ILLEGAL_PATH_SAMPLE_CHARACTER}"
    )
    assert (
        PageHandler().generalise_path("/test/:id/hello/:test")
        == f"/test/{ILLEGAL_PATH_SAMPLE_CHARACTER}/hello/{ILLEGAL_PATH_SAMPLE_CHARACTER}"
    )
    assert (
        PageHandler().generalise_path("/test/:id-:hello")
        == f"/test/{ILLEGAL_PATH_SAMPLE_CHARACTER}-{ILLEGAL_PATH_SAMPLE_CHARACTER}"
    )
