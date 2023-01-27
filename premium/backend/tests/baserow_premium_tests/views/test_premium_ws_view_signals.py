from unittest.mock import patch

import pytest

from baserow.contrib.database.views.handler import ViewHandler


@pytest.mark.django_db(transaction=True)
def test_view_signals_not_collaborative(
    data_fixture, alternative_per_group_license_service
):
    group = data_fixture.create_group(name="Group 1")
    user = data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    alternative_per_group_license_service.restrict_user_premium_to(user, group.id)
    field = data_fixture.create_text_field(table=table)
    field2 = data_fixture.create_text_field(table=table)
    view = data_fixture.create_grid_view(user=user, table=table)
    view.ownership_type = "personal"
    view.created_by = user
    view.save()

    # view_created

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().create_view(
            user=user,
            table=table,
            type_name="grid",
            name="Grid",
            ownership_type="personal",
        )
        broadcast.delay.assert_not_called()

    with patch(
        "baserow.contrib.database.ws.views.signals.broadcast_to_users"
    ) as broadcast:
        ViewHandler().create_view(
            user=user,
            table=table,
            type_name="grid",
            name="Grid",
            ownership_type="personal",
        )
        args = broadcast.delay.call_args
        assert args[0][0] == [user.id]

    # view_updated

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().update_view(user=user, view=view, name="View")
        broadcast.delay.assert_not_called()

    # view_deleted

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().delete_view(user=user, view=view)
        broadcast.delay.assert_not_called()

    view = data_fixture.create_grid_view(user=user, table=table)
    view.ownership_type = "personal"
    view.created_by = user
    view.save()

    with patch(
        "baserow.contrib.database.ws.views.signals.broadcast_to_users"
    ) as broadcast:
        ViewHandler().delete_view(user=user, view=view)
        args = broadcast.delay.call_args
        assert args[0][0] == [user.id]

    view = data_fixture.create_grid_view(user=user, table=table)
    view.ownership_type = "personal"
    view.created_by = user
    view.save()
    filter = ViewHandler().create_filter(user, view, field, "equal", "value")
    equal_sort = data_fixture.create_view_sort(user=user, view=view, field=field)
    decorator_type_name = "left_border_color"
    value_provider_type_name = ""
    value_provider_conf = {}
    decoration = data_fixture.create_view_decoration(user=user, view=view)

    # views_reordered

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().order_views(user=user, table=table, order=[view.id])
        broadcast.delay.assert_not_called()

    # view_filter_created

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().create_filter(user, view, field, "equal", "value")
        broadcast.delay.assert_not_called()

    # view_filter_updated

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().update_filter(user, filter, field, "equal", "another value")
        broadcast.delay.assert_not_called()

    # view_filter_deleted

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().delete_filter(user, filter)
        broadcast.delay.assert_not_called()

    # view_sort_created

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().create_sort(user=user, view=view, field=field2, order="ASC")
        broadcast.delay.assert_not_called()

    # view_sort_updated

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().update_sort(user, equal_sort, field)
        broadcast.delay.assert_not_called()

    # view_sort_deleted

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().delete_sort(user, equal_sort)
        broadcast.delay.assert_not_called()

    # view_decoration_created

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().create_decoration(
            view,
            decorator_type_name,
            value_provider_type_name,
            value_provider_conf,
            user=user,
        )
        broadcast.delay.assert_not_called()

    # view_decoration_updated

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().update_decoration(decoration, user)
        broadcast.delay.assert_not_called()

    # view_decoration_deleted

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().delete_decoration(decoration, user)
        broadcast.delay.assert_not_called()

    # view_field_options_updated

    with patch("baserow.ws.registries.broadcast_to_channel_group") as broadcast:
        ViewHandler().update_field_options(view, {}, user)
        broadcast.delay.assert_not_called()
