import pytest
from pyinstrument import Profiler

from baserow.contrib.database.views.usage_types import FormViewGroupStorageUsageItem
from baserow.core.trash.handler import TrashHandler


@pytest.mark.django_db
def test_form_view_group_storage_usage_item(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)

    usage = FormViewGroupStorageUsageItem().calculate_storage_usage(group.id)

    assert usage == 0

    cover_image = data_fixture.create_user_file(is_image=True, size=200)
    logo_image = data_fixture.create_user_file(is_image=True, size=400)

    data_fixture.create_form_view(
        table=table,
        cover_image=cover_image,
        logo_image=logo_image,
    )

    usage = FormViewGroupStorageUsageItem().calculate_storage_usage(group.id)

    assert usage == 600


@pytest.mark.django_db
def test_form_view_group_storage_usage_item_trashed_database(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    cover_image = data_fixture.create_user_file(is_image=True, size=200)
    logo_image = data_fixture.create_user_file(is_image=True, size=400)

    data_fixture.create_form_view(
        table=table,
        cover_image=cover_image,
        logo_image=logo_image,
    )

    usage = FormViewGroupStorageUsageItem().calculate_storage_usage(group.id)

    assert usage == 600

    TrashHandler().trash(user, group, database, database)
    usage = FormViewGroupStorageUsageItem().calculate_storage_usage(group.id)
    assert usage == 0


@pytest.mark.django_db
def test_form_view_group_storage_usage_item_trashed_table(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    cover_image = data_fixture.create_user_file(is_image=True, size=200)
    logo_image = data_fixture.create_user_file(is_image=True, size=400)

    data_fixture.create_form_view(
        table=table,
        cover_image=cover_image,
        logo_image=logo_image,
    )

    usage = FormViewGroupStorageUsageItem().calculate_storage_usage(group.id)

    assert usage == 600

    TrashHandler().trash(user, group, database, table)
    usage = FormViewGroupStorageUsageItem().calculate_storage_usage(group.id)
    assert usage == 0


@pytest.mark.django_db
def test_form_view_group_storage_usage_item_duplicate_ids(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)

    image = data_fixture.create_user_file(is_image=True, size=200)

    data_fixture.create_form_view(
        table=table,
        cover_image=image,
        logo_image=image,
    )

    usage = FormViewGroupStorageUsageItem().calculate_storage_usage(group.id)

    assert usage == 200  # Instead of 400


@pytest.mark.django_db
def test_form_view_group_storage_usage_item_duplicate_ids_within_image_category(
    data_fixture,
):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)

    cover_image = data_fixture.create_user_file(is_image=True, size=200)
    logo_image = data_fixture.create_user_file(is_image=True, size=400)

    data_fixture.create_form_view(
        table=table,
        cover_image=cover_image,
        logo_image=logo_image,
    )

    data_fixture.create_form_view(
        table=table,
        cover_image=cover_image,
        logo_image=logo_image,
    )

    usage = FormViewGroupStorageUsageItem().calculate_storage_usage(group.id)

    assert usage == 600  # Instead of 1200


@pytest.mark.django_db
@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
def test_form_view_group_storage_usage_item_performance(data_fixture):
    form_views_amount = 1000

    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)

    for i in range(form_views_amount):
        cover_image = data_fixture.create_user_file(is_image=True, size=200)
        logo_image = data_fixture.create_user_file(is_image=True, size=400)

        data_fixture.create_form_view(
            table=table,
            cover_image=cover_image,
            logo_image=logo_image,
        )

    profiler = Profiler()
    profiler.start()
    usage = FormViewGroupStorageUsageItem().calculate_storage_usage(group.id)
    profiler.stop()

    print(profiler.output_text(unicode=True, color=True))

    assert usage == form_views_amount * 600
