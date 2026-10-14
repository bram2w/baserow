"""
Follow-ups: something a user asked the agent to keep an eye on. Each one owns
its own schedule or row event, apart from the agent's triggers, that starts
a check with the agent's own configuration; the
check notifies the user and completes the follow-up once its criteria are met.
"""

import json
from datetime import timedelta
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.db.models import Exists, F, OuterRef, Q, QuerySet
from django.utils import timezone

from baserow.contrib.integrations.core.constants import (
    PERIODIC_INTERVAL_DAY,
    PERIODIC_INTERVAL_HOUR,
    PERIODIC_INTERVAL_MINUTE,
    PERIODIC_INTERVAL_WEEK,
)
from baserow.core.exceptions import PermissionDenied, PermissionException
from baserow.core.handler import CoreHandler
from baserow.core.models import WorkspaceUser

from .exceptions import AgentFollowUpDoesNotExist, AgentFollowUpInvalid
from .models import AgentApplication, AgentChat, AgentFollowUp

MAX_ACTIVE_FOLLOW_UPS_PER_USER = 10
DEFAULT_EXPIRY_DAYS = 30
MAX_EXPIRY_DAYS = 365
MAX_FAILED_CHECKS_IN_A_ROW = 3
MAX_WATCHED_ROWS = 50
# The trigger type of a check someone started by hand.
CHECK_NOW_TRIGGER_TYPE = "check_now"

# How often a scheduled follow-up checks, and how many checks a day that is,
# which the approval shows because every check costs tokens.
SCHEDULES = {
    "15_minutes": ({"interval": PERIODIC_INTERVAL_MINUTE, "minute": 15}, 96),
    "30_minutes": ({"interval": PERIODIC_INTERVAL_MINUTE, "minute": 30}, 48),
    "hour": ({"interval": PERIODIC_INTERVAL_HOUR}, 24),
    "day": ({"interval": PERIODIC_INTERVAL_DAY}, 1),
    "week": ({"interval": PERIODIC_INTERVAL_WEEK}, None),
}
ROW_WATCH_SERVICE_TYPES = {
    "rows_created": "local_baserow_rows_created",
    "rows_updated": "local_baserow_rows_updated",
    "rows_deleted": "local_baserow_rows_deleted",
}
WATCH_TYPES = ("schedule", *ROW_WATCH_SERVICE_TYPES)


def follow_up_is_visible_to(follow_up: AgentFollowUp, user) -> bool:
    """
    The details of a follow-up from a private conversation are only for the
    person who asked for it; others only see that it exists.
    """

    return not follow_up.private or follow_up.created_by_id == getattr(user, "id", None)


class AgentFollowUpHandler:
    # ------------------------------------------------------------------
    # Proposing and creating
    # ------------------------------------------------------------------

    def can_create(self, user, application: AgentApplication) -> bool:
        from .operations import CreateAgentFollowUpOperationType

        try:
            CoreHandler().check_permissions(
                user,
                CreateAgentFollowUpOperationType.type,
                workspace=application.workspace,
                context=application.application_ptr,
            )
        except PermissionException:
            return False
        return True

    def prepare_proposal(self, user, chat: AgentChat, values: dict) -> dict:
        """
        Validates what the agent proposes and resolves it into the values the
        approval shows and the follow-up is created from.

        :raises AgentFollowUpInvalid: With a message the agent can act on.
        """

        from baserow.contrib.database.table.models import Table
        from baserow.contrib.database.table.operations import (
            ReadDatabaseTableOperationType,
        )

        application = chat.agent.application
        if not self.can_create(user, application):
            raise AgentFollowUpInvalid(
                "This user's role doesn't allow creating follow-ups for this agent."
            )
        active = AgentFollowUp.objects.filter(
            application=application,
            created_by=user,
            status=AgentFollowUp.Status.ACTIVE,
        ).count()
        if active >= MAX_ACTIVE_FOLLOW_UPS_PER_USER:
            raise AgentFollowUpInvalid(
                f"The user already has {active} active follow-ups for this agent, "
                "the maximum. Ask them which one to cancel first."
            )

        texts = {}
        for key, limit in (
            ("title", 255),
            ("goal", 2000),
            ("check_instructions", 4000),
            ("done_when", 2000),
        ):
            text = str(values.get(key) or "").strip()
            if not text:
                raise AgentFollowUpInvalid(f"`{key}` is required.")
            texts[key] = text[:limit]

        watch_type = values.get("watch")
        if watch_type not in WATCH_TYPES:
            raise AgentFollowUpInvalid(f"`watch` must be one of {list(WATCH_TYPES)}.")
        if watch_type == "schedule":
            every = values.get("every")
            if every not in SCHEDULES:
                raise AgentFollowUpInvalid(
                    f"`every` must be one of {list(SCHEDULES)} for a schedule."
                )
            watch = {"type": "schedule", "every": every}
        else:
            table = (
                Table.objects.filter(
                    id=values.get("table_id"),
                    database__workspace_id=application.workspace_id,
                    database__trashed=False,
                )
                .select_related("database__workspace")
                .first()
            )
            if table is None:
                raise AgentFollowUpInvalid(
                    "`table_id` must be a table in this workspace."
                )
            try:
                CoreHandler().check_permissions(
                    user,
                    ReadDatabaseTableOperationType.type,
                    workspace=table.database.workspace,
                    context=table,
                )
            except PermissionException:
                raise AgentFollowUpInvalid("The user can't read that table.")
            row_ids = sorted({int(row_id) for row_id in values.get("row_ids") or []})[
                :MAX_WATCHED_ROWS
            ]
            if watch_type != "rows_created" and not row_ids:
                raise AgentFollowUpInvalid(
                    "Watching updated or deleted rows needs the `row_ids` to watch."
                )
            watch = {
                "type": watch_type,
                "table_id": table.id,
                "table_name": table.name,
                "row_ids": row_ids,
            }

        # Explicitly none means it keeps checking until it's done or stopped.
        if "expires_in_days" in values and values["expires_in_days"] is None:
            expires_in_days = None
        else:
            try:
                expires_in_days = int(values.get("expires_in_days") or 0)
            except (TypeError, ValueError):
                expires_in_days = 0
            expires_in_days = min(
                max(expires_in_days or DEFAULT_EXPIRY_DAYS, 1), MAX_EXPIRY_DAYS
            )

        return {
            **texts,
            "watch": watch,
            "state": str(values.get("state") or "").strip()[:4000],
            "expires_in_days": expires_in_days,
        }

    def create_follow_up(self, user, chat: AgentChat, values: dict) -> AgentFollowUp:
        """
        Creates the approved follow-up and the schedule or row event that
        starts its checks. It's the follow-up's own, so the agent's triggers
        stay as they are.
        Validated again, because the role or the number of active follow-ups
        may have changed while the approval waited.
        """

        from .realtime import broadcast_follow_up_updated

        prepared = self.prepare_proposal(user, chat, values)
        application = chat.agent.application
        watch = prepared["watch"]
        expires_in_days = prepared["expires_in_days"]

        with transaction.atomic():
            service = self._create_service(user, application, watch)
            follow_up = AgentFollowUp.objects.create(
                application=application,
                created_by=user,
                source_chat=chat,
                service=service,
                private=chat.private,
                title=prepared["title"],
                goal=prepared["goal"],
                check_instructions=prepared["check_instructions"],
                done_when=prepared["done_when"],
                watch=watch,
                state=prepared["state"],
                expires_on=(
                    timezone.now() + timedelta(days=expires_in_days)
                    if expires_in_days is not None
                    else None
                ),
            )
        transaction.on_commit(lambda: broadcast_follow_up_updated(follow_up))
        return follow_up

    def _create_service(self, user, application, watch: dict):
        """
        The follow-up's own schedule or row event, apart from the agent's
        triggers. Daily and weekly checks happen around the time it's created.
        """

        from .triggers.handler import AgentTriggerHandler

        now = timezone.now()
        if watch["type"] == "schedule":
            schedule, _ = SCHEDULES[watch["every"]]
            service_type = "periodic"
            service_values = {
                "timezone": "UTC",
                "minute": now.minute,
                "hour": now.hour,
                "day_of_week": now.weekday(),
                **schedule,
            }
        else:
            service_type = ROW_WATCH_SERVICE_TYPES[watch["type"]]
            service_values = {"table_id": watch["table_id"]}
        return AgentTriggerHandler().create_trigger_service(
            user, application, service_type, service_values
        )

    # ------------------------------------------------------------------
    # Reading and ending
    # ------------------------------------------------------------------

    def get_follow_up(
        self, follow_up_id: int, application: Optional[AgentApplication] = None
    ) -> AgentFollowUp:
        queryset = AgentFollowUp.objects.select_related(
            "application__workspace", "created_by", "source_chat"
        )
        if application is not None:
            queryset = queryset.filter(application=application)
        try:
            return queryset.get(id=follow_up_id)
        except AgentFollowUp.DoesNotExist:
            raise AgentFollowUpDoesNotExist(
                f"The follow-up with id {follow_up_id} does not exist."
            )

    def can_see_everyone(self, user, application: AgentApplication) -> bool:
        from .operations import ListAgentFollowUpsOperationType

        try:
            CoreHandler().check_permissions(
                user,
                ListAgentFollowUpsOperationType.type,
                workspace=application.workspace,
                context=application.application_ptr,
            )
        except PermissionException:
            return False
        return True

    def list_follow_ups(
        self, user, application: AgentApplication, status: Optional[str] = None
    ) -> QuerySet:
        """
        Everyone's follow-ups for those who manage them, otherwise only the
        user's own.

        :param status: `active`, `ended` or None for all of them.
        """

        queryset = AgentFollowUp.objects.filter(application=application).select_related(
            "created_by", "source_chat"
        )
        if not self.can_see_everyone(user, application):
            queryset = queryset.filter(created_by=user)
        if status == "active":
            queryset = queryset.filter(status=AgentFollowUp.Status.ACTIVE)
        elif status == "ended":
            queryset = queryset.exclude(status=AgentFollowUp.Status.ACTIVE)
        return queryset

    def check_can_manage(self, user, follow_up: AgentFollowUp) -> None:
        """
        Everybody may check or cancel their own follow-ups; those who manage
        the agent may do so with anyone's.

        :raises PermissionDenied: When the user may do neither.
        """

        from .operations import DeleteAgentFollowUpOperationType

        if follow_up.created_by_id == user.id:
            return
        application = follow_up.application
        CoreHandler().check_permissions(
            user,
            DeleteAgentFollowUpOperationType.type,
            workspace=application.workspace,
            context=application.application_ptr,
        )

    def cancel_follow_up(self, user, follow_up: AgentFollowUp) -> AgentFollowUp:
        self.check_can_manage(user, follow_up)
        if follow_up.created_by_id != user.id:
            outcome = f"Cancelled by {user.first_name}."
        else:
            outcome = "Cancelled."
        return self.end_follow_up(follow_up, AgentFollowUp.Status.CANCELLED, outcome)

    def resume_follow_up(self, user, follow_up: AgentFollowUp) -> AgentFollowUp:
        """
        Undoes stopping a follow-up: its schedule or row event is recreated
        from what it watched. Only while it would still be valid: not expired,
        and its creator still in the workspace with access to what it watches.

        :raises AgentFollowUpNotActive: When it can't be resumed.
        """

        from .exceptions import AgentFollowUpNotActive
        from .realtime import broadcast_follow_up_updated

        self.check_can_manage(user, follow_up)
        creator = follow_up.created_by
        if follow_up.status != AgentFollowUp.Status.CANCELLED:
            raise AgentFollowUpNotActive("Only a stopped follow-up can be resumed.")
        if follow_up.expires_on is not None and follow_up.expires_on <= timezone.now():
            raise AgentFollowUpNotActive("The follow-up expired in the meantime.")
        if (
            creator is None
            or not creator.is_active
            or not WorkspaceUser.objects.filter(
                workspace_id=follow_up.application.workspace_id, user=creator
            ).exists()
        ):
            raise AgentFollowUpNotActive("Its creator is no longer in the workspace.")

        with transaction.atomic():
            follow_up.service = self._create_service(
                creator, follow_up.application, follow_up.watch
            )
            follow_up.status = AgentFollowUp.Status.ACTIVE
            follow_up.outcome = ""
            follow_up.ended_on = None
            follow_up.save(
                update_fields=["service", "status", "outcome", "ended_on", "updated_on"]
            )
        transaction.on_commit(lambda: broadcast_follow_up_updated(follow_up))
        return follow_up

    def end_follow_up(
        self, follow_up: AgentFollowUp, status: str, outcome: str = ""
    ) -> AgentFollowUp:
        """
        Ends an active follow-up: its schedule or row event is removed, the
        follow-up itself is kept as a record of what happened.
        """

        from baserow.core.services.handler import ServiceHandler
        from baserow.core.services.models import Service

        from .realtime import broadcast_follow_up_updated

        with transaction.atomic():
            # Locked so a check completing it and a user cancelling it at the
            # same moment end it once.
            locked = (
                AgentFollowUp.objects.select_for_update(of=("self",))
                .filter(id=follow_up.id, status=AgentFollowUp.Status.ACTIVE)
                .first()
            )
            if locked is None:
                follow_up.refresh_from_db()
                return follow_up
            service = Service.objects.filter(id=locked.service_id).first()
            locked.status = status
            locked.outcome = outcome[:4000]
            locked.ended_on = timezone.now()
            locked.service = None
            locked.save(
                update_fields=["status", "outcome", "ended_on", "service", "updated_on"]
            )
            if service is not None:
                service = service.specific
                ServiceHandler().delete_service(service.get_type(), service)

        for field in ("status", "outcome", "ended_on", "service_id", "updated_on"):
            setattr(follow_up, field, getattr(locked, field))
        transaction.on_commit(lambda: broadcast_follow_up_updated(follow_up))
        return follow_up

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def filter_event_payload(self, follow_up: AgentFollowUp, payload):
        """
        A row event only concerns the follow-up when it contains a watched
        row, and the check only gets to see those rows.

        :return: The payload narrowed to the watched rows, or None when the
            event doesn't concern the follow-up.
        """

        row_ids = set((follow_up.watch or {}).get("row_ids") or [])
        if not row_ids or not isinstance(payload, dict):
            return payload
        results = [
            row
            for row in payload.get("results") or []
            if isinstance(row, dict) and row.get("id") in row_ids
        ]
        if not results:
            return None
        return {**payload, "results": results}

    def is_checking(self, follow_up: AgentFollowUp) -> bool:
        # A slow check must not be overtaken by the next one, which would
        # notify twice about the same change.
        return follow_up.chats.filter(
            status__in=[
                AgentChat.Status.IN_PROGRESS,
                AgentChat.Status.CANCELING,
                AgentChat.Status.AWAITING_APPROVAL,
            ]
        ).exists()

    def check_now(self, user, follow_up: AgentFollowUp) -> AgentChat:
        """
        Checks the follow-up right away instead of waiting for its schedule or
        row event. The conversation is kept, also when nothing changed, so the
        person who asked sees the outcome.

        :raises AgentFollowUpNotActive: When it ended or is being checked.
        """

        from .exceptions import AgentFollowUpNotActive

        self.check_can_manage(user, follow_up)
        if not follow_up.is_active:
            raise AgentFollowUpNotActive("The follow-up has ended.")
        if self.is_checking(follow_up):
            raise AgentFollowUpNotActive("The follow-up is being checked already.")
        chat = self.start_check(follow_up, CHECK_NOW_TRIGGER_TYPE, None)
        if chat is None:
            raise AgentFollowUpNotActive("The follow-up has ended.")
        return chat

    def start_check(self, follow_up: AgentFollowUp, trigger_type, event_payload):
        """
        Starts a conversation checking the follow-up, owned by the user who
        asked for it so the agent works within their access.
        """

        from .handler import AgentChatHandler
        from .models import AgentChatMessage

        if follow_up.expires_on is not None and follow_up.expires_on <= timezone.now():
            self.end_follow_up(
                follow_up,
                AgentFollowUp.Status.EXPIRED,
                "Stopped checking because it expired.",
            )
            self.notify_ended(follow_up)
            return None
        if follow_up.created_by is None or self.is_checking(follow_up):
            return None

        chat_handler = AgentChatHandler()
        main_agent = follow_up.application.agents.first()
        chat = AgentChat.objects.create(
            agent=main_agent,
            source=AgentChat.Source.FOLLOW_UP,
            trigger_type=trigger_type,
            event_payload=event_payload,
            user=follow_up.created_by,
            private=follow_up.private,
            follow_up=follow_up,
            title=f"Follow-up: {follow_up.title}"[: AgentChat.TITLE_MAX_LENGTH],
        )
        message = chat_handler.create_message(
            chat,
            AgentChatMessage.Role.SYSTEM,
            self.get_check_prompt(follow_up, event_payload),
        )
        chat_handler.start_chat_run(chat, message)
        return chat

    def get_check_prompt(self, follow_up: AgentFollowUp, event_payload) -> str:
        from .triggers.registries import _EVENT_PAYLOAD_PROMPT_LIMIT

        lines = [
            f'Follow-up check: "{follow_up.title}".',
            f"{follow_up.created_by.first_name} asked you to keep an eye on "
            f"something. Why: {follow_up.goal}",
            "",
            f"What to check: {follow_up.check_instructions}",
            f"It is done when: {follow_up.done_when}",
            "What you remembered after the previous check: "
            + (follow_up.state or "(nothing yet)"),
            f"Previous checks: {follow_up.checks_count}.",
            "",
            "Do the check with your tools. Then:",
            "- Nothing relevant changed: only update what you remember with "
            "`remember_follow_up_state` when that helps the next check, and "
            "stop without notifying.",
            "- Something the user wants to know about happened: tell them with "
            "`notify_user`, and remember the new situation.",
            "- The criteria are met: notify the user, then call `complete_follow_up`.",
            "- It can't be checked anymore (e.g. the thing no longer exists): "
            "notify the user why, then complete it.",
        ]
        if event_payload is not None:
            payload_json = json.dumps(event_payload, default=str)
            if len(payload_json) > _EVENT_PAYLOAD_PROMPT_LIMIT:
                payload_json = (
                    payload_json[:_EVENT_PAYLOAD_PROMPT_LIMIT] + "… (truncated)"
                )
            lines += ["", f"Event data:\n```json\n{payload_json}\n```"]
        return "\n".join(lines)

    def remember_state(self, follow_up: AgentFollowUp, state: str) -> None:
        from .realtime import broadcast_follow_up_updated

        follow_up.state = state[:4000]
        follow_up.save(update_fields=["state", "updated_on"])
        broadcast_follow_up_updated(follow_up)

    def notify_user(
        self, follow_up: AgentFollowUp, chat: AgentChat, message: str
    ) -> None:
        from .notification_types import AgentFollowUpNotificationType

        if follow_up.created_by is None:
            return
        AgentFollowUpNotificationType.notify(follow_up, chat, message)
        AgentFollowUp.objects.filter(id=follow_up.id).update(
            notifications_count=F("notifications_count") + 1
        )

    def notify_ended(self, follow_up: AgentFollowUp) -> None:
        """Lets the user know a follow-up stopped without completing."""

        from .notification_types import AgentFollowUpNotificationType

        if follow_up.created_by is not None:
            AgentFollowUpNotificationType.notify(follow_up, None, follow_up.outcome)

    def finish_check(
        self, chat: AgentChat, notified: bool, ended: bool
    ) -> Optional[AgentFollowUp]:
        """
        Books a finished check. A check that found nothing worth telling
        leaves no conversation behind, so the list isn't filled with them;
        its usage is counted already. Failing checks are kept, and too many
        in a row stop the follow-up.

        :param notified: Whether the check notified the user.
        :param ended: Whether the check completed the follow-up.
        """

        from .handler import AgentChatHandler
        from .realtime import broadcast_follow_up_updated

        follow_up = AgentFollowUp.objects.filter(id=chat.follow_up_id).first()
        if follow_up is None:
            return None
        failed = chat.status == AgentChat.Status.ERROR
        AgentFollowUp.objects.filter(id=follow_up.id).update(
            checks_count=F("checks_count") + 1,
            last_checked_on=timezone.now(),
            failed_checks_in_a_row=(F("failed_checks_in_a_row") + 1) if failed else 0,
        )
        follow_up.refresh_from_db()

        if failed and follow_up.failed_checks_in_a_row >= MAX_FAILED_CHECKS_IN_A_ROW:
            self.end_follow_up(
                follow_up,
                AgentFollowUp.Status.FAILED,
                f"Stopped after {follow_up.failed_checks_in_a_row} checks in a "
                "row failed.",
            )
            self.notify_ended(follow_up)
        elif (
            not (failed or notified or ended)
            and chat.status == AgentChat.Status.IDLE
            and chat.trigger_type != CHECK_NOW_TRIGGER_TYPE
        ):
            AgentChatHandler().delete_chat(chat)
        broadcast_follow_up_updated(follow_up)
        return follow_up

    def add_usage(
        self,
        follow_up_id: int,
        input_tokens: int,
        output_tokens: int,
        cost: Optional[Decimal],
    ) -> None:
        AgentFollowUp.objects.filter(id=follow_up_id).update(
            total_input_tokens=F("total_input_tokens") + input_tokens,
            total_output_tokens=F("total_output_tokens") + output_tokens,
            total_cost=F("total_cost") + (cost or 0),
            unpriced_turns=F("unpriced_turns") + (0 if cost is not None else 1),
        )

    # ------------------------------------------------------------------
    # Clean up
    # ------------------------------------------------------------------

    def end_stale_follow_ups(self) -> int:
        """
        Ends the follow-ups that expired, whose agent is gone, or whose
        creator is no longer in the workspace, so nobody is notified about
        something they can no longer see.

        :return: How many follow-ups were ended.
        """

        now = timezone.now()
        active = AgentFollowUp.objects.filter(
            status=AgentFollowUp.Status.ACTIVE
        ).select_related("created_by", "application")
        expired = list(active.filter(expires_on__lte=now))
        for follow_up in expired:
            self.end_follow_up(
                follow_up,
                AgentFollowUp.Status.EXPIRED,
                "Stopped checking because it expired.",
            )
            self.notify_ended(follow_up)

        is_member = Exists(
            WorkspaceUser.objects.filter(
                workspace_id=OuterRef("application__workspace_id"),
                user_id=OuterRef("created_by_id"),
            )
        )
        orphaned = list(
            active.exclude(id__in=[follow_up.id for follow_up in expired]).filter(
                Q(created_by__isnull=True) | Q(created_by__is_active=False) | ~is_member
            )
        )
        for follow_up in orphaned:
            self.end_follow_up(
                follow_up,
                AgentFollowUp.Status.CANCELLED,
                "Cancelled because its creator is no longer in the workspace.",
            )
        return len(expired) + len(orphaned)


def check_can_see(user, follow_up: AgentFollowUp) -> None:
    """
    :raises PermissionDenied: When it's someone else's follow-up and the user
        doesn't manage follow-ups.
    """

    if follow_up.created_by_id == getattr(user, "id", None):
        return
    if not AgentFollowUpHandler().can_see_everyone(user, follow_up.application):
        raise PermissionDenied()
