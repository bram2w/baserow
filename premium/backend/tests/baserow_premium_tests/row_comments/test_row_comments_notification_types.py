from unittest.mock import call, patch

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
