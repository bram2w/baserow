import secrets
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS

# noinspection PyPep8Naming
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

# noinspection PyPep8Naming


@pytest.mark.django_db
def test_forwards_migration(data_fixture, transactional_db):
    migrate_from = [("database", "0052_table_order_and_id_index")]
    migrate_to = [("database", "0053_add_and_move_public_flags")]

    old_state = migrate(migrate_from)

    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    FormView = old_state.apps.get_model("database", "FormView")
    GridView = old_state.apps.get_model("database", "GridView")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    form_content_type_id = ContentType.objects.get_for_model(FormView).id
    grid_content_type_id = ContentType.objects.get_for_model(GridView).id
    form_view = FormView.objects.create(
        table_id=table.id,
        name="a",
        order=1,
        public=True,
        slug="slug",
        content_type_id=form_content_type_id,
    )
    form_view2 = FormView.objects.create(
        table_id=table.id,
        name="b",
        order=1,
        public=False,
        slug="slug2",
        content_type_id=form_content_type_id,
    )
    grid_view = GridView.objects.create(
        table_id=table.id,
        name="c",
        order=1,
        content_type_id=grid_content_type_id,
    )
    grid_view2 = GridView.objects.create(
        table_id=table.id,
        name="d",
        order=2,
        content_type_id=grid_content_type_id,
    )
    new_state = migrate(migrate_to)
    NewFormView = new_state.apps.get_model("database", "FormView")
    NewGridView = new_state.apps.get_model("database", "GridView")

    new_form_view = NewFormView.objects.get(id=form_view.id)
    assert new_form_view.view_ptr.public
    assert new_form_view.view_ptr.slug == form_view.slug

    new_form_view2 = NewFormView.objects.get(id=form_view2.id)
    assert not new_form_view2.view_ptr.public
    assert new_form_view2.view_ptr.slug == form_view2.slug

    new_grid_view = NewGridView.objects.get(id=grid_view.id)
    assert not new_grid_view.view_ptr.public
    assert new_grid_view.view_ptr.slug is not None
    assert len(new_grid_view.view_ptr.slug) == len(secrets.token_urlsafe())

    new_grid_view2 = NewGridView.objects.get(id=grid_view2.id)
    assert not new_grid_view2.view_ptr.public
    assert new_grid_view2.view_ptr.slug is not None
    assert len(new_grid_view2.view_ptr.slug) == len(secrets.token_urlsafe())
    assert new_grid_view.view_ptr.slug != new_grid_view2.view_ptr.slug

    # We need to apply the latest migration otherwise other tests might fail.
    call_command("migrate", verbosity=0, database=DEFAULT_DB_ALIAS)


@pytest.mark.django_db
@patch(
    "baserow.contrib.database.migrations.0053_add_and_move_public_flags"
    ".update_batch_size"
)
def test_multi_batch_forwards_migration(
    patched_update_size, data_fixture, transactional_db
):
    migrate_from = [("database", "0052_table_order_and_id_index")]
    migrate_to = [("database", "0053_add_and_move_public_flags")]

    old_state = migrate(migrate_from)

    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    GridView = old_state.apps.get_model("database", "GridView")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    grid_content_type_id = ContentType.objects.get_for_model(GridView).id
    size = 3
    patched_update_size.return_value = size
    views_to_make = size * 2 + int(size / 2)
    for i in range(views_to_make):
        GridView.objects.create(
            table_id=table.id,
            name=str(i),
            order=1,
            content_type_id=grid_content_type_id,
        )
    new_state = migrate(migrate_to)
    NewGridView = new_state.apps.get_model("database", "GridView")

    assert not NewGridView.objects.filter(slug__isnull=True).exists()
    assert not NewGridView.objects.filter(public=True).exists()
    # We need to apply the latest migration otherwise other tests might fail.
    call_command("migrate", verbosity=0, database=DEFAULT_DB_ALIAS)


@pytest.mark.django_db
def test_backwards_migration(data_fixture, transactional_db):
    migrate_from = [("database", "0053_add_and_move_public_flags")]
    migrate_to = [("database", "0052_table_order_and_id_index")]

    old_state = migrate(migrate_from)

    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    FormView = old_state.apps.get_model("database", "FormView")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    content_type_id = ContentType.objects.get_for_model(FormView).id
    form_view = FormView.objects.create(
        table_id=table.id,
        name="a",
        order=1,
        public=True,
        slug="slug",
        content_type_id=content_type_id,
    )
    form_view2 = FormView.objects.create(
        table_id=table.id,
        name="b",
        order=2,
        public=False,
        slug="slug2",
        content_type_id=content_type_id,
    )
    new_state = migrate(migrate_to)
    NewFormView = new_state.apps.get_model("database", "FormView")
    new_form_view = NewFormView.objects.get(id=form_view.id)
    new_form_view2 = NewFormView.objects.get(id=form_view2.id)
    assert new_form_view.public
    assert new_form_view.slug == form_view.slug
    assert not new_form_view2.public
    assert new_form_view2.slug == form_view2.slug

    # We need to apply the latest migration otherwise other tests might fail.
    call_command("migrate", verbosity=0, database=DEFAULT_DB_ALIAS)


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()  # reload.
    executor.migrate(target)
    new_state = executor.loader.project_state(target)
    return new_state
