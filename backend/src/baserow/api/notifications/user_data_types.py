from baserow.api.user.registries import UserDataType
from baserow.core.notifications.handler import NotificationHandler


class UnreadUserNotificationsCountPermissionsDataType(UserDataType):
    type = "user_notifications"

    def get_user_data(self, user, request) -> dict:
        """
        Responsible for annotating `User` responses with the number of unread
        user notifications. User notifications are direct (non-broadcast)
        notifications sent to the user and not bound to a specific workspace.
        """

        unread_count = NotificationHandler.get_unread_notifications_count(user)
        return {"unread_count": unread_count}
