from unittest.mock import patch

import pytest

from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.pages.service import PageService
from baserow.core.exceptions import UserNotInGroup


@patch("baserow.contrib.builder.pages.service.page_created")
@pytest.mark.django_db
def test_page_created_signal_sent(page_created_mock, data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)

    page = PageService().create_page(user, builder, "test")

    assert page_created_mock.called_with(page=page, user=user)


@pytest.mark.django_db
def test_create_page_user_not_in_group(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application()

    with pytest.raises(UserNotInGroup):
        PageService().create_page(user, builder, "test")


@patch("baserow.contrib.builder.pages.service.page_deleted")
@pytest.mark.django_db
def test_page_deleted_signal_sent(page_deleted_mock, data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    page = data_fixture.create_builder_page(builder=builder)

    PageService().delete_page(user, page)

    assert page_deleted_mock.called_with(builder=builder, page_id=page.id, user=user)


@pytest.mark.django_db(transaction=True)
def test_delete_page_user_not_in_group(data_fixture):
    user = data_fixture.create_user()
    user_unrelated = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)

    page = PageService().create_page(user, builder, "test")

    with pytest.raises(UserNotInGroup):
        PageService().delete_page(user_unrelated, page)

    assert Page.objects.count() == 1


@pytest.mark.django_db
def test_get_page_user_not_in_group(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application()
    page = data_fixture.create_builder_page(builder=builder)

    with pytest.raises(UserNotInGroup):
        PageService().get_page(user, page.id)


@patch("baserow.contrib.builder.pages.service.page_updated")
@pytest.mark.django_db
def test_page_updated_signal_sent(page_updated_mock, data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    page = data_fixture.create_builder_page(builder=builder)

    PageService().update_page(user, page, name="new")

    assert page_updated_mock.called_with(page=page, user=user)


@pytest.mark.django_db
def test_update_page_user_not_in_group(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application()
    page = data_fixture.create_builder_page(builder=builder)

    with pytest.raises(UserNotInGroup):
        PageService().update_page(user, page, name="test")


@pytest.mark.django_db
def test_update_page_invalid_values(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    page = data_fixture.create_builder_page(builder=builder)

    page_updated = PageService().update_page(user, page, nonsense="hello")

    assert hasattr(page_updated, "nonsense") is False


@patch("baserow.contrib.builder.pages.service.pages_reordered")
@pytest.mark.django_db
def test_pages_reordered_signal_sent(pages_reordered_mock, data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    page_one = data_fixture.create_builder_page(builder=builder, order=1)
    page_two = data_fixture.create_builder_page(builder=builder, order=2)

    full_order = PageService().order_pages(user, builder, [page_two.id, page_one.id])

    assert pages_reordered_mock.called_with(
        builder=builder, order=full_order, user=user
    )


@pytest.mark.django_db
def test_order_pages_user_not_in_group(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application()
    page_one = data_fixture.create_builder_page(builder=builder, order=1)
    page_two = data_fixture.create_builder_page(builder=builder, order=2)

    with pytest.raises(UserNotInGroup):
        PageService().order_pages(user, builder, [page_two.id, page_one.id])
