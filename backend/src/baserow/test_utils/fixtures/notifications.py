from baserow.core.notifications.handler import NotificationHandler
from baserow.core.notifications.registries import (
    NotificationType,
    NotificationTypeAlreadyRegistered,
    notification_type_registry,
)


class NotificationsFixture:
    def register_notification_type(self, notification_type):
        class FakeNotificationType(NotificationType):
            type = notification_type

        # register the type if not already registered
        try:
            notification_type_registry.register(FakeNotificationType())
        except NotificationTypeAlreadyRegistered:
            pass

        return FakeNotificationType

    def create_notification_for_users(self, recipients=None, **kwargs):
        if recipients is None:
            recipients = [self.create_user()]

        notification_type = kwargs.pop("notification_type", "fake_notification")

        FakeNotificationType = self.register_notification_type(notification_type)

        notification_recipients = (
            NotificationHandler.create_direct_notification_for_users(
                FakeNotificationType.type, recipients=recipients, **kwargs
            )
        )

        return notification_recipients[0].notification

    def create_workspace_notification_for_users(
        self, recipients=None, workspace=None, **kwargs
    ):
        if recipients is None:
            recipients = [self.create_user()]

        if workspace is None:
            workspace = self.create_workspace(members=recipients)

        if "notification_type" not in kwargs:
            kwargs["notification_type"] = "fake_workspace_notification"

        return self.create_notification_for_users(
            recipients=recipients, workspace=workspace, **kwargs
        )

    def create_user_notification_for_users(self, recipients=None, **kwargs):
        if "notification_type" not in kwargs:
            kwargs["notification_type"] = "fake_user_notification"

        return self.create_notification_for_users(recipients=recipients, **kwargs)

    def create_broadcast_notification(self, **kwargs):
        notification_type = kwargs.pop("notification_type", "fake_notification")

        FakeNotificationType = self.register_notification_type(notification_type)

        if "workspace_id" in kwargs:
            kwargs["workspace_id"] = None

        notification = NotificationHandler.create_broadcast_notification(
            FakeNotificationType.type, workspace_id=None, **kwargs
        )

        return notification
