from django.test.utils import override_settings

import pytest
from baserow_premium.row_comments.actions import (
    CreateRowCommentActionType,
    DeleteRowCommentActionType,
    UpdateRowCommentActionType,
)
from baserow_premium.row_comments.handler import RowCommentHandler
from baserow_premium.row_comments.models import RowComment

from baserow.contrib.database.action.scopes import TableActionScopeType
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_row_comment_action_type(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    table = premium_data_fixture.create_database_table(user=user)
    premium_data_fixture.create_text_field(table=table)
    rows = premium_data_fixture.create_rows_in_table(table, [[]])

    row_comment = action_type_registry.get(CreateRowCommentActionType.type).do(
        user, table.id, rows[0].id, "comment"
    )
    assert row_comment.comment == "comment"


@pytest.mark.undo_redo
@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_creating_row_comments(premium_data_fixture):
    session_id = "test_session_id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    table = premium_data_fixture.create_database_table(user=user)
    premium_data_fixture.create_text_field(table=table)
    rows = premium_data_fixture.create_rows_in_table(table, [[]])

    row_comment = action_type_registry.get(CreateRowCommentActionType.type).do(
        user, table.id, rows[0].id, "comment"
    )
    assert row_comment.comment == "comment"
    assert RowComment.objects.count() == 1

    actions_undone = ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert_undo_redo_actions_are_valid(actions_undone, [CreateRowCommentActionType])

    assert RowComment.objects.count() == 0
    assert RowComment.objects_and_trash.count() == 1


@pytest.mark.undo_redo
@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_redo_creating_row_comments(premium_data_fixture):
    session_id = "test_session_id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    table = premium_data_fixture.create_database_table(user=user)
    premium_data_fixture.create_text_field(table=table)
    rows = premium_data_fixture.create_rows_in_table(table, [[]])

    row_comment = action_type_registry.get(CreateRowCommentActionType.type).do(
        user, table.id, rows[0].id, "comment"
    )
    assert row_comment.comment == "comment"
    assert RowComment.objects.count() == 1

    ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    actions_redone = ActionHandler.redo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert_undo_redo_actions_are_valid(actions_redone, [CreateRowCommentActionType])

    assert RowComment.objects.count() == 1


@pytest.mark.undo_redo
@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_updating_row_comments(premium_data_fixture):
    session_id = "test_session_id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    table = premium_data_fixture.create_database_table(user=user)
    premium_data_fixture.create_text_field(table=table)
    rows = premium_data_fixture.create_rows_in_table(table, [[]])

    row_comment = RowCommentHandler.create_comment(
        user, table.id, rows[0].id, "comment"
    )

    row_comment = action_type_registry.get(UpdateRowCommentActionType.type).do(
        user, table.id, row_comment.id, "updated comment"
    )
    assert row_comment.comment == "updated comment"

    actions_undone = ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert_undo_redo_actions_are_valid(actions_undone, [UpdateRowCommentActionType])

    row_comment.refresh_from_db()
    assert row_comment.comment == "comment"


@pytest.mark.undo_redo
@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_redo_updating_row_comments(premium_data_fixture):
    session_id = "test_session_id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    table = premium_data_fixture.create_database_table(user=user)
    premium_data_fixture.create_text_field(table=table)
    rows = premium_data_fixture.create_rows_in_table(table, [[]])

    row_comment = RowCommentHandler.create_comment(
        user, table.id, rows[0].id, "comment"
    )

    row_comment = action_type_registry.get(UpdateRowCommentActionType.type).do(
        user, table.id, row_comment.id, "updated comment"
    )
    assert row_comment.comment == "updated comment"

    ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    actions_redone = ActionHandler.redo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert_undo_redo_actions_are_valid(actions_redone, [UpdateRowCommentActionType])

    row_comment.refresh_from_db()
    assert row_comment.comment == "updated comment"


@pytest.mark.undo_redo
@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_deleting_row_comments(premium_data_fixture):
    session_id = "test_session_id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    table = premium_data_fixture.create_database_table(user=user)
    premium_data_fixture.create_text_field(table=table)
    rows = premium_data_fixture.create_rows_in_table(table, [[]])

    row_comment = RowCommentHandler.create_comment(
        user, table.id, rows[0].id, "comment"
    )

    row_comment = action_type_registry.get(DeleteRowCommentActionType.type).do(
        user, table.id, row_comment.id
    )
    assert RowComment.objects.count() == 0
    assert RowComment.objects_and_trash.count() == 1

    actions_undone = ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert_undo_redo_actions_are_valid(actions_undone, [DeleteRowCommentActionType])

    assert RowComment.objects.count() == 1


@pytest.mark.undo_redo
@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_undo_redo_deleting_row_comments(premium_data_fixture):
    session_id = "test_session_id"
    user = premium_data_fixture.create_user(
        has_active_premium_license=True, session_id=session_id
    )
    table = premium_data_fixture.create_database_table(user=user)
    premium_data_fixture.create_text_field(table=table)
    rows = premium_data_fixture.create_rows_in_table(table, [[]])

    row_comment = RowCommentHandler.create_comment(
        user, table.id, rows[0].id, "comment"
    )

    row_comment = action_type_registry.get(DeleteRowCommentActionType.type).do(
        user, table.id, row_comment.id
    )
    assert RowComment.objects.count() == 0
    assert RowComment.objects_and_trash.count() == 1

    ActionHandler.undo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    actions_redone = ActionHandler.redo(
        user, [TableActionScopeType.value(table_id=table.id)], session_id
    )

    assert_undo_redo_actions_are_valid(actions_redone, [DeleteRowCommentActionType])

    assert RowComment.objects.count() == 0
    assert RowComment.objects_and_trash.count() == 1
