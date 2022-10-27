from django.test.utils import override_settings

import pytest
from baserow_premium.license.exceptions import FeaturesNotAvailableError

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import ViewDecoration
from baserow.contrib.database.views.registries import view_type_registry


@pytest.mark.django_db
def test_import_export_grid_view_w_decorator(data_fixture):
    grid_view = data_fixture.create_grid_view(
        name="Test", order=1, filter_type="AND", filters_disabled=False
    )
    field = data_fixture.create_text_field(table=grid_view.table)
    imported_field = data_fixture.create_text_field(table=grid_view.table)

    view_decoration = data_fixture.create_view_decoration(
        view=grid_view,
        type="left_border_color",
        value_provider_type="single_select_color",
        value_provider_conf={"field_id": field.id},
        order=1,
    )

    view_decoration_2 = data_fixture.create_view_decoration(
        view=grid_view,
        type="left_border_color",
        value_provider_type="conditional_color",
        value_provider_conf={
            "colors": [
                {"filters": [{"field": field.id}]},
                {"filters": [{"field": field.id}]},
            ]
        },
        order=2,
    )

    id_mapping = {"database_fields": {field.id: imported_field.id}}

    grid_view_type = view_type_registry.get("grid")
    serialized = grid_view_type.export_serialized(grid_view, None, None)
    imported_grid_view = grid_view_type.import_serialized(
        grid_view.table, serialized, id_mapping, None, None
    )

    imported_view_decorations = imported_grid_view.viewdecoration_set.all()
    assert view_decoration.id != imported_view_decorations[0].id
    assert view_decoration.type == imported_view_decorations[0].type
    assert (
        view_decoration.value_provider_type
        == imported_view_decorations[0].value_provider_type
    )
    assert imported_view_decorations[0].value_provider_conf == {
        "field_id": imported_field.id
    }

    assert view_decoration_2.id != imported_view_decorations[1].id
    assert view_decoration_2.type == imported_view_decorations[1].type
    assert (
        view_decoration_2.value_provider_type
        == imported_view_decorations[1].value_provider_type
    )
    assert imported_view_decorations[1].value_provider_conf == {
        "colors": [
            {"filters": [{"field": imported_field.id}]},
            {"filters": [{"field": imported_field.id}]},
        ]
    }


@pytest.mark.django_db
def test_field_type_changed_w_decoration(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    option_field = data_fixture.create_single_select_field(
        table=table, name="option_field", order=1
    )
    data_fixture.create_select_option(field=option_field, value="A", color="blue")

    grid_view = data_fixture.create_grid_view(table=table)

    select_view_decoration = data_fixture.create_view_decoration(
        view=grid_view,
        type="left_border_color",
        value_provider_type="single_select_color",
        value_provider_conf={"field_id": option_field.id},
        order=1,
    )

    condition_view_decoration = data_fixture.create_view_decoration(
        view=grid_view,
        type="left_border_color",
        value_provider_type="conditional_color",
        value_provider_conf={
            "colors": [
                {"filters": [{"field": text_field.id, "type": "equal"}]},
                {"filters": [{"field": option_field.id, "type": "equal"}]},
                {
                    "filters": [
                        {"field": option_field.id, "type": "single_select_equal"}
                    ]
                },
                {"filters": []},
            ]
        },
        order=2,
    )

    field_handler = FieldHandler()

    decorations = list(ViewDecoration.objects.all())
    assert len(decorations) == 2
    assert (
        decorations[0].value_provider_conf == select_view_decoration.value_provider_conf
    )
    assert (
        decorations[1].value_provider_conf
        == condition_view_decoration.value_provider_conf
    )

    field_handler.update_field(
        user=user, field=option_field, new_type_name="single_select"
    )

    decorations = list(ViewDecoration.objects.all())
    assert (
        decorations[0].value_provider_conf == select_view_decoration.value_provider_conf
    )
    assert (
        decorations[1].value_provider_conf
        == condition_view_decoration.value_provider_conf
    )

    field_handler.update_field(user=user, field=option_field, new_type_name="text")

    decorations = list(ViewDecoration.objects.all())
    assert decorations[0].value_provider_conf == {"field_id": None}
    assert decorations[1].value_provider_conf == {
        "colors": [
            {"filters": [{"type": "equal", "field": text_field.id}]},
            {"filters": [{"type": "equal", "field": option_field.id}]},
            {"filters": []},
            {"filters": []},
        ]
    }


@pytest.mark.django_db
def test_field_deleted_w_decoration(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    option_field = data_fixture.create_single_select_field(
        table=table, name="option_field", order=1
    )
    data_fixture.create_select_option(field=option_field, value="A", color="blue")

    grid_view = data_fixture.create_grid_view(table=table)

    data_fixture.create_view_decoration(
        view=grid_view,
        type="left_border_color",
        value_provider_type="single_select_color",
        value_provider_conf={"field_id": option_field.id},
        order=1,
    )

    data_fixture.create_view_decoration(
        view=grid_view,
        type="left_border_color",
        value_provider_type="conditional_color",
        value_provider_conf={
            "colors": [
                {"filters": [{"field": text_field.id, "type": "equal"}]},
                {"filters": [{"field": option_field.id, "type": "equal"}]},
                {
                    "filters": [
                        {"field": option_field.id, "type": "single_select_equal"}
                    ]
                },
                {"filters": []},
            ]
        },
        order=2,
    )

    field_handler = FieldHandler()

    field_handler.delete_field(user=user, field=option_field)

    decorations = list(ViewDecoration.objects.all())
    assert decorations[0].value_provider_conf == {"field_id": None}
    assert decorations[1].value_provider_conf == {
        "colors": [
            {"filters": [{"type": "equal", "field": text_field.id}]},
            {"filters": []},
            {"filters": []},
            {"filters": []},
        ]
    }

    field_handler.delete_field(user=user, field=text_field)

    decorations = list(ViewDecoration.objects.all())
    assert decorations[0].value_provider_conf == {"field_id": None}
    assert decorations[1].value_provider_conf == {
        "colors": [
            {"filters": []},
            {"filters": []},
            {"filters": []},
            {"filters": []},
        ]
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_single_select_color_with_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()
    decoration = handler.create_decoration(
        view=grid_view,
        decorator_type_name="left_border_color",
        value_provider_type_name="single_select_color",
        value_provider_conf={},
        user=user,
    )

    assert isinstance(decoration, ViewDecoration)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_single_select_color_without_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=False)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()

    with pytest.raises(FeaturesNotAvailableError):
        handler.create_decoration(
            view=grid_view,
            decorator_type_name="left_border_color",
            value_provider_type_name="single_select_color",
            value_provider_conf={"field": None},
            user=user,
        )

    decoration = handler.create_decoration(
        view=grid_view,
        decorator_type_name="left_border_color",
        value_provider_type_name="single_select_color",
        value_provider_conf={"field": None},
    )
    assert isinstance(decoration, ViewDecoration)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_single_select_color_without_premium_license_for_group(
    premium_data_fixture, alternative_per_group_license_service
):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()

    alternative_per_group_license_service.restrict_user_premium_to(
        user, [grid_view.table.database.group.id]
    )
    handler.create_decoration(
        view=grid_view,
        decorator_type_name="left_border_color",
        value_provider_type_name="single_select_color",
        value_provider_conf={"field": None},
        user=user,
    )

    alternative_per_group_license_service.restrict_user_premium_to(user, [0])
    with pytest.raises(FeaturesNotAvailableError):
        handler.create_decoration(
            view=grid_view,
            decorator_type_name="left_border_color",
            value_provider_type_name="single_select_color",
            value_provider_conf={"field": None},
            user=user,
        )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_conditional_color_with_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()
    decoration = handler.create_decoration(
        view=grid_view,
        decorator_type_name="left_border_color",
        value_provider_type_name="conditional_color",
        value_provider_conf={},
        user=user,
    )

    assert isinstance(decoration, ViewDecoration)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_conditional_color_without_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=False)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()

    with pytest.raises(FeaturesNotAvailableError):
        handler.create_decoration(
            view=grid_view,
            decorator_type_name="left_border_color",
            value_provider_type_name="conditional_color",
            value_provider_conf={},
            user=user,
        )

    decoration = handler.create_decoration(
        view=grid_view,
        decorator_type_name="background_color",
        value_provider_type_name="conditional_color",
        value_provider_conf={},
    )
    assert isinstance(decoration, ViewDecoration)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_conditional_color_without_premium_license_for_group(
    premium_data_fixture, alternative_per_group_license_service
):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()

    alternative_per_group_license_service.restrict_user_premium_to(
        user, [grid_view.table.database.group.id]
    )
    handler.create_decoration(
        view=grid_view,
        decorator_type_name="left_border_color",
        value_provider_type_name="conditional_color",
        value_provider_conf={"field": None},
        user=user,
    )

    alternative_per_group_license_service.restrict_user_premium_to(user, [0])
    with pytest.raises(FeaturesNotAvailableError):
        handler.create_decoration(
            view=grid_view,
            decorator_type_name="left_border_color",
            value_provider_type_name="conditional_color",
            value_provider_conf={"field": None},
            user=user,
        )
