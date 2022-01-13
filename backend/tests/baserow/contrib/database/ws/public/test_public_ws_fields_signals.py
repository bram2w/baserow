import pytest

from unittest.mock import patch, call, ANY

from baserow.contrib.database.api.constants import PUBLIC_PLACEHOLDER_ENTITY_ID
from baserow.contrib.database.fields.dependencies.handler import FieldDependencyHandler
from baserow.contrib.database.fields.field_cache import FieldCache
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
    mock_broadcast_to_channel_group, data_fixture, django_assert_num_queries
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
    field_cache = FieldCache()
    FieldDependencyHandler().rebuild_dependencies(hidden_broken_field, field_cache)
    FieldDependencyHandler().rebuild_dependencies(visible_broken_field, field_cache)
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    public_view = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    data_fixture.create_grid_view_field_option(
        public_view, hidden_broken_field, hidden=True, order=0
    )
    new_visible_field = FieldHandler().create_field(
        user, table, "text", name="a", order=1
    )

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(
                f"view-{public_view.slug}",
                {
                    "type": "field_created",
                    "field": MatchDictSubSet(
                        {
                            "id": new_visible_field.id,
                            "table_id": PUBLIC_PLACEHOLDER_ENTITY_ID,
                            "name": new_visible_field.name,
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
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_field_deleted_public_views_are_field_deleted_with_restricted_related(
    mock_broadcast_to_channel_group, data_fixture
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
    field_cache = FieldCache()
    FieldDependencyHandler().rebuild_dependencies(hidden_broken_field, field_cache)
    FieldDependencyHandler().rebuild_dependencies(visible_broken_field, field_cache)
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    public_view = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    data_fixture.create_grid_view_field_option(
        public_view, hidden_broken_field, hidden=True, order=0
    )
    deleted_field_id = visible_field.id
    FieldHandler().delete_field(user, visible_field)

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
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
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_field_restored_public_views_sent_event_with_restricted_related_fields(
    mock_broadcast_to_channel_group, data_fixture
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
    field_cache = FieldCache()
    FieldDependencyHandler().rebuild_dependencies(hidden_broken_field, field_cache)
    FieldDependencyHandler().rebuild_dependencies(visible_broken_field, field_cache)
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    public_view = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    data_fixture.create_grid_view_field_option(
        public_view, hidden_broken_field, hidden=True, order=0
    )
    deleted_field_id = visible_field.id
    FieldHandler().delete_field(user, visible_field)
    TrashHandler().restore_item(user, "field", visible_field.id)

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
            call(f"view-{public_view.slug}", ANY, ANY),
            call(f"table-{table.id}", ANY, ANY),
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
            ),
        ]
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.registries.broadcast_to_channel_group")
def test_when_field_updated_public_views_are_sent_event_with_restricted_related(
    mock_broadcast_to_channel_group, data_fixture
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
    field_cache = FieldCache()
    FieldDependencyHandler().rebuild_dependencies(hidden_broken_field, field_cache)
    FieldDependencyHandler().rebuild_dependencies(visible_broken_field, field_cache)
    # Should not appear in any results
    data_fixture.create_form_view(user, table=table, public=True)
    public_view = data_fixture.create_grid_view(
        user, create_options=False, table=table, public=True, order=0
    )
    data_fixture.create_grid_view_field_option(
        public_view, hidden_broken_field, hidden=True, order=0
    )
    updated_field = FieldHandler().update_field(user, visible_field, name="a")

    assert mock_broadcast_to_channel_group.delay.mock_calls == (
        [
            call(f"table-{table.id}", ANY, ANY),
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
            ),
        ]
    )
