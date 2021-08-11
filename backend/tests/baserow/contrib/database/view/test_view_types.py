import pytest
import secrets
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

from baserow.core.user_files.handler import UserFileHandler
from baserow.contrib.database.views.registries import view_type_registry


@pytest.mark.django_db
def test_import_export_grid_view(data_fixture):
    grid_view = data_fixture.create_grid_view(
        name="Test", order=1, filter_type="AND", filters_disabled=False
    )
    field = data_fixture.create_text_field(table=grid_view.table)
    imported_field = data_fixture.create_text_field(table=grid_view.table)
    field_option = data_fixture.create_grid_view_field_option(
        grid_view=grid_view, field=field
    )
    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=field, value="test", type="equal"
    )
    view_sort = data_fixture.create_view_sort(view=grid_view, field=field, order="ASC")

    id_mapping = {"database_fields": {field.id: imported_field.id}}

    grid_view_type = view_type_registry.get("grid")
    serialized = grid_view_type.export_serialized(grid_view, None, None)
    imported_grid_view = grid_view_type.import_serialized(
        grid_view.table, serialized, id_mapping, None, None
    )

    assert grid_view.id != imported_grid_view.id
    assert grid_view.name == imported_grid_view.name
    assert grid_view.order == imported_grid_view.order
    assert grid_view.filter_type == imported_grid_view.filter_type
    assert grid_view.filters_disabled == imported_grid_view.filters_disabled
    assert imported_grid_view.viewfilter_set.all().count() == 1
    assert imported_grid_view.viewsort_set.all().count() == 1

    imported_view_filter = imported_grid_view.viewfilter_set.all().first()
    assert view_filter.id != imported_view_filter.id
    assert imported_field.id == imported_view_filter.field_id
    assert view_filter.value == imported_view_filter.value
    assert view_filter.type == imported_view_filter.type

    imported_view_sort = imported_grid_view.viewsort_set.all().first()
    assert view_sort.id != imported_view_sort.id
    assert imported_field.id == imported_view_sort.field_id
    assert view_sort.order == imported_view_sort.order

    imported_field_options = imported_grid_view.get_field_options()
    imported_field_option = imported_field_options[0]
    assert field_option.id != imported_field_option.id
    assert imported_field.id == imported_field_option.field_id
    assert field_option.width == imported_field_option.width
    assert field_option.hidden == imported_field_option.hidden
    assert field_option.order == imported_field_option.order


@pytest.mark.django_db
def test_import_export_form_view(data_fixture, tmpdir):
    user = data_fixture.create_user()

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    handler = UserFileHandler()
    user_file = handler.upload_user_file(
        user, "test.jpg", ContentFile(b"Hello World"), storage=storage
    )

    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(
        table=table,
        slug="public-test-slug",
        public=True,
        title="Title",
        description="Description",
        cover_image=user_file,
        logo_image=user_file,
        submit_action="REDIRECT",
        submit_action_message="TEst message",
        submit_action_redirect_url="https://localhost",
    )
    text_field = data_fixture.create_text_field(table=table)
    imported_text_field = data_fixture.create_text_field(table=form_view.table)
    field_option = data_fixture.create_form_view_field_option(
        form_view,
        text_field,
        required=True,
        enabled=True,
        name="Test name",
        description="Field description",
        order=1,
    )

    files_buffer = BytesIO()
    form_view_type = view_type_registry.get("form")

    with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
        serialized = form_view_type.export_serialized(
            form_view, files_zip=files_zip, storage=storage
        )

    assert serialized["id"] == form_view.id
    assert serialized["type"] == "form"
    assert serialized["name"] == form_view.name
    assert serialized["order"] == 0
    assert "slug" not in serialized
    assert serialized["public"] == form_view.public
    assert serialized["title"] == form_view.title
    assert serialized["cover_image"] == {
        "name": form_view.cover_image.name,
        "original_name": form_view.cover_image.original_name,
    }
    assert serialized["logo_image"] == {
        "name": form_view.logo_image.name,
        "original_name": form_view.logo_image.original_name,
    }
    assert serialized["submit_action"] == form_view.submit_action
    assert serialized["submit_action_message"] == form_view.submit_action_message
    assert (
        serialized["submit_action_redirect_url"] == form_view.submit_action_redirect_url
    )
    assert len(serialized["field_options"]) == 1
    assert serialized["field_options"][0]["id"] == field_option.id
    assert serialized["field_options"][0]["field_id"] == field_option.field_id
    assert serialized["field_options"][0]["name"] == field_option.name
    assert serialized["field_options"][0]["description"] == field_option.description
    assert serialized["field_options"][0]["enabled"] == field_option.enabled
    assert serialized["field_options"][0]["required"] == field_option.required

    with ZipFile(files_buffer, "r", ZIP_DEFLATED, False) as zip_file:
        assert zip_file.read(user_file.name) == b"Hello World"
        assert len(zip_file.infolist()) == 1

    id_mapping = {"database_fields": {text_field.id: imported_text_field.id}}

    with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
        imported_form_view = form_view_type.import_serialized(
            form_view.table, serialized, id_mapping, files_zip, storage
        )

    assert form_view.id != imported_form_view.id
    assert form_view.name == imported_form_view.name
    assert form_view.order == imported_form_view.order
    assert form_view.slug != imported_form_view.slug
    assert len(secrets.token_urlsafe()) == len(imported_form_view.slug)
    assert form_view.public == imported_form_view.public
    assert form_view.title == imported_form_view.title
    assert form_view.description == imported_form_view.description
    assert form_view.cover_image_id == imported_form_view.cover_image_id
    assert form_view.logo_image_id == imported_form_view.logo_image_id
    assert form_view.submit_action == imported_form_view.submit_action
    assert form_view.submit_action_message == imported_form_view.submit_action_message
    assert (
        form_view.submit_action_redirect_url
        == imported_form_view.submit_action_redirect_url
    )

    imported_field_options = imported_form_view.get_field_options()
    assert len(imported_field_options) == 1
    imported_field_option = imported_field_options[0]
    assert field_option.id != imported_field_option.id
    assert imported_text_field.id == imported_field_option.field_id
    assert field_option.name == imported_field_option.name
    assert field_option.description == imported_field_option.description
    assert field_option.enabled == imported_field_option.enabled
    assert field_option.required == imported_field_option.required
    assert field_option.order == imported_field_option.order
