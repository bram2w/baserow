from unittest.mock import ANY, call, patch

import pytest

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.core.trash.handler import TrashHandler


class MatchDictSubSet(object):
    def __init__(self, sub_set):
        self.sub_set = sub_set

    def __eq__(self, other):
        return all(
            self.sub_set[k] == other[k] for k in self.sub_set.keys() & other.keys()
        )

    def __repr__(self):
        return f"MatchDictSubSet({self.sub_set})"


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_field_created_public_views_are_sent_field_created_with_restricted_related(
    mock_broadcast_to_channel_group,
    data_fixture,
    django_assert_num_queries,
    public_realtime_view_tester,
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table, order=0)
    hidden_broken_field = data_fixture.create_formula_field(
        table=table, formula="field('a')", name="hidden_broken"
    )
    visible_broken_field = data_fixture.create_formula_field(
        table=table, formula="field('a')", name="visible_broken"
    )
    public_view = public_realtime_view_tester.create_public_view(
        user,
        table,
        visible_fields=[visible_broken_field],
        hidden_fields=[hidden_broken_field],
    )
    public_realtime_view_tester.create_other_views_that_should_not_get_realtime_signals(
        user, table, mock_broadcast_to_channel_group
    )
    new_field = FieldHandler().create_field(user, table, "text", name="a", order=1)

    expected_calls = [
        call(f"table-{table.id}", ANY, ANY, None),
    ]
    if public_realtime_view_tester.newly_created_field_visible_by_default:
        expected_calls.append(
            call(
                f"view-{public_view.slug}",
                {
                    "type": "field_created",
                    "field": MatchDictSubSet(
                        {
                            "id": new_field.id,
                            "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                            "name": new_field.name,
                        }
                    ),
                    "related_fields": [
                        MatchDictSubSet(
                            {
                                "id": visible_broken_field.id,
                                "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                                "name": visible_broken_field.name,
                            }
                        ),
                    ],
                },
                None,
                None,
            ),
        )
    assert mock_broadcast_to_channel_group.delay.mock_calls == (expected_calls)


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_field_deleted_public_views_are_field_deleted_with_restricted_related(
    mock_broadcast_to_channel_group, data_fixture, public_realtime_view_tester
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table, order=0, name="visible")
    hidden_broken_field = data_fixture.create_formula_field(
        table=table, formula="field('visible')", name="hidden_broken"
    )
    visible_broken_field = data_fixture.create_formula_field(
        table=table, formula="field('visible')", name="visible_broken"
    )
    public_view = public_realtime_view_tester.create_public_view(
        user,
        table,
        visible_fields=[visible_broken_field, visible_field],
        hidden_fields=[hidden_broken_field],
    )
    deleted_field_id = visible_field.id

    public_realtime_view_tester.create_other_views_that_should_not_get_realtime_signals(
        user, table, mock_broadcast_to_channel_group
    )

    FieldHandler().delete_field(user, visible_field)

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY, None),
            call(
                f"view-{public_view.slug}",
                {
                    "type": "field_deleted",
                    "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                    "field_id": deleted_field_id,
                    "related_fields": [
                        MatchDictSubSet(
                            {
                                "id": visible_broken_field.id,
                                "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                                "name": visible_broken_field.name,
                            }
                        ),
                    ],
                },
                None,
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_field_restored_public_views_sent_event_with_restricted_related_fields(
    mock_broadcast_to_channel_group, data_fixture, public_realtime_view_tester
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table, order=0, name="visible")
    hidden_broken_field = data_fixture.create_formula_field(
        table=table, formula="field('visible')", name="hidden_broken"
    )
    visible_broken_field = data_fixture.create_formula_field(
        table=table, formula="field('visible')", name="visible_broken"
    )
    public_view = public_realtime_view_tester.create_public_view(
        user,
        table,
        visible_fields=[visible_broken_field, visible_field],
        hidden_fields=[hidden_broken_field],
    )
    public_realtime_view_tester.create_other_views_that_should_not_get_realtime_signals(
        user, table, mock_broadcast_to_channel_group
    )
    deleted_field_id = visible_field.id
    FieldHandler().delete_field(user, visible_field)
    TrashHandler().restore_item(user, "field", visible_field.id)

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY, None),
            call(f"view-{public_view.slug}", ANY, ANY, None),
            call(f"table-{table.id}", ANY, ANY, None),
            call(
                f"view-{public_view.slug}",
                {
                    "type": "field_restored",
                    "field": MatchDictSubSet(
                        {
                            "id": deleted_field_id,
                            "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                            "name": visible_field.name,
                        }
                    ),
                    "related_fields": [
                        MatchDictSubSet(
                            {
                                "id": visible_broken_field.id,
                                "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                                "name": visible_broken_field.name,
                            }
                        ),
                    ],
                },
                None,
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_field_updated_public_views_are_sent_event_with_restricted_related(
    mock_broadcast_to_channel_group, data_fixture, public_realtime_view_tester
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_field = data_fixture.create_text_field(table=table, order=0, name="b")
    hidden_broken_field = data_fixture.create_formula_field(
        table=table, formula="field('a')", name="hidden_broken"
    )
    visible_broken_field = data_fixture.create_formula_field(
        table=table, formula="field('a')", name="visible_broken"
    )
    public_view = public_realtime_view_tester.create_public_view(
        user,
        table,
        visible_fields=[visible_broken_field, visible_field],
        hidden_fields=[hidden_broken_field],
    )

    public_realtime_view_tester.create_other_views_that_should_not_get_realtime_signals(
        user, table, mock_broadcast_to_channel_group
    )

    updated_field = FieldHandler().update_field(user, visible_field, name="a")

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY, None),
            call(
                f"view-{public_view.slug}",
                {
                    "type": "field_updated",
                    "field_id": updated_field.id,
                    "field": MatchDictSubSet(
                        {
                            "id": updated_field.id,
                            "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                            "name": updated_field.name,
                        }
                    ),
                    "related_fields": [
                        MatchDictSubSet(
                            {
                                "id": visible_broken_field.id,
                                "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                                "name": visible_broken_field.name,
                            }
                        ),
                    ],
                },
                None,
                None,
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_cover_image_is_always_included_in_field_update_signal(
    mock_broadcast_to_channel_group, data_fixture, public_realtime_view_tester
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    file_field = data_fixture.create_file_field(table=table, order=0, name="file")
    public_gallery_view = data_fixture.create_gallery_view(
        table=table, user=user, public=True, card_cover_image_field=file_field
    )
    data_fixture.create_gallery_view_field_option(
        public_gallery_view, file_field, hidden=True
    )

    updated_field = FieldHandler().update_field(user, file_field, name="a")

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY, None),
            call(
                f"view-{public_gallery_view.slug}",
                {
                    "type": "field_updated",
                    "field_id": updated_field.id,
                    "field": MatchDictSubSet(
                        {
                            "id": updated_field.id,
                            "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                            "name": updated_field.name,
                        }
                    ),
                    "related_fields": [],
                },
                None,
                None,
            ),
        ]
    )
