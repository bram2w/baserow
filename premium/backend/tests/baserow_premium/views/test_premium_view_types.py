import pytest
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.files.storage import FileSystemStorage

from baserow.contrib.database.views.registries import view_type_registry
from baserow.contrib.database.views.handler import ViewHandler

from baserow.contrib.database.fields.handler import FieldHandler

from baserow_premium.views.exceptions import KanbanViewFieldDoesNotBelongToSameTable
from baserow_premium.views.models import KanbanViewFieldOptions


@pytest.mark.django_db
def test_field_of_same_table_is_provided(premium_data_fixture):
    user = premium_data_fixture.create_user()
    table = premium_data_fixture.create_database_table(user=user)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    single_select_field_2 = premium_data_fixture.create_single_select_field()

    view_handler = ViewHandler()

    with pytest.raises(KanbanViewFieldDoesNotBelongToSameTable):
        view_handler.create_view(
            user=user,
            table=table,
            type_name="kanban",
            single_select_field=single_select_field_2,
        )

    with pytest.raises(KanbanViewFieldDoesNotBelongToSameTable):
        view_handler.create_view(
            user=user,
            table=table,
            type_name="kanban",
            single_select_field=single_select_field_2.id,
        )

    kanban_view = view_handler.create_view(
        user=user,
        table=table,
        type_name="kanban",
        single_select_field=single_select_field,
    )

    with pytest.raises(KanbanViewFieldDoesNotBelongToSameTable):
        view_handler.update_view(
            user=user,
            view=kanban_view,
            single_select_field=single_select_field_2,
        )

    with pytest.raises(KanbanViewFieldDoesNotBelongToSameTable):
        view_handler.update_view(
            user=user,
            view=kanban_view,
            single_select_field=single_select_field_2.id,
        )

    view_handler.update_view(
        user=user,
        view=kanban_view,
        single_select_field=None,
    )


@pytest.mark.django_db
def test_import_export_kanban_view(premium_data_fixture, tmpdir):
    user = premium_data_fixture.create_user()

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    table = premium_data_fixture.create_database_table(user=user)
    file_field = premium_data_fixture.create_file_field(table=table)
    kanban_view = premium_data_fixture.create_kanban_view(
        table=table, single_select_field=None, card_cover_image_field=file_field
    )
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    field_option = premium_data_fixture.create_kanban_view_field_option(
        kanban_view=kanban_view, field=single_select_field, hidden=True, order=1
    )
    kanban_view.single_select_field = single_select_field
    kanban_view.save()

    files_buffer = BytesIO()
    kanban_field_type = view_type_registry.get("kanban")

    with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
        serialized = kanban_field_type.export_serialized(
            kanban_view, files_zip=files_zip, storage=storage
        )

    assert serialized["id"] == kanban_view.id
    assert serialized["type"] == "kanban"
    assert serialized["name"] == kanban_view.name
    assert serialized["order"] == 0
    assert serialized["single_select_field_id"] == single_select_field.id
    assert serialized["card_cover_image_field_id"] == file_field.id
    assert len(serialized["field_options"]) == 2
    assert serialized["field_options"][0]["id"] == field_option.id
    assert serialized["field_options"][0]["field_id"] == field_option.field_id
    assert serialized["field_options"][0]["hidden"] is True
    assert serialized["field_options"][0]["order"] == 1

    imported_single_select_field = premium_data_fixture.create_single_select_field(
        table=table
    )
    imported_file_field = premium_data_fixture.create_file_field(table=table)

    id_mapping = {
        "database_fields": {
            single_select_field.id: imported_single_select_field.id,
            file_field.id: imported_file_field.id,
        }
    }

    with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
        imported_kanban_view = kanban_field_type.import_serialized(
            kanban_view.table, serialized, id_mapping, files_zip, storage
        )

    assert kanban_view.id != imported_kanban_view.id
    assert kanban_view.name == imported_kanban_view.name
    assert kanban_view.order == imported_kanban_view.order
    assert (
        kanban_view.single_select_field_id != imported_kanban_view.single_select_field
    )
    assert (
        kanban_view.card_cover_image_field_id
        != imported_kanban_view.card_cover_image_field_id
    )
    assert imported_kanban_view.card_cover_image_field_id == imported_file_field.id

    imported_field_options = imported_kanban_view.get_field_options()
    assert len(imported_field_options) == 2
    imported_field_option = imported_field_options[0]
    assert field_option.id != imported_field_option.id
    assert imported_single_select_field.id == imported_field_option.field_id
    assert field_option.hidden == imported_field_option.hidden
    assert field_option.order == imported_field_option.order


@pytest.mark.django_db
def test_newly_created_view(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    table = premium_data_fixture.create_database_table(user=user)
    premium_data_fixture.create_text_field(table=table, primary=True)
    premium_data_fixture.create_text_field(table=table)
    premium_data_fixture.create_text_field(table=table)
    premium_data_fixture.create_text_field(table=table)

    handler = ViewHandler()
    handler.create_view(user, table=table, type_name="kanban")

    all_field_options = (
        KanbanViewFieldOptions.objects.all()
        .order_by("field_id")
        .values_list("hidden", flat=True)
    )
    assert list(all_field_options) == [False, False, False, True]


@pytest.mark.django_db
def test_convert_card_cover_image_field_to_another(premium_data_fixture):
    user = premium_data_fixture.create_user()
    table = premium_data_fixture.create_database_table(user=user)
    file_field = premium_data_fixture.create_file_field(table=table)
    kanban_view = premium_data_fixture.create_kanban_view(
        table=table, card_cover_image_field=file_field
    )

    FieldHandler().update_field(user=user, field=file_field, new_type_name="text")
    kanban_view.refresh_from_db()
    assert kanban_view.card_cover_image_field_id is None


@pytest.mark.django_db
def test_convert_card_cover_image_field_deleted(premium_data_fixture):
    user = premium_data_fixture.create_user()
    table = premium_data_fixture.create_database_table(user=user)
    file_field = premium_data_fixture.create_file_field(table=table)
    kanban_view = premium_data_fixture.create_kanban_view(
        table=table, card_cover_image_field=file_field
    )

    FieldHandler().delete_field(user=user, field=file_field)

    kanban_view.refresh_from_db()
    assert kanban_view.card_cover_image_field_id is None
