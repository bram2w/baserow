from datetime import datetime
from typing import Any, Dict, Optional, Type

from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver

from baserow_premium.license.exceptions import FeaturesNotAvailableError

from baserow.core.action.registries import ActionType
from baserow.core.action.signals import ActionCommandType, action_done
from baserow.core.models import Group

from .handler import AuditLogHandler


@receiver(action_done)
def log_action(
    sender,
    user: AbstractUser,
    action_type: Type[ActionType],
    action_params: Dict[str, Any],
    action_timestamp: datetime,
    action_command_type: ActionCommandType,
    group: Optional[Group] = None,
    **kwargs
):
    try:
        AuditLogHandler.log_action(
            user,
            action_type,
            action_params,
            action_timestamp,
            action_command_type,
            group=group,
            **kwargs
        )
    except FeaturesNotAvailableError:
        pass
