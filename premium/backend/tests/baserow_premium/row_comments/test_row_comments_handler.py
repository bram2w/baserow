import pytest

from baserow_premium.row_comments.exceptions import InvalidRowCommentException
from baserow_premium.row_comments.handler import RowCommentHandler


@pytest.mark.django_db
def test_cant_make_null_comment_using_handler(data_fixture):
    user = data_fixture.create_user(first_name="Test User")
    table, fields, rows = data_fixture.build_table(
        columns=[("text", "text")], rows=["first row", "second_row"], user=user
    )
    with pytest.raises(InvalidRowCommentException):
        # noinspection PyTypeChecker
        RowCommentHandler.create_comment(user, table.id, rows[0].id, None)


@pytest.mark.django_db
def test_cant_make_blank_comment_using_handler(data_fixture):
    user = data_fixture.create_user(first_name="Test User")
    table, fields, rows = data_fixture.build_table(
        columns=[("text", "text")], rows=["first row", "second_row"], user=user
    )
    with pytest.raises(InvalidRowCommentException):
        RowCommentHandler.create_comment(user, table.id, rows[0].id, "")
