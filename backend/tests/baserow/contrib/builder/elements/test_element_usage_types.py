import pytest

from baserow.contrib.builder.elements.usage_types import (
    ImageElementWorkspaceStorageUsageItem,
)


@pytest.mark.django_db
def test_image_element_workspace_storage_usage_item(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    builder = data_fixture.create_builder_application(workspace=workspace)
    page = data_fixture.create_builder_page(builder=builder)

    usage = ImageElementWorkspaceStorageUsageItem().calculate_storage_usage(
        workspace.id
    )

    assert usage == 0

    image_file = data_fixture.create_user_file(is_image=True, size=200)

    data_fixture.create_builder_image_element(
        page=page,
        image_file=image_file,
    )

    usage = ImageElementWorkspaceStorageUsageItem().calculate_storage_usage(
        workspace.id
    )

    assert usage == 200


@pytest.mark.django_db
def test_image_element_workspace_storage_usage_item_trashed_builder(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    builder = data_fixture.create_builder_application(workspace=workspace)
    page = data_fixture.create_builder_page(builder=builder)
    image_file = data_fixture.create_user_file(is_image=True, size=200)

    data_fixture.create_builder_image_element(
        page=page,
        image_file=image_file,
    )

    usage = ImageElementWorkspaceStorageUsageItem().calculate_storage_usage(
        workspace.id
    )

    assert usage == 200

    builder.trashed = True
    builder.save()
    usage = ImageElementWorkspaceStorageUsageItem().calculate_storage_usage(
        workspace.id
    )
    assert usage == 0


@pytest.mark.django_db
def test_image_element_workspace_storage_usage_item_trashed_page(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    builder = data_fixture.create_builder_application(workspace=workspace)
    page = data_fixture.create_builder_page(builder=builder)
    image_file = data_fixture.create_user_file(is_image=True, size=200)

    data_fixture.create_builder_image_element(
        page=page,
        image_file=image_file,
    )

    usage = ImageElementWorkspaceStorageUsageItem().calculate_storage_usage(
        workspace.id
    )

    assert usage == 200

    page.trashed = True
    page.save()
    usage = ImageElementWorkspaceStorageUsageItem().calculate_storage_usage(
        workspace.id
    )
    assert usage == 0


@pytest.mark.django_db
def test_image_element_workspace_storage_usage_item_duplicate_ids(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    builder = data_fixture.create_builder_application(workspace=workspace)
    page = data_fixture.create_builder_page(builder=builder)
    image_file = data_fixture.create_user_file(is_image=True, size=200)

    data_fixture.create_builder_image_element(
        page=page,
        image_file=image_file,
    )

    usage = ImageElementWorkspaceStorageUsageItem().calculate_storage_usage(
        workspace.id
    )

    assert usage == 200

    data_fixture.create_builder_image_element(
        page=page,
        image_file=image_file,
    )

    usage = ImageElementWorkspaceStorageUsageItem().calculate_storage_usage(
        workspace.id
    )

    assert usage == 200
