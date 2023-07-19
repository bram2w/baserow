from django.dispatch import Signal

notification_created = Signal()
notification_marked_as_read = Signal()
all_notifications_marked_as_read = Signal()
all_notifications_cleared = Signal()
