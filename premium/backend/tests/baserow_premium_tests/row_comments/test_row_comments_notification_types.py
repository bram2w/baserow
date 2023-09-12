from unittest.mock import MagicMock, call, patch

from django.db.models import Q
from django.shortcuts import reverse
from django.test import override_settings

import pytest
from baserow_premium.row_comments.handler import RowCommentHandler
from baserow_premium.row_comments.notification_types import (
    RowCommentMentionNotificationType,
)
from freezegun import freeze_time
from rest_framework.status import HTTP_200_OK

from baserow.core.notifications.handler import NotificationHandler
from baserow.core.notifications.models import NotificationRecipient
from baserow.test_utils.helpers import AnyInt


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.core.notifications.signals.notification_created.send")
def test_notification_creation_on_creating_row_comment_mention(
    mocked_notification_created, api_client, premium_data_fixture
):
    user_1, token_1 = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table, _, rows = premium_data_fixture.build_table(
        columns=[("text", "text")], rows=["first row", "second_row"], user=user_1
    )
    workspace = table.database.workspace
    user_2, token_2 = premium_data_fixture.create_user_and_token(
        workspace=workspace, has_active_premium_license=True
    )

    message = premium_data_fixture.create_comment_message_with_mentions([user_2])

    with freeze_time("2020-01-01 12:00"):
        response = api_client.post(
            reverse(
                "api:premium:row_comments:list",
                kwargs={"table_id": table.id, "row_id": rows[0].id},
            ),
            {"message": message},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token_1}",
        )
    assert response.status_code == HTTP_200_OK
    comment_id = response.json()["id"]

    assert mocked_notification_created.called_once()
    args = mocked_notification_created.call_args
    assert args == call(
        sender=NotificationHandler,
        notification=NotificationHandler.get_notification_by(
            user_2, data__contains={"comment_id": comment_id}
        ),
        notification_recipients=list(
            NotificationRecipient.objects.filter(recipient=user_2)
        ),
        user=user_1,
    )

    # the user can see the notification in the list of notifications
    response = api_client.get(
        reverse("api:notifications:list", kwargs={"workspace_id": workspace.id}),
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": AnyInt(),
                "created_on": "2020-01-01T12:00:00Z",
                "type": RowCommentMentionNotificationType.type,
                "read": False,
                "sender": {
                    "id": user_1.id,
                    "username": user_1.username,
                    "first_name": user_1.first_name,
                },
                "workspace": {"id": workspace.id},
                "data": {
                    "database_id": table.database.id,
                    "database_name": table.database.name,
                    "table_id": table.id,
                    "table_name": table.name,
                    "row_id": rows[0].id,
                    "comment_id": comment_id,
                    "message": message,
                },
            }
        ],
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.core.notifications.signals.notification_created.send")
def test_notify_only_new_mentions_when_updating_a_comment(
    mocked_notification_created, api_client, premium_data_fixture
):
    user_1, token_1 = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    table, _, rows = premium_data_fixture.build_table(
        columns=[("text", "text")], rows=["first row", "second_row"], user=user_1
    )
    workspace = table.database.workspace
    user_2 = premium_data_fixture.create_user(
        workspace=workspace, has_active_premium_license=True
    )

    message = premium_data_fixture.create_comment_message_with_mentions([user_2])
    with freeze_time("2020-01-01 11:00"):
        comment = RowCommentHandler.create_comment(
            user_1, table.id, rows[0].id, message
        )
    new_message = premium_data_fixture.create_comment_message_with_mentions(
        [user_1, user_2]
    )

    with freeze_time("2020-01-01 12:00"):
        response = api_client.patch(
            reverse(
                "api:premium:row_comments:item",
                kwargs={"table_id": table.id, "comment_id": comment.id},
            ),
            {"message": new_message},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token_1}",
        )
    assert response.status_code == HTTP_200_OK
    comment_id = response.json()["id"]

    assert mocked_notification_created.called_once()
    args = mocked_notification_created.call_args
    assert args == call(
        sender=NotificationHandler,
        notification=NotificationHandler.get_notification_by(
            user_1, data__contains={"comment_id": comment_id}
        ),
        notification_recipients=list(
            NotificationRecipient.objects.filter(recipient=user_1)
        ),
        user=user_1,
    )

    # the user can see the notification in the list of notifications
    response = api_client.get(
        reverse("api:notifications:list", kwargs={"workspace_id": workspace.id}),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": AnyInt(),
                "type": RowCommentMentionNotificationType.type,
                "created_on": "2020-01-01T12:00:00Z",
                "read": False,
                "sender": {
                    "id": user_1.id,
                    "username": user_1.username,
                    "first_name": user_1.first_name,
                },
                "workspace": {"id": workspace.id},
                "data": {
                    "database_id": table.database.id,
                    "database_name": table.database.name,
                    "table_id": table.id,
                    "table_name": table.name,
                    "row_id": rows[0].id,
                    "comment_id": comment_id,
                    "message": new_message,
                },
            }
        ],
    }


@pytest.mark.django_db(transaction=True)
@patch("baserow.core.notifications.handler.get_mail_connection")
@override_settings(DEBUG=True)
def test_email_notifications_are_created_correctly(
    mock_get_mail_connection, premium_data_fixture, api_client
):
    mock_connection = MagicMock()
    mock_get_mail_connection.return_value = mock_connection

    user_1, token_1 = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True, first_name="User 1"
    )
    table, _, rows = premium_data_fixture.build_table(
        columns=[("text", "text")], rows=["first row", "second_row"], user=user_1
    )
    workspace = table.database.workspace
    user_2 = premium_data_fixture.create_user(
        workspace=workspace, has_active_premium_license=True, first_name="User 2"
    )

    row = rows[0]
    message = premium_data_fixture.create_comment_message_with_mentions([user_2])

    with freeze_time("2020-01-01 12:00"):
        response = api_client.post(
            reverse(
                "api:premium:row_comments:list",
                kwargs={"table_id": table.id, "row_id": row.id},
            ),
            {"message": message},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token_1}",
        )
        assert response.status_code == HTTP_200_OK

    # Force to send the notifications
    res = NotificationHandler.send_new_notifications_to_users_matching_filters_by_email(
        Q(pk=user_2.pk)
    )
    assert res.users_with_notifications == [user_2]
    assert len(res.users_with_notifications[0].unsent_email_notifications) == 1
    assert res.users_with_notifications[0].total_unsent_count == 1
    assert res.remaining_users_to_notify_count == 0

    mock_get_mail_connection.assert_called_once_with(fail_silently=False)
    summary_emails = mock_connection.send_messages.call_args[0][0]
    assert len(summary_emails) == 1
    user_2_summary_email = summary_emails[0]
    assert user_2_summary_email.to == [user_2.email]
    assert user_2_summary_email.get_subject() == "You have 1 new notification - Baserow"

    expected_context = {
        "notifications": [
            {
                "title": f"User 1 mentioned you in row {row.id} in {table.name}.",
                "description": "@User 2",
            }
        ],
        "new_notifications_count": 1,
        "unlisted_notifications_count": 0,
    }
    user_2_summary_email_context = user_2_summary_email.get_context()

    for k, v in expected_context.items():
        assert user_2_summary_email_context[k] == v
