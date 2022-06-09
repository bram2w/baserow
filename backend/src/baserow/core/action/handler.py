import logging
import traceback
from copy import deepcopy
from datetime import datetime
from typing import List, Optional, Set, Tuple

from django.conf import settings
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
            .select_for_update(of=("self",))
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
                # noinspection PyArgumentList
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
            .select_for_update(of=("self",))
            .first()
        )

        if latest_undone_action is None:
            return None

        normal_action_happened_since_undo = (
            Action.objects.filter(
                user=user,
                created_on__gt=latest_undone_action.undone_at,
                undone_at__isnull=True,
                session=session,
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
                    # noinspection PyArgumentList
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

    @classmethod
    def clean_up_old_actions(cls):
        """
        Any actions which haven't been updated in
        settings.MINUTES_UNTIL_ACTION_CLEANED_UP will be deleted any have an extra
        data associated with them cleaned up.
        """

        now = timezone.now()
        minutes = int(settings.MINUTES_UNTIL_ACTION_CLEANED_UP)
        cutoff = now - timezone.timedelta(minutes=minutes)

        types_with_custom_clean_up = set()
        for action_type in action_type_registry.get_all():
            if action_type.has_custom_cleanup():
                types_with_custom_clean_up.add(action_type.type)

        # Delete in a separate atomic block so if we crash later we don't roll back
        # these valid deletes.
        with transaction.atomic():
            # Here we delete all actions which have a type which doesn't have a custom
            # `clean_up_any_extra_action_data` implementation. This means that all
            # we need to do to clean them up is delete the actions, which we can do
            # in a single DELETE WHERE query.
            bulk_delete_count, _ = (
                Action.objects.filter(updated_on__lte=cutoff)
                .exclude(type__in=types_with_custom_clean_up)
                .delete()
            )

        (
            custom_deleted_count,
            cleanup_error,
        ) = cls._cleanup_actions_with_custom_cleanup_logic(
            cutoff, types_with_custom_clean_up
        )
        total_deleted = bulk_delete_count + custom_deleted_count

        logger.info(f"Cleaned up {total_deleted} actions.")

        if cleanup_error:
            logger.error("However an error was encountered during an action cleanup: ")
            raise cleanup_error

    @classmethod
    def _cleanup_actions_with_custom_cleanup_logic(
        cls, cutoff: datetime, types_with_custom_clean_up: Set[str]
    ) -> Tuple[int, Optional[Exception]]:
        """
        ActionTypes can implement a custom clean_up_any_extra_action_data method to
        clean up any extra data associated with them. This method will loop over all
        of those actions calling their custom clean_up_any_extra_action_data method
        and deleting the action.

        :param cutoff: Any actions updated on or before this time will be cleaned up.
        :param types_with_custom_clean_up: The set of ActionType.type names which
            have custom clean_up_any_extra_action_data methods which need to be
            called to do some extra per type cleanup.
        :return: A tuple of the number of deleted actions and an optional Exception
            which is present when a custom cleanup failed.
        """

        with transaction.atomic():
            actions_to_cleanup_with_custom_logic = (
                Action.objects.filter(
                    updated_on__lte=cutoff, type__in=types_with_custom_clean_up
                )
                .select_for_update(of=("self",))
                .order_by("updated_on", "id")
            )
            deleted_count = 0
            for action in actions_to_cleanup_with_custom_logic:
                try:
                    with transaction.atomic():
                        # Run each clean up in a single inside its own atomic block so
                        # later cleanup for different action fails we don't roll back
                        # previous successful clean ups.
                        action_type = action_type_registry.get(action.type)
                        action_type.clean_up_any_extra_action_data(action)
                        action.delete()
                        deleted_count += 1
                except Exception as e:
                    # We don't want to roll back the entire transaction if one of the
                    # cleanup's failed. The failed cleanup has already been rolled
                    # back due to its own inner atomic block so we can safely stop
                    # , commit the outer transaction which persists the successful
                    # cleanups and let the caller decide what to do with the error.
                    return deleted_count, e

        return deleted_count, None
