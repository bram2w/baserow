import pytest

from baserow.contrib.builder.pages.exceptions import PageDoesNotExist, PageNotInBuilder
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

    # Without selecting related
    page = PageHandler().get_page(page.id)
    with django_assert_num_queries(2):
        group = page.builder.group

    # With selecting related
    base_queryset = Page.objects.select_related("builder", "builder__group")
    page = PageHandler().get_page(page.id, base_queryset=base_queryset)
    with django_assert_num_queries(0):
        group = page.builder.group


@pytest.mark.django_db
def test_create_page(data_fixture):
    builder = data_fixture.create_builder_application()
    expected_order = Page.get_last_order(builder)

    page = PageHandler().create_page(builder, "test")

    assert page.order == expected_order
    assert page.name == "test"


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
