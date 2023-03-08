import pytest
from baserow_premium.views.handler import get_rows_grouped_by_single_select_field

from baserow.contrib.database.views.exceptions import ViewDoesNotExist, ViewNotInTable
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import (
    OWNERSHIP_TYPE_COLLABORATIVE,
    GridView,
    View,
)
from baserow.core.exceptions import PermissionDenied


@pytest.mark.django_db
def test_get_rows_grouped_by_single_select_field(
    premium_data_fixture, django_assert_num_queries
):
    table = premium_data_fixture.create_database_table()
    view = View()
    view.table = table
    text_field = premium_data_fixture.create_text_field(table=table, primary=True)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    option_b = premium_data_fixture.create_select_option(
        field=single_select_field, value="B", color="red"
    )

    model = table.get_model()
    row_none1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row None 1",
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_none2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row None 2",
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_a1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row A1",
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_a2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row A2",
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_b1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row B1",
            f"field_{single_select_field.id}_id": option_b.id,
        }
    )
    row_b2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row B2",
            f"field_{single_select_field.id}_id": option_b.id,
        }
    )

    # The amount of queries including
    with django_assert_num_queries(4):
        rows = get_rows_grouped_by_single_select_field(
            view, single_select_field, model=model
        )

    assert len(rows) == 3
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 2
    assert rows["null"]["results"][0].id == row_none1.id
    assert rows["null"]["results"][1].id == row_none2.id

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 2
    assert rows[str(option_a.id)]["results"][0].id == row_a1.id
    assert rows[str(option_a.id)]["results"][1].id == row_a2.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 2
    assert rows[str(option_b.id)]["results"][0].id == row_b1.id
    assert rows[str(option_b.id)]["results"][1].id == row_b2.id

    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, default_limit=1
    )

    assert len(rows) == 3
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 1
    assert rows["null"]["results"][0].id == row_none1.id

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_a1.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 1
    assert rows[str(option_b.id)]["results"][0].id == row_b1.id

    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, default_limit=1, default_offset=1
    )

    assert len(rows) == 3
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 1
    assert rows["null"]["results"][0].id == row_none2.id

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_a2.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 1
    assert rows[str(option_b.id)]["results"][0].id == row_b2.id

    rows = get_rows_grouped_by_single_select_field(
        view,
        single_select_field,
        option_settings={"null": {"limit": 1, "offset": 1}},
    )

    assert len(rows) == 1
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 1
    assert rows["null"]["results"][0].id == row_none2.id

    rows = get_rows_grouped_by_single_select_field(
        view,
        single_select_field,
        option_settings={
            str(option_a.id): {"limit": 1, "offset": 0},
            str(option_b.id): {"limit": 1, "offset": 1},
        },
    )

    assert len(rows) == 2

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_a1.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 1
    assert rows[str(option_b.id)]["results"][0].id == row_b2.id

    rows = get_rows_grouped_by_single_select_field(
        view,
        single_select_field,
        option_settings={
            str(option_a.id): {"limit": 10, "offset": 10},
        },
    )

    assert len(rows) == 1
    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 0


@pytest.mark.django_db
def test_get_rows_grouped_by_single_select_field_not_existing_options_are_null(
    premium_data_fixture,
):
    table = premium_data_fixture.create_database_table()
    view = View()
    view.table = table
    text_field = premium_data_fixture.create_text_field(table=table, primary=True)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    option_b = premium_data_fixture.create_select_option(
        field=single_select_field, value="B", color="red"
    )

    model = table.get_model()
    row_1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row 1",
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row 2",
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row 3",
            f"field_{single_select_field.id}_id": option_b.id,
        }
    )

    option_b.delete()
    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, model=model
    )

    assert len(rows) == 2
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 2
    assert rows["null"]["results"][0].id == row_1.id
    assert rows["null"]["results"][1].id == row_3.id
    assert rows[str(option_a.id)]["count"] == 1
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_2.id

    option_a.delete()
    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, model=model
    )

    assert len(rows) == 1
    assert rows["null"]["count"] == 3
    assert len(rows["null"]["results"]) == 3
    assert rows["null"]["results"][0].id == row_1.id
    assert rows["null"]["results"][1].id == row_2.id
    assert rows["null"]["results"][2].id == row_3.id


@pytest.mark.django_db
def test_get_rows_grouped_by_single_select_field_with_empty_table(
    premium_data_fixture,
):
    table = premium_data_fixture.create_database_table()
    view = View()
    view.table = table
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    rows = get_rows_grouped_by_single_select_field(view, single_select_field)
    assert len(rows) == 1
    assert rows["null"]["count"] == 0
    assert len(rows["null"]["results"]) == 0


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_list_views_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)
    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type=OWNERSHIP_TYPE_COLLABORATIVE,
    )
    view2 = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    user_views = handler.list_views(user, table, "grid", None, None, None, 10)
    assert len(user_views) == 2

    user2_views = handler.list_views(user2, table, "grid", None, None, None, 10)
    assert len(user2_views) == 1
    assert user2_views[0].id == view.id


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_get_view_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    handler.get_view_as_user(user, view.id)

    with pytest.raises(PermissionDenied):
        handler.get_view_as_user(user2, view.id)


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_create_view_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)

    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    grid = GridView.objects.all().first()
    assert grid.created_by == user
    assert grid.ownership_type == "personal"


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_update_view_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)

    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    handler.update_view(user=user, view=view, name="Renamed")
    view.refresh_from_db()
    assert view.name == "Renamed"

    with pytest.raises(PermissionDenied):
        handler.update_view(user=user2, view=view, name="Not my view")


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_duplicate_view_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)

    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    duplicated_view = handler.duplicate_view(user, view)
    assert duplicated_view.ownership_type == "personal"
    assert duplicated_view.created_by == user

    with pytest.raises(PermissionDenied):
        handler.get_view_as_user(user2, duplicated_view.id)

    with pytest.raises(PermissionDenied):
        duplicated_view = handler.duplicate_view(user2, view)


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_delete_view_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)
    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    handler.delete_view(user, view)

    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    with pytest.raises(PermissionDenied):
        handler.delete_view(user2, view)


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_field_options_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)
    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    handler.get_field_options_as_user(user, view)

    with pytest.raises(PermissionDenied):
        handler.get_field_options_as_user(user2, view)

    handler.update_field_options(view, {}, user)

    with pytest.raises(PermissionDenied):
        handler.update_field_options(view, {}, user2)


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_filters_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)
    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )
    field = data_fixture.create_text_field(table=view.table)

    filter = handler.create_filter(user, view, field, "equal", "value")

    with pytest.raises(PermissionDenied):
        handler.create_filter(user2, view, field, "equal", "value")

    handler.get_filter(user, filter.id)

    with pytest.raises(PermissionDenied):
        handler.get_filter(user2, filter.id)

    list = handler.list_filters(user, view.id)
    assert len(list) == 1

    with pytest.raises(PermissionDenied):
        handler.list_filters(user2, view.id)

    handler.update_filter(user, filter, field, "equal", "another value")

    with pytest.raises(PermissionDenied):
        handler.update_filter(user2, filter, field, "equal", "another value")

    with pytest.raises(PermissionDenied):
        handler.delete_filter(user2, filter)

    handler.delete_filter(user, filter)


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_sorts_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)
    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )
    field = data_fixture.create_text_field(table=view.table)

    sort = handler.create_sort(user=user, view=view, field=field, order="ASC")

    with pytest.raises(PermissionDenied):
        handler.create_sort(user=user2, view=view, field=field, order="ASC")

    handler.get_sort(user, sort.id)

    with pytest.raises(PermissionDenied):
        handler.get_sort(user2, sort.id)

    list = handler.list_sorts(user, view.id)
    assert len(list) == 1

    with pytest.raises(PermissionDenied):
        handler.list_sorts(user2, view.id)

    handler.update_sort(user, sort, field)

    with pytest.raises(PermissionDenied):
        handler.update_sort(user2, sort, field)

    with pytest.raises(PermissionDenied):
        handler.delete_sort(user2, sort)

    handler.delete_sort(user, sort)


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_decorations_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)
    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )
    decorator_type_name = "left_border_color"
    value_provider_type_name = ""
    value_provider_conf = {}

    decoration = handler.create_decoration(
        view,
        decorator_type_name,
        value_provider_type_name,
        value_provider_conf,
        user=user,
    )

    with pytest.raises(PermissionDenied):
        handler.create_decoration(
            view,
            decorator_type_name,
            value_provider_type_name,
            value_provider_conf,
            user=user2,
        )

    result = handler.get_decoration(user, decoration.id)
    assert result == decoration

    with pytest.raises(PermissionDenied):
        handler.get_decoration(user2, decoration.id)

    list = handler.list_decorations(user, view.id)
    assert len(list) == 1

    with pytest.raises(PermissionDenied):
        handler.list_decorations(user2, view.id)

    handler.update_decoration(decoration, user)

    with pytest.raises(PermissionDenied):
        handler.update_decoration(decoration, user2)

    with pytest.raises(PermissionDenied):
        handler.delete_decoration(decoration, user2)

    handler.delete_decoration(decoration, user)


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_aggregations_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)
    field = data_fixture.create_number_field(user=user, table=table)
    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )
    handler.update_field_options(
        view=view,
        field_options={
            field.id: {
                "aggregation_type": "sum",
                "aggregation_raw_type": "sum",
            }
        },
    )
    aggr = [
        (
            field,
            "max",
        ),
    ]

    aggregations = handler.get_view_field_aggregations(user, view)
    assert field.db_column in aggregations

    handler.get_field_aggregations(user, view, aggr)

    with pytest.raises(PermissionDenied):
        handler.get_view_field_aggregations(user2, view)

    with pytest.raises(PermissionDenied):
        handler.get_field_aggregations(user2, view, aggr)


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_update_view_slug_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)
    view = handler.create_view(
        user=user,
        table=table,
        type_name="form",
        name="Form",
        ownership_type="personal",
    )

    handler.update_view_slug(user, view, "new-slug")
    view.refresh_from_db()
    assert view.slug == "new-slug"

    with pytest.raises(PermissionDenied):
        handler.update_view_slug(user2, view, "new-slug")


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_get_public_view_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)
    view = handler.create_view(
        user=user,
        table=table,
        type_name="form",
        name="Form",
        ownership_type="personal",
    )
    view.public = False
    view.slug = "slug"
    view.save()

    handler.get_public_view_by_slug(user, "slug")

    with pytest.raises(ViewDoesNotExist):
        handler.get_public_view_by_slug(user2, "slug")


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_order_views_personal_ownership_type(
    data_fixture, premium_data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    alternative_per_group_license_service.restrict_user_premium_to(user2, group.id)
    grid_1 = data_fixture.create_grid_view(
        table=table, user=user, created_by=user, order=1, ownership_type="collaborative"
    )
    grid_2 = data_fixture.create_grid_view(
        table=table, user=user, created_by=user, order=2, ownership_type="collaborative"
    )
    grid_3 = data_fixture.create_grid_view(
        table=table, user=user, created_by=user, order=3, ownership_type="collaborative"
    )
    personal_grid = data_fixture.create_grid_view(
        table=table, user=user, created_by=user, order=2, ownership_type="personal"
    )
    personal_grid_2 = data_fixture.create_grid_view(
        table=table, user=user, created_by=user, order=3, ownership_type="personal"
    )

    handler.order_views(
        user=user,
        table=table,
        order=[personal_grid_2.id, personal_grid.id],
    )

    grid_1.refresh_from_db()
    grid_2.refresh_from_db()
    grid_3.refresh_from_db()
    personal_grid.refresh_from_db()
    personal_grid_2.refresh_from_db()
    assert personal_grid_2.order == 1
    assert personal_grid.order == 2
    assert grid_1.order == 1
    assert grid_2.order == 2
    assert grid_3.order == 3

    with pytest.raises(ViewNotInTable):
        handler.order_views(
            user=user2,
            table=table,
            order=[personal_grid_2.id, personal_grid_2.id],
        )
