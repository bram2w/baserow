import secrets
from io import BytesIO
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

import pytest

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import GalleryViewFieldOptions
from baserow.contrib.database.views.registries import (
    view_aggregation_type_registry,
    view_type_registry,
)
from baserow.contrib.database.views.view_ownership_types import (
    CollaborativeViewOwnershipType,
)
from baserow.core.models import GroupUser
from baserow.core.user_files.handler import UserFileHandler


@pytest.mark.django_db
def test_import_export_grid_view(data_fixture):
    grid_view = data_fixture.create_grid_view(
        name="Test",
        order=1,
        filter_type="AND",
        filters_disabled=False,
        row_identifier_type="count",
    )
    field = data_fixture.create_text_field(table=grid_view.table)
    imported_field = data_fixture.create_text_field(table=grid_view.table)
    field_option = data_fixture.create_grid_view_field_option(
        grid_view=grid_view,
        field=field,
        aggregation_type="whatever",
        aggregation_raw_type="empty",
    )
    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=field, value="test", type="equal"
    )
    view_sort = data_fixture.create_view_sort(view=grid_view, field=field, order="ASC")

    view_decoration = data_fixture.create_view_decoration(
        view=grid_view,
        value_provider_conf={"config": 12},
    )

    id_mapping = {"database_fields": {field.id: imported_field.id}}

    grid_view_type = view_type_registry.get("grid")
    serialized = grid_view_type.export_serialized(grid_view, None, None, None)
    imported_grid_view = grid_view_type.import_serialized(
        grid_view.table, serialized, id_mapping, None, None
    )

    assert grid_view.id != imported_grid_view.id
    assert grid_view.name == imported_grid_view.name
    assert grid_view.order == imported_grid_view.order
    assert grid_view.filter_type == imported_grid_view.filter_type
    assert grid_view.filters_disabled == imported_grid_view.filters_disabled
    assert grid_view.row_identifier_type == imported_grid_view.row_identifier_type
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

    imported_view_decoration = imported_grid_view.viewdecoration_set.all().first()
    assert view_decoration.id != imported_view_decoration.id
    assert view_decoration.type == imported_view_decoration.type
    assert (
        view_decoration.value_provider_type
        == imported_view_decoration.value_provider_type
    )
    assert (
        imported_view_decoration.value_provider_conf
        == imported_view_decoration.value_provider_conf
    )
    assert view_decoration.order == imported_view_decoration.order

    imported_field_options = imported_grid_view.get_field_options()
    imported_field_option = imported_field_options[0]
    assert field_option.id != imported_field_option.id
    assert imported_field.id == imported_field_option.field_id
    assert field_option.width == imported_field_option.width
    assert field_option.hidden == imported_field_option.hidden
    assert field_option.order == imported_field_option.order
    assert field_option.aggregation_type == imported_field_option.aggregation_type
    assert (
        field_option.aggregation_raw_type == imported_field_option.aggregation_raw_type
    )


@pytest.mark.django_db
def test_grid_view_field_type_change(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field1 = data_fixture.create_text_field(table=table)
    field2 = data_fixture.create_text_field(table=table)
    grid_view = data_fixture.create_grid_view(table=table, create_options=False)

    field_option1 = data_fixture.create_grid_view_field_option(
        grid_view=grid_view,
        field=field1,
        aggregation_type="whatever",
        aggregation_raw_type="empty_count",
    )

    field_option2 = data_fixture.create_grid_view_field_option(
        grid_view=grid_view,
        field=field2,
        aggregation_type="",
        aggregation_raw_type="",
    )

    field_handler = FieldHandler()

    options = grid_view.get_field_options()
    assert options[0].aggregation_raw_type == "empty_count"

    # Force field incompatibility for the test
    empty_count = view_aggregation_type_registry.get("empty_count")
    empty_count.field_is_compatible = lambda _: False

    field_handler.update_field(
        user=user,
        field=field1,
        new_type_name="boolean",
    )

    # We also test a field with field option but without aggregation_raw_type
    field_handler.update_field(
        user=user,
        field=field2,
        new_type_name="boolean",
    )

    empty_count.field_is_compatible = lambda _: True

    options = grid_view.get_field_options()
    assert options[0].aggregation_raw_type == ""


@pytest.mark.django_db
def test_import_export_gallery_view(data_fixture, tmpdir):
    user = data_fixture.create_user()

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)
    gallery_view = data_fixture.create_gallery_view(
        table=table, card_cover_image_field=file_field
    )
    text_field = data_fixture.create_text_field(table=table)
    field_option = data_fixture.create_gallery_view_field_option(
        gallery_view, text_field, order=1
    )

    files_buffer = BytesIO()
    gallery_view_type = view_type_registry.get("gallery")

    with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
        serialized = gallery_view_type.export_serialized(
            gallery_view, None, files_zip=files_zip, storage=storage
        )

    assert serialized["id"] == gallery_view.id
    assert serialized["type"] == "gallery"
    assert serialized["name"] == gallery_view.name
    assert serialized["order"] == 0
    assert serialized["card_cover_image_field_id"] == file_field.id
    assert len(serialized["field_options"]) == 2
    assert serialized["field_options"][0]["id"] == field_option.id
    assert serialized["field_options"][0]["field_id"] == field_option.field_id
    assert serialized["field_options"][0]["hidden"] is True
    assert serialized["field_options"][0]["order"] == 1

    imported_single_select_field = data_fixture.create_text_field(table=table)
    imported_file_field = data_fixture.create_file_field(table=table)
    id_mapping = {
        "database_fields": {
            text_field.id: imported_single_select_field.id,
            file_field.id: imported_file_field.id,
        }
    }

    with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
        imported_gallery_view = gallery_view_type.import_serialized(
            gallery_view.table, serialized, id_mapping, files_zip, storage
        )

    assert gallery_view.id != imported_gallery_view.id
    assert gallery_view.name == imported_gallery_view.name
    assert gallery_view.order == imported_gallery_view.order
    assert imported_gallery_view.card_cover_image_field.id == imported_file_field.id
    imported_field_options = imported_gallery_view.get_field_options()
    assert len(imported_field_options) == 2
    imported_field_option = imported_field_options[0]
    assert field_option.id != imported_field_option.id
    assert field_option.hidden == imported_field_option.hidden
    assert field_option.order == imported_field_option.order


@pytest.mark.django_db
def test_newly_created_gallery_view(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table, primary=True)
    data_fixture.create_text_field(table=table)
    data_fixture.create_text_field(table=table)
    data_fixture.create_text_field(table=table)

    handler = ViewHandler()
    handler.create_view(user, table=table, type_name="gallery")

    all_field_options = (
        GalleryViewFieldOptions.objects.all()
        .order_by("field_id")
        .values_list("hidden", flat=True)
    )
    assert list(all_field_options) == [False, False, False, True]


@pytest.mark.django_db
def test_convert_card_cover_image_field_to_another(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)
    gallery_view = data_fixture.create_gallery_view(
        table=table, card_cover_image_field=file_field
    )
    FieldHandler().update_field(user=user, field=file_field, new_type_name="text")
    gallery_view.refresh_from_db()
    assert gallery_view.card_cover_image_field_id is None


@pytest.mark.django_db
def test_convert_card_cover_image_field_deleted(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table)
    gallery_view = data_fixture.create_gallery_view(
        table=table, card_cover_image_field=file_field
    )
    FieldHandler().delete_field(user=user, field=file_field)
    gallery_view.refresh_from_db()
    assert gallery_view.card_cover_image_field_id is None


@pytest.mark.django_db
def test_convert_to_incompatible_field_in_form_view(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table)
    field_2 = data_fixture.create_text_field(table=table)
    form_view = data_fixture.create_form_view(table=table)
    options = data_fixture.create_form_view_field_option(form_view, field, enabled=True)
    options_2 = data_fixture.create_form_view_field_option(
        form_view, field_2, enabled=True
    )

    FieldHandler().update_field(
        user=user,
        table=table,
        field=field,
        new_type_name="created_on",
    )
    options.refresh_from_db()
    options_2.refresh_from_db()
    assert options.enabled is False
    assert options_2.enabled is True


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
        submit_text="My Submit",
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
    condition = data_fixture.create_form_view_field_options_condition(
        field_option=field_option, field=text_field
    )
    condition_2 = data_fixture.create_form_view_field_options_condition(
        field_option=field_option,
        field=text_field,
        type="multiple_select_has",
        value="1",
    )

    files_buffer = BytesIO()
    form_view_type = view_type_registry.get("form")

    with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
        serialized = form_view_type.export_serialized(
            form_view, None, files_zip=files_zip, storage=storage
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
    assert serialized["submit_text"] == form_view.submit_text
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
    assert serialized["field_options"][0]["conditions"] == [
        {
            "id": condition.id,
            "field": condition.field_id,
            "type": condition.type,
            "value": condition.value,
        },
        {
            "id": condition_2.id,
            "field": condition_2.field_id,
            "type": condition_2.type,
            "value": condition_2.value,
        },
    ]

    with ZipFile(files_buffer, "r", ZIP_DEFLATED, False) as zip_file:
        assert zip_file.read(user_file.name) == b"Hello World"
        assert len(zip_file.infolist()) == 1

    id_mapping = {
        "database_fields": {text_field.id: imported_text_field.id},
        "database_field_select_options": {1: 2},
    }

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
    assert form_view.submit_text == imported_form_view.submit_text
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

    imported_field_option_conditions = imported_field_option.conditions.all()
    assert len(imported_field_option_conditions) == 2
    imported_field_option_condition = imported_field_option_conditions[0]
    assert imported_field_option_condition.field_id == imported_text_field.id
    assert imported_field_option_condition.field_option_id == imported_field_option.id
    assert imported_field_option_condition.type == condition.type
    assert imported_field_option_condition.value == condition.value
    imported_field_option_condition_2 = imported_field_option_conditions[1]
    assert imported_field_option_condition_2.field_id == imported_text_field.id
    assert imported_field_option_condition_2.field_option_id == imported_field_option.id
    assert imported_field_option_condition_2.type == condition_2.type
    assert imported_field_option_condition_2.value == "2"


@pytest.mark.django_db
def test_import_export_view_ownership_type(data_fixture):
    group = data_fixture.create_group()
    user = data_fixture.create_user(group=group)
    user2 = data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    grid_view = data_fixture.create_grid_view(
        table=table,
        name="Test",
        order=1,
        filter_type="AND",
        filters_disabled=False,
        row_identifier_type="count",
    )
    grid_view.ownership_type = "personal"
    grid_view.created_by = user2
    grid_view.save()
    grid_view_type = view_type_registry.get("grid")

    serialized = grid_view_type.export_serialized(grid_view, None, None)
    imported_grid_view = grid_view_type.import_serialized(
        grid_view.table, serialized, {}, None, None
    )

    assert grid_view.id != imported_grid_view.id
    assert grid_view.ownership_type == imported_grid_view.ownership_type
    assert grid_view.created_by == imported_grid_view.created_by

    # view should not be imported if the user is gone

    GroupUser.objects.filter(user=user2).delete()

    imported_grid_view = grid_view_type.import_serialized(
        grid_view.table, serialized, {}, None, None
    )

    assert imported_grid_view is None

    # created by is not set
    grid_view.created_by = None
    grid_view.ownership_type = "collaborative"
    grid_view.save()

    serialized = grid_view_type.export_serialized(grid_view, None, None)
    imported_grid_view = grid_view_type.import_serialized(
        grid_view.table, serialized, {}, None, None
    )

    assert grid_view.id != imported_grid_view.id
    assert imported_grid_view.ownership_type == "collaborative"
    assert imported_grid_view.created_by is None


@pytest.mark.django_db
def test_import_export_view_ownership_type_not_in_registry(data_fixture):
    ownership_types = {"collaborative": CollaborativeViewOwnershipType()}
    group = data_fixture.create_group()
    user = data_fixture.create_user(group=group)
    user2 = data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    grid_view = data_fixture.create_grid_view(
        table=table,
        name="Test",
        order=1,
        filter_type="AND",
        filters_disabled=False,
        row_identifier_type="count",
    )
    grid_view.ownership_type = "personal"
    grid_view.created_by = user2
    grid_view.save()
    grid_view_type = view_type_registry.get("grid")
    serialized = grid_view_type.export_serialized(grid_view, None, None)

    with patch(
        "baserow.contrib.database.views.registries.view_ownership_type_registry.registry",
        ownership_types,
    ):
        imported_grid_view = grid_view_type.import_serialized(
            grid_view.table, serialized, {}, None, None
        )

        assert imported_grid_view is None
