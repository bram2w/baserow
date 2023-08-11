import contextlib
from typing import Optional

from baserow.core.notifications.registries import (
    EmailNotificationTypeMixin,
    NotificationType,
    notification_type_registry,
)


@contextlib.contextmanager
def custom_notification_types_registered():
    class ExcludedFromEmailTestNotification(NotificationType):
        type = "excluded_from_email_test_notification"

    class TestNotification(EmailNotificationTypeMixin, NotificationType):
        type = "test_email_notification"

        @classmethod
        def get_notification_title_for_email(cls, notification, context) -> str:
            return "Test notification"

        @classmethod
        def get_notification_description_for_email(
            cls, notification, context
        ) -> Optional[str]:
            return None

    notification_type_registry.register(ExcludedFromEmailTestNotification())
    notification_type_registry.register(TestNotification())

    try:
        yield TestNotification, ExcludedFromEmailTestNotification
    finally:
        notification_type_registry.unregister(ExcludedFromEmailTestNotification.type)
        notification_type_registry.unregister(TestNotification.type)
