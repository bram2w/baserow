from unittest.mock import MagicMock, call, patch

from django.db.models import Q
from django.shortcuts import reverse

import pytest
from freezegun import freeze_time
from rest_framework.status import HTTP_200_OK

from baserow.contrib.database.fields.notification_types import (
    CollaboratorAddedToRowNotificationType,
)
from baserow.contrib.database.rows.handler import RowHandler
from baserow.core.notifications.handler import NotificationHandler
from baserow.test_utils.helpers import AnyInt


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.tasks.broadcast_to_users.apply")
def test_notification_creation_on_adding_users_on_collaborator_fields(
    mocked_broadcast_to_users, api_client, data_fixture
):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    user_3, token_3 = data_fixture.create_user_and_token(email="test3@test.nl")
    workspace = data_fixture.create_workspace(members=[user_1, user_2, user_3])
    database = data_fixture.create_database_application(
        user=user_1, workspace=workspace, name="Placeholder"
    )
    table = data_fixture.create_database_table(name="Example", database=database)
    collaborator_field = data_fixture.create_multiple_collaborators_field(
        user=user_1, table=table, name="Collaborator 1", notify_user_when_added=True
    )
    row = RowHandler().create_row(
        user=user_1, table=table, values={collaborator_field.id: []}
    )

    with freeze_time("2023-07-06 12:00"):
        response = api_client.patch(
            reverse(
                "api:database:rows:item",
                kwargs={"table_id": table.id, "row_id": row.id},
            ),
            {f"field_{collaborator_field.id}": [{"id": user_2.id}]},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token_1}",
        )
        assert response.status_code == HTTP_200_OK

    # user_2 can see his own notification in the list of notifications
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
                "created_on": "2023-07-06T12:00:00Z",
                "type": CollaboratorAddedToRowNotificationType.type,
                "read": False,
                "sender": {
                    "id": user_1.id,
                    "username": user_1.username,
                    "first_name": user_1.first_name,
                },
                "workspace": {"id": workspace.id},
                "data": {
                    "row_id": row.id,
                    "row_name": str(row),
                    "field_id": collaborator_field.id,
                    "field_name": collaborator_field.name,
                    "table_id": table.id,
                    "table_name": table.name,
                    "database_id": database.id,
                    "database_name": database.name,
                },
            }
        ],
    }

    assert mocked_broadcast_to_users.call_count == 1
    args = mocked_broadcast_to_users.call_args_list
    assert args[0][0] == call(
        [user_2.id],
        {
            "type": "notifications_created",
            "notifications": [
                {
                    "id": AnyInt(),
                    "type": CollaboratorAddedToRowNotificationType.type,
                    "sender": {
                        "id": user_1.id,
                        "username": user_1.username,
                        "first_name": user_1.first_name,
                    },
                    "created_on": "2023-07-06T12:00:00Z",
                    "data": {
                        "row_id": row.id,
                        "row_name": str(row),
                        "field_id": collaborator_field.id,
                        "field_name": collaborator_field.name,
                        "table_id": table.id,
                        "table_name": table.name,
                        "database_id": database.id,
                        "database_name": database.name,
                    },
                    "workspace": {"id": workspace.id},
                    "read": False,
                }
            ],
        },
    )

    # user_3 has no notifications yet
    response = api_client.get(
        reverse("api:notifications:list", kwargs={"workspace_id": workspace.id}),
        HTTP_AUTHORIZATION=f"JWT {token_3}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json == {"count": 0, "next": None, "previous": None, "results": []}

    # Adding user_3 to the list of collaborators only notify user_3
    with freeze_time("2023-07-06 12:00"):
        response = api_client.patch(
            reverse(
                "api:database:rows:item",
                kwargs={"table_id": table.id, "row_id": row.id},
            ),
            {
                f"field_{collaborator_field.id}": [
                    {"id": user_2.id},
                    {"id": user_3.id},
                ]
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token_1}",
        )
        assert response.status_code == HTTP_200_OK

    assert mocked_broadcast_to_users.call_count == 2
    args = mocked_broadcast_to_users.call_args_list
    assert args[1][0] == call(
        [user_3.id],
        {
            "type": "notifications_created",
            "notifications": [
                {
                    "id": AnyInt(),
                    "type": CollaboratorAddedToRowNotificationType.type,
                    "sender": {
                        "id": user_1.id,
                        "username": user_1.username,
                        "first_name": user_1.first_name,
                    },
                    "created_on": "2023-07-06T12:00:00Z",
                    "data": {
                        "row_id": row.id,
                        "row_name": str(row),
                        "field_id": collaborator_field.id,
                        "field_name": collaborator_field.name,
                        "table_id": table.id,
                        "table_name": table.name,
                        "database_id": database.id,
                        "database_name": database.name,
                    },
                    "workspace": {"id": workspace.id},
                    "read": False,
                }
            ],
        },
    )

    # user_3 list notifications and see there is a new one for him
    response = api_client.get(
        reverse("api:notifications:list", kwargs={"workspace_id": workspace.id}),
        HTTP_AUTHORIZATION=f"JWT {token_3}",
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
                "created_on": "2023-07-06T12:00:00Z",
                "type": CollaboratorAddedToRowNotificationType.type,
                "read": False,
                "sender": {
                    "id": user_1.id,
                    "username": user_1.username,
                    "first_name": user_1.first_name,
                },
                "workspace": {"id": workspace.id},
                "data": {
                    "row_id": row.id,
                    "row_name": str(row),
                    "field_id": collaborator_field.id,
                    "field_name": collaborator_field.name,
                    "table_id": table.id,
                    "table_name": table.name,
                    "database_id": database.id,
                    "database_name": database.name,
                },
            }
        ],
    }


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.tasks.broadcast_to_users.apply")
def test_notifications_are_grouped_when_user_is_added_to_multiple_rows(
    mocked_broadcast_to_users, api_client, data_fixture
):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    workspace = data_fixture.create_workspace(members=[user_1, user_2])
    database = data_fixture.create_database_application(
        user=user_1, workspace=workspace
    )
    table = data_fixture.create_database_table(database=database)
    collaborator_field = data_fixture.create_multiple_collaborators_field(
        user=user_1, table=table, notify_user_when_added=True
    )

    with freeze_time("2023-07-06 12:00"):
        url = reverse("api:database:rows:batch", kwargs={"table_id": table.id})
        request_body = {
            "items": [
                {f"field_{collaborator_field.id}": [{"id": user_2.id}]},
                {f"field_{collaborator_field.id}": [{"id": user_2.id}]},
            ]
        }
        response = api_client.post(
            url,
            request_body,
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token_1}",
        )
        assert response.status_code == HTTP_200_OK
        row_1_id = response.json()["items"][0]["id"]
        row_2_id = response.json()["items"][1]["id"]

    # user_2 can see his own notification in the list of notifications
    response = api_client.get(
        reverse("api:notifications:list", kwargs={"workspace_id": workspace.id}),
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": AnyInt(),
                "created_on": "2023-07-06T12:00:00Z",
                "type": CollaboratorAddedToRowNotificationType.type,
                "read": False,
                "sender": {
                    "id": user_1.id,
                    "username": user_1.username,
                    "first_name": user_1.first_name,
                },
                "workspace": {"id": workspace.id},
                "data": {
                    "row_id": row_1_id,
                    "row_name": f"unnamed row {row_1_id}",
                    "field_id": collaborator_field.id,
                    "field_name": collaborator_field.name,
                    "table_id": table.id,
                    "table_name": table.name,
                    "database_id": database.id,
                    "database_name": database.name,
                },
            },
            {
                "id": AnyInt(),
                "created_on": "2023-07-06T12:00:00Z",
                "type": CollaboratorAddedToRowNotificationType.type,
                "read": False,
                "sender": {
                    "id": user_1.id,
                    "username": user_1.username,
                    "first_name": user_1.first_name,
                },
                "workspace": {"id": workspace.id},
                "data": {
                    "row_id": row_2_id,
                    "row_name": f"unnamed row {row_2_id}",
                    "field_id": collaborator_field.id,
                    "field_name": collaborator_field.name,
                    "table_id": table.id,
                    "table_name": table.name,
                    "database_id": database.id,
                    "database_name": database.name,
                },
            },
        ],
    }

    assert mocked_broadcast_to_users.call_count == 1
    args = mocked_broadcast_to_users.call_args_list
    assert args[0][0] == call(
        [user_2.id],
        {
            "type": "notifications_created",
            "notifications": [
                {
                    "id": AnyInt(),
                    "type": CollaboratorAddedToRowNotificationType.type,
                    "sender": {
                        "id": user_1.id,
                        "username": user_1.username,
                        "first_name": user_1.first_name,
                    },
                    "created_on": "2023-07-06T12:00:00Z",
                    "data": {
                        "row_id": row_1_id,
                        "row_name": f"unnamed row {row_1_id}",
                        "field_id": collaborator_field.id,
                        "field_name": collaborator_field.name,
                        "table_id": table.id,
                        "table_name": table.name,
                        "database_id": database.id,
                        "database_name": database.name,
                    },
                    "workspace": {"id": workspace.id},
                    "read": False,
                },
                {
                    "id": AnyInt(),
                    "type": CollaboratorAddedToRowNotificationType.type,
                    "sender": {
                        "id": user_1.id,
                        "username": user_1.username,
                        "first_name": user_1.first_name,
                    },
                    "created_on": "2023-07-06T12:00:00Z",
                    "data": {
                        "row_id": row_2_id,
                        "row_name": f"unnamed row {row_2_id}",
                        "field_id": collaborator_field.id,
                        "field_name": collaborator_field.name,
                        "table_id": table.id,
                        "table_name": table.name,
                        "database_id": database.id,
                        "database_name": database.name,
                    },
                    "workspace": {"id": workspace.id},
                    "read": False,
                },
            ],
        },
    )


@pytest.mark.django_db(transaction=True)
@patch("baserow.ws.tasks.broadcast_to_users.apply")
def test_notifications_are_not_created_if_the_field_parameter_is_false(
    mocked_broadcast_to_users, api_client, data_fixture
):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    workspace = data_fixture.create_workspace(members=[user_1, user_2])
    database = data_fixture.create_database_application(
        user=user_1, workspace=workspace, name="Placeholder"
    )
    table = data_fixture.create_database_table(name="Example", database=database)
    collaborator_field = data_fixture.create_multiple_collaborators_field(
        user=user_1, table=table, name="Collaborator 1", notify_user_when_added=False
    )
    row = RowHandler().create_row(
        user=user_1, table=table, values={collaborator_field.id: []}
    )

    with freeze_time("2023-07-06 12:00"):
        response = api_client.patch(
            reverse(
                "api:database:rows:item",
                kwargs={"table_id": table.id, "row_id": row.id},
            ),
            {f"field_{collaborator_field.id}": [{"id": user_1.id}, {"id": user_2.id}]},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token_1}",
        )
        assert response.status_code == HTTP_200_OK

    # user_2 can see his own notification in the list of notifications
    response = api_client.get(
        reverse("api:notifications:list", kwargs={"workspace_id": workspace.id}),
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json == {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }

    assert mocked_broadcast_to_users.call_count == 0


@pytest.mark.django_db(transaction=True)
@patch("baserow.core.notifications.handler.get_mail_connection")
def test_email_notifications_are_created_correctly(
    mock_get_mail_connection,
    data_fixture,
    api_client,
):
    mock_connection = MagicMock()
    mock_get_mail_connection.return_value = mock_connection

    user_1, token_1 = data_fixture.create_user_and_token(
        email="test1@test.nl", first_name="User 1"
    )
    user_2 = data_fixture.create_user(email="test2@test.nl", first_name="User 2")
    workspace = data_fixture.create_workspace(members=[user_1, user_2])
    database = data_fixture.create_database_application(
        user=user_1, workspace=workspace, name="Placeholder"
    )
    table = data_fixture.create_database_table(name="Example", database=database)
    collaborator_field = data_fixture.create_multiple_collaborators_field(
        user=user_1, table=table, name="Collaborator 1", notify_user_when_added=True
    )
    row = RowHandler().create_row(
        user=user_1, table=table, values={collaborator_field.id: []}
    )

    with freeze_time("2023-07-06 12:00"):
        response = api_client.patch(
            reverse(
                "api:database:rows:item",
                kwargs={"table_id": table.id, "row_id": row.id},
            ),
            {f"field_{collaborator_field.id}": [{"id": user_2.id}]},
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
                "title": f"User 1 assigned you to Collaborator 1 in row unnamed row"
                f" {row.id} in Example.",
                "description": None,
            }
        ],
        "new_notifications_count": 1,
        "unlisted_notifications_count": 0,
    }
    user_2_summary_email_context = user_2_summary_email.get_context()

    for k, v in expected_context.items():
        assert user_2_summary_email_context[k] == v
