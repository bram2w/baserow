from copy import deepcopy
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver

import posthog
from loguru import logger

from baserow.core.action.signals import ActionCommandType, action_done
from baserow.core.models import Workspace
from baserow.core.utils import exception_capturer


def capture_event(
    user: AbstractUser,
    event: str,
    properties: dict,
    session: Optional[str] = None,
    workspace: Optional[Workspace] = None,
):
    """
    Captures a Posthog event in a consistent property format.

    :param user: The user that performed the event.
    :param event: Unique name identifying the event.
    :param properties: A dictionary containing the properties that must be added.
        Note that the `user_email`, `user_session`, `workspace_id`,
        and `workspace_name` will be overwritten.
    :param session: A unique session id that identifies the user throughout their
        session.
    :param workspace: Optionally the workspace related to the event.
    """

    if not settings.POSTHOG_ENABLED:
        return

    properties["user_email"] = user.email

    if session is not None:
        properties["user_session"] = session

    if workspace is not None:
        properties["workspace_id"] = workspace.id
        properties["workspace_name"] = workspace.name

    try:
        posthog.capture(
            distinct_id=user.id,
            event=event,
            properties=properties,
        )
    except Exception as e:
        logger.error(
            "Failed to log to Posthog because of {e}.",
            e=str(e),
        )
        exception_capturer(e)


@receiver(action_done)
def capture_event_action_done(
    sender,
    user,
    action_type,
    action_params,
    action_timestamp,
    action_command_type,
    workspace,
    session,
    **kwargs,
):
    # Only capture do commands for now because the undo might make it more difficult
    # to do analytics on the data.
    if action_command_type == ActionCommandType.DO:
        # We don't want to capture privacy sensitive information, and will therefore
        # remove those from the properties if they exist.
        properties = deepcopy(action_params)
        for param in action_type.privacy_sensitive_params:
            properties.pop(param, None)

        capture_event(
            user, action_type.type, properties, workspace=workspace, session=session
        )
