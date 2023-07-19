from baserow.core.notifications.handler import NotificationHandler


class NotificationsFixture:
    def create_notification(self, recipients=None, **kwargs):
        if recipients is None:
            recipients = [self.create_user()]

        notification_type = kwargs.pop("type", "fake_notification")

        notification_recipients = NotificationHandler.create_notification_for_users(
            notification_type, recipients=recipients, **kwargs
        )

        return notification_recipients[0].notification

    def create_workspace_notification(self, recipients=None, workspace=None, **kwargs):
        if recipients is None:
            recipients = [self.create_user()]

        if workspace is None:
            workspace = self.create_workspace(members=recipients)

        if "type" not in kwargs:
            kwargs["type"] = "fake_workspace_notification"

        return self.create_notification(
            recipients=recipients, workspace=workspace, **kwargs
        )

    def create_user_notification(self, recipients=None, **kwargs):
        if "type" not in kwargs:
            kwargs["type"] = "fake_user_notification"

        return self.create_notification(recipients=recipients, **kwargs)

    def create_broadcast_notification(self, **kwargs):
        notification_type = kwargs.pop("type", "fake_broadcast_notification")

        if "workspace_id" in kwargs:
            kwargs["workspace_id"] = None

        notification = NotificationHandler.create_broadcast_notification(
            notification_type, workspace_id=None, **kwargs
        )
        return notification
