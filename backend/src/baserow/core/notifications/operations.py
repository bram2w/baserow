from baserow.core.operations import WorkspaceCoreOperationType


class ListNotificationsOperationType(WorkspaceCoreOperationType):
    type = "workspace.list_notifications"


class ClearNotificationsOperationType(WorkspaceCoreOperationType):
    type = "workspace.clear_notification"


class MarkNotificationAsReadOperationType(WorkspaceCoreOperationType):
    type = "workspace.mark_notification_as_read"
