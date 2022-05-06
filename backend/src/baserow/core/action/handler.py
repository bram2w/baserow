import logging
import traceback
from copy import deepcopy
from typing import List, Optional

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from baserow.core.action.models import Action
from baserow.core.action.registries import action_type_registry, ActionScopeStr

logger = logging.getLogger(__name__)


def scopes_to_q_filter(scopes: List[ActionScopeStr]):
    q = Q()
    for scope_str in scopes:
        q |= Q(scope=scope_str)
    return q


class ActionHandler:
    """
    Contains methods to do high level operations on ActionType's like undoing or
    redoing them.
    """

    @classmethod
    def undo(
        cls, user: AbstractUser, scopes: List[ActionScopeStr], session: str
    ) -> Optional[Action]:
        # Un-set the web_socket_id so the user doing this undo will receive any
        # events triggered by the action.
        user.web_socket_id = None

        latest_not_undone_action = (
            Action.objects.filter(user=user, undone_at__isnull=True, session=session)
            .filter(scopes_to_q_filter(scopes))
            .order_by("-created_on", "-id")
            .select_for_update()
            .first()
        )
        if latest_not_undone_action is None:
            return None

        action_being_undone = latest_not_undone_action
        action_being_undone.error = None
        # noinspection PyBroadException
        try:
            # Wrap with an inner transaction to ensure any errors get rolled back.
            with transaction.atomic():
                action_type = action_type_registry.get(latest_not_undone_action.type)
                latest_params = action_type.Params(
                    **deepcopy(latest_not_undone_action.params)
                )

                action_type.undo(user, latest_params, action_being_undone)
        except Exception:
            tb = traceback.format_exc()
            logger.error(
                f"Undoing {latest_not_undone_action} failed because of: \n{tb}"
            )
            latest_not_undone_action.error = tb
        finally:
            latest_not_undone_action.undone_at = timezone.now()
            latest_not_undone_action.save()
        return latest_not_undone_action

    @classmethod
    def redo(
        cls, user: AbstractUser, scopes: List[ActionScopeStr], session: str
    ) -> Optional[Action]:
        # Un-set the web_socket_id so the user doing this redo will receive any
        # events triggered by the action.
        user.web_socket_id = None

        scopes_filter = scopes_to_q_filter(scopes)
        latest_undone_action = (
            Action.objects.filter(user=user, undone_at__isnull=False, session=session)
            .filter(scopes_filter)
            .order_by("-undone_at", "-id")
            .select_for_update()
            .first()
        )

        if latest_undone_action is None:
            return None

        normal_action_happened_since_undo = (
            Action.objects.filter(
                user=user,
                created_on__gt=latest_undone_action.undone_at,
                undone_at__isnull=True,
            )
            .filter(scopes_filter)
            .exists()
        )
        if normal_action_happened_since_undo:
            return None

        if latest_undone_action.error:
            # We are redoing an undo action that failed and so we have nothing to redo
            # However we mark it as redone so the user can try undo again
            # to see if it works this time.
            latest_undone_action.undone_at = None
            latest_undone_action.save()
        else:
            action_being_redone = latest_undone_action
            # noinspection PyBroadException
            try:
                # Wrap with an inner transaction to ensure any errors get rolled back.
                with transaction.atomic():
                    action_type = action_type_registry.get(latest_undone_action.type)
                    latest_params = action_type.Params(
                        **deepcopy(latest_undone_action.params)
                    )
                    action_type.redo(user, latest_params, action_being_redone)
            except Exception:
                tb = traceback.format_exc()
                logger.error(
                    f"Redoing {normal_action_happened_since_undo} failed because of: \n"
                    f"{tb}",
                )
                latest_undone_action.error = tb
            finally:
                latest_undone_action.undone_at = None
                latest_undone_action.save()

        return latest_undone_action
