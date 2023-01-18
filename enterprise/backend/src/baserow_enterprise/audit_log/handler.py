from datetime import datetime
from typing import Any, Dict, Optional, Type

from django.contrib.auth.models import AbstractUser

from baserow_premium.license.handler import LicenseHandler

from baserow.api.sessions import get_user_remote_addr_ip
from baserow.core.action.registries import ActionType
from baserow.core.action.signals import ActionCommandType
from baserow.core.models import Group
from baserow_enterprise.features import AUDIT_LOG

from .models import AuditLogEntry


class AuditLogHandler:
    @classmethod
    def log_action(
        cls,
        user: AbstractUser,
        action_type: Type[ActionType],
        action_params: Dict[str, Any],
        action_timestamp: datetime,
        action_command_type: ActionCommandType,
        group: Optional[Group] = None,
        **kwargs: Any,
    ):
        """
        Creates a new audit log entry for the given user, group and event type.
        The kwargs will be stored as JSON in the data field of the audit log
        entry.

        :param user: The user that performed the action.
        :param action_type: The type of the action that should be logged.
        :param action_params: The parameters that were used to perform the
            action.
        :param action_timestamp: The timestamp when the action was performed.
        :param action_command_type: The command type that was used to perform
            the action.
        :param group: The group that the action was performed on.
        :raises FeaturesNotAvailableError: When the AUDIT_LOG feature is not
            available.
        """

        LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(AUDIT_LOG, user)

        group_id, group_name = None, None
        if group is not None:
            group_id = group.id
            group_name = group.name

        ip_address = get_user_remote_addr_ip(user)

        return AuditLogEntry.objects.create(
            user_id=user.id,
            user_email=user.email,
            group_id=group_id,
            group_name=group_name,
            action_type=action_type.type,
            action_params=action_params,
            action_timestamp=action_timestamp,
            action_command_type=action_command_type.name,
            original_action_short_descr=action_type.description.short,
            original_action_long_descr=action_type.description.long,
            original_action_context_descr=action_type.description.context,
            ip_address=ip_address,
        )

    @classmethod
    def delete_entries_older_than(cls, cutoff: datetime):
        """
        Deletes all audit log entries that are older than the given number of days.

        :param cutoff: The date and time before which all entries will be deleted.
        """

        AuditLogEntry.objects.filter(action_timestamp__lt=cutoff).delete()
