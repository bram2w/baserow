from unittest.mock import call, patch

from django.test.utils import override_settings

import pytest
from baserow_premium.license.exceptions import FeaturesNotAvailableError
from baserow_premium.row_comments.exceptions import InvalidRowCommentException
from baserow_premium.row_comments.handler import RowCommentHandler
from freezegun import freeze_time

from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_make_null_comment_using_handler(premium_data_fixture):
    user = premium_data_fixture.create_user(
        first_name="Test User", has_active_premium_license=True
    )
    table, fields, rows = premium_data_fixture.build_table(
        columns=[("text", "text")], rows=["first row", "second_row"], user=user
    )
    with pytest.raises(InvalidRowCommentException):
        # noinspection PyTypeChecker
        RowCommentHandler.create_comment(user, table.id, rows[0].id, None)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_make_blank_comment_using_handler(premium_data_fixture):
    user = premium_data_fixture.create_user(
        first_name="Test User", has_active_premium_license=True
    )
    table, fields, rows = premium_data_fixture.build_table(
        columns=[("text", "text")], rows=["first row", "second_row"], user=user
    )
    with pytest.raises(InvalidRowCommentException):
        RowCommentHandler.create_comment(user, table.id, rows[0].id, "")


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_create_comment_without_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user(first_name="Test User")
    table, fields, rows = premium_data_fixture.build_table(
        columns=[("text", "text")], rows=["first row", "second_row"], user=user
    )
    with pytest.raises(FeaturesNotAvailableError):
        RowCommentHandler.create_comment(user, table.id, rows[0].id, "Test")


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_create_comment_without_premium_license_for_group(
    premium_data_fixture, alternative_per_group_license_service
):
    user = premium_data_fixture.create_user(
        first_name="Test User", has_active_premium_license=True
    )
    table, fields, rows = premium_data_fixture.build_table(
        columns=[("text", "text")], rows=["first row", "second_row"], user=user
    )

    alternative_per_group_license_service.restrict_user_premium_to(
        user, [table.database.group_id]
    )
    RowCommentHandler.create_comment(user, table.id, rows[0].id, "Test")

    alternative_per_group_license_service.restrict_user_premium_to(user, [0])
    with pytest.raises(FeaturesNotAvailableError):
        RowCommentHandler.create_comment(user, table.id, rows[0].id, "Test")


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
@patch("baserow_premium.row_comments.signals.row_comment_created.send")
def test_row_comment_created_signal_called(
    mock_row_comment_created, premium_data_fixture
):
    user = premium_data_fixture.create_user(
        first_name="test_user", has_active_premium_license=True
    )
    table, fields, rows = premium_data_fixture.build_table(
        columns=[("text", "text")], rows=["first row"], user=user
    )

    with freeze_time("2020-01-02 12:00"):
        c = RowCommentHandler.create_comment(user, table.id, rows[0].id, "comment")

    mock_row_comment_created.assert_called_once()
    args = mock_row_comment_created.call_args

    assert args == call(RowHandler, row_comment=c, user=user)
