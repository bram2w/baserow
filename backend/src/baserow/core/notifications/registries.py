from baserow.core.exceptions import (
    InstanceTypeAlreadyRegistered,
    InstanceTypeDoesNotExist,
)
from baserow.core.registry import (
    CustomFieldsRegistryMixin,
    Instance,
    MapAPIExceptionsInstanceMixin,
    ModelRegistryMixin,
    Registry,
)

from .models import Notification


class NotificationType(MapAPIExceptionsInstanceMixin, Instance):
    model_class = Notification


class NotificationTypeDoesNotExist(InstanceTypeDoesNotExist):
    """Raised when a notification type with a given identifier does not exist."""


class NotificationTypeAlreadyRegistered(InstanceTypeAlreadyRegistered):
    """Raised when a notification type is already registered."""


class NotificationTypeRegistry(
    CustomFieldsRegistryMixin,
    ModelRegistryMixin[Notification, NotificationType],
    Registry[NotificationType],
):
    """
    The registry that holds all the available job types.
    """

    name = "notification_type"

    does_not_exist_exception_class = NotificationTypeDoesNotExist
    already_registered_exception_class = NotificationTypeAlreadyRegistered


notification_type_registry: NotificationTypeRegistry = NotificationTypeRegistry()
