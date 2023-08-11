from unittest.mock import call, patch

import pytest

from baserow.core.notifications.handler import NotificationHandler
from baserow.core.notifications.models import NotificationRecipient


@pytest.mark.django_db
@patch("baserow.core.notifications.signals.notification_created.send")
def test_notification_created_signal_called(mock_notification_created, data_fixture):
    sender = data_fixture.create_user()
    recipient = data_fixture.create_user()

    notification = data_fixture.create_workspace_notification_for_users(
        notification_type="direct",
        recipients=[recipient],
        data={"test": True},
        sender=sender,
    )
    mock_notification_created.assert_called_once()
    args = mock_notification_created.call_args

    assert args == call(
        sender=NotificationHandler,
        notification=notification,
        notification_recipients=list(notification.notificationrecipient_set.all()),
        user=sender,
    )


@pytest.mark.django_db
@patch("baserow.core.notifications.signals.notification_created.send")
def test_notification_broadcast_created_signal_called(
    mock_notification_created, data_fixture
):
    notification = data_fixture.create_broadcast_notification(
        notification_type="broadcast", data={"test": True}
    )
    mock_notification_created.assert_called_once()
    args = mock_notification_created.call_args

    assert args == call(
        sender=NotificationHandler,
        notification=notification,
        notification_recipients=list(
            NotificationRecipient.objects.filter(
                recipient=None, notification=notification
            )
        ),
        user=None,
    )


@pytest.mark.django_db
@patch("baserow.core.notifications.signals.notification_marked_as_read.send")
def test_notification_marked_as_read_signal_called(
    mock_notification_marked_as_read, data_fixture
):
    sender = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=sender)
    recipient = data_fixture.create_user(
        workspace=workspace, web_socket_id="web_socket_id"
    )
    notification = data_fixture.create_workspace_notification_for_users(
        recipients=[recipient], workspace=workspace, sender=sender
    )
    notification_recipient = NotificationHandler.mark_notification_as_read(
        recipient, notification
    )

    mock_notification_marked_as_read.assert_called_once()
    args = mock_notification_marked_as_read.call_args

    assert args == call(
        sender=NotificationHandler,
        user=recipient,
        notification=notification,
        notification_recipient=notification_recipient,
        ignore_web_socket_id="web_socket_id",
    )


@pytest.mark.django_db
@patch("baserow.core.notifications.signals.all_notifications_marked_as_read.send")
def test_all_notifications_marked_as_read_signal_called(
    mock_all_notifications_marked_as_read, data_fixture
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    NotificationHandler.mark_all_notifications_as_read(user, workspace)

    mock_all_notifications_marked_as_read.assert_called_once()
    args = mock_all_notifications_marked_as_read.call_args

    assert args == call(sender=NotificationHandler, user=user, workspace=workspace)


@pytest.mark.django_db
@patch("baserow.core.notifications.signals.all_notifications_cleared.send")
def test_all_notifications_cleared_signal_called(
    mock_all_notifications_cleared, data_fixture
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    NotificationHandler.clear_all_notifications(user, workspace)

    mock_all_notifications_cleared.assert_called_once()
    args = mock_all_notifications_cleared.call_args

    assert args == call(sender=NotificationHandler, user=user, workspace=workspace)
