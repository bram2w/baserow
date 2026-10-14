import uuid

from django.contrib.auth import get_user_model
from django.db import models

from baserow.core.mixins import (
    BigAutoFieldMixin,
    CreatedAndUpdatedOnMixin,
    HierarchicalModelMixin,
    TrashableModelMixin,
)
from baserow.core.models import Agent, Application
from baserow.core.services.models import Service

User = get_user_model()

__all__ = [
    "AgentApplication",
    "AgentDefinition",
    "AgentTrigger",
    "AgentTool",
    "AgentChatChannel",
    "AgentChat",
    "AgentChatMessage",
    "AgentChatToolApproval",
    "AgentUsage",
    "AgentFollowUp",
]


class AgentChatMinRole(models.TextChoices):
    EDITOR = "EDITOR", "Editors and up"
    BUILDER = "BUILDER", "Builders and up"
    ADMIN = "ADMIN", "Admins"
    NOBODY = "NOBODY", "Nobody"


class AgentApplication(Application):
    description = models.TextField(
        blank=True,
        db_default="",
        help_text="What the agent should do, used to AI-configure the agent.",
    )
    agent_identity = models.ForeignKey(
        Agent,
        null=True,
        blank=True,
        default=None,
        db_default=None,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=(
            "The workspace agent subject this application acts as. Without one "
            "the agent has no access to the workspace."
        ),
    )
    act_as_user = models.BooleanField(
        default=False,
        db_default=False,
        help_text=(
            "Acts on behalf of the Baserow user who started or continued the "
            "conversation instead of an agent identity. Conversations without "
            "such a user get no workspace access."
        ),
    )
    start_chat_min_role = models.CharField(
        max_length=16,
        choices=AgentChatMinRole.choices,
        default=AgentChatMinRole.EDITOR,
        db_default=AgentChatMinRole.EDITOR,
        help_text="The minimum role needed to start a conversation in Baserow.",
    )
    continue_chat_min_role = models.CharField(
        max_length=16,
        choices=AgentChatMinRole.choices,
        default=AgentChatMinRole.EDITOR,
        db_default=AgentChatMinRole.EDITOR,
        help_text=(
            "The minimum role needed to continue a conversation that a trigger started."
        ),
    )
    follow_up_min_role = models.CharField(
        max_length=16,
        choices=AgentChatMinRole.choices,
        default=AgentChatMinRole.BUILDER,
        db_default=AgentChatMinRole.BUILDER,
        help_text="The minimum role needed to have the agent create a follow-up.",
    )

    def get_parent(self):
        # Parent is the Application here even if it's at the "same" level
        # but it's a more generic type
        return self.application_ptr


class AgentDefinition(
    HierarchicalModelMixin,
    CreatedAndUpdatedOnMixin,
    models.Model,
):
    """
    The configuration of a single agent within an agent application. An
    application holds exactly one agent for now; the separate table exists so
    that sub agents can later become additional rows with a parent relation.
    """

    application = models.ForeignKey(
        AgentApplication,
        on_delete=models.CASCADE,
        related_name="agents",
    )
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True, db_default="")
    instructions = models.TextField(blank=True, db_default="")
    memory = models.TextField(
        blank=True,
        db_default="",
        help_text=(
            "Persistent notes loaded into every run. Written by the agent "
            "itself (e.g. ids of things it created, lessons learned) and "
            "editable by users to teach the agent."
        ),
    )
    ai_generative_ai_type = models.CharField(
        max_length=32, null=True, blank=True, db_default=None
    )
    ai_generative_ai_model = models.CharField(
        max_length=128, null=True, blank=True, db_default=None
    )
    ai_temperature = models.FloatField(null=True, blank=True, db_default=None)

    class Meta:
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=["application"],
                name="unique_agent_definition_per_application",
            )
        ]

    def get_parent(self):
        return self.application


class AgentSkill(models.Model):
    """
    A workspace skill an agent follows. "Always" inlines the skill's content
    into every prompt; "on demand" only lists its name and description and
    lets the agent load the content with a tool when it decides it applies.
    """

    class Mode(models.TextChoices):
        ALWAYS = "always", "Always"
        ON_DEMAND = "on_demand", "On demand"

    agent = models.ForeignKey(
        AgentDefinition, on_delete=models.CASCADE, related_name="agent_skills"
    )
    skill = models.ForeignKey(
        "core.WorkspaceSkill", on_delete=models.CASCADE, related_name="agent_skills"
    )
    mode = models.CharField(
        max_length=16,
        choices=Mode.choices,
        default=Mode.ALWAYS,
        db_default=Mode.ALWAYS,
    )
    order = models.PositiveIntegerField(default=0, db_default=0)

    class Meta:
        ordering = ("order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["agent", "skill"], name="unique_agent_skill"
            )
        ]


class AgentTrigger(
    HierarchicalModelMixin, CreatedAndUpdatedOnMixin, TrashableModelMixin, models.Model
):
    """
    Connects an agent application to a trigger service. The trigger's service
    type determines when a new agent chat is started automatically. An
    application can have multiple triggers.
    """

    application = models.ForeignKey(
        AgentApplication,
        on_delete=models.CASCADE,
        related_name="triggers",
    )
    service = models.OneToOneField(
        Service,
        on_delete=models.CASCADE,
        related_name="agent_trigger",
    )
    enabled = models.BooleanField(default=True, db_default=True)
    # Options of the trigger type itself (e.g. "only when mentioned" for row
    # comments), as opposed to the service's configuration.
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("id",)

    def get_parent(self):
        return self.application


class AgentTool(
    HierarchicalModelMixin, CreatedAndUpdatedOnMixin, TrashableModelMixin, models.Model
):
    """
    A tool enabled for an agent. The `type` refers to an agent tool type in
    the registry; service-backed tools additionally point at a configured
    service that is dispatched when the model calls the tool.
    """

    agent = models.ForeignKey(
        AgentDefinition,
        on_delete=models.CASCADE,
        related_name="tools",
    )
    type = models.CharField(max_length=64)
    name = models.CharField(max_length=160, blank=True, db_default="")
    config = models.JSONField(default=dict, blank=True, db_default={})
    service = models.OneToOneField(
        Service,
        null=True,
        blank=True,
        default=None,
        db_default=None,
        on_delete=models.SET_NULL,
        related_name="agent_tool",
    )
    identity = models.ForeignKey(
        Agent,
        null=True,
        blank=True,
        default=None,
        db_default=None,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=(
            "The workspace agent this tool acts as instead of the application's "
            "identity."
        ),
    )
    act_as_user = models.BooleanField(
        default=False,
        db_default=False,
        help_text=(
            "Acts on behalf of the Baserow user of the conversation instead of "
            "the application's identity. Unavailable without such a user."
        ),
    )
    order = models.PositiveIntegerField(default=1, db_default=1)

    class Meta:
        ordering = ("order", "id")

    def get_parent(self):
        return self.agent


class AgentChatChannel(
    HierarchicalModelMixin, CreatedAndUpdatedOnMixin, TrashableModelMixin, models.Model
):
    """
    Connects an agent application to an external chat surface (e.g. Slack)
    through which conversations with the agent can be started. The `type`
    refers to a chat channel type in the registry; the config holds the
    type-specific credentials.
    """

    application = models.ForeignKey(
        AgentApplication,
        on_delete=models.CASCADE,
        related_name="chat_channels",
    )
    type = models.CharField(max_length=64)
    name = models.CharField(max_length=160, blank=True, db_default="")
    config = models.JSONField(default=dict, blank=True, db_default={})
    enabled = models.BooleanField(default=True, db_default=True)
    uid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unguessable token identifying this channel's inbound webhook URL.",
    )

    class Meta:
        ordering = ("id",)

    def get_parent(self):
        return self.application


class AgentChat(
    BigAutoFieldMixin,
    HierarchicalModelMixin,
    CreatedAndUpdatedOnMixin,
    models.Model,
):
    """
    A conversation with an agent. Started manually by a user, by a trigger
    event, by an external chat channel, or by the AI-assisted setup of the
    agent.
    """

    TITLE_MAX_LENGTH = 250

    class Status(models.TextChoices):
        IDLE = "idle", "Idle"
        IN_PROGRESS = "in_progress", "In progress"
        CANCELING = "canceling", "Canceling"
        # The run is paused on tool calls waiting in the approval queue.
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting approval"
        ERROR = "error", "Error"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        TRIGGER = "trigger", "Trigger"
        SETUP = "setup", "Setup"
        CHANNEL = "channel", "Channel"
        # Started by a "Run agent" service: a button, an automation, an
        # application builder action or another agent's tool call.
        SERVICE = "service", "Service"
        # A check of a follow-up, owned by the user who asked for it.
        FOLLOW_UP = "follow_up", "Follow-up"

    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    agent = models.ForeignKey(
        AgentDefinition,
        on_delete=models.CASCADE,
        related_name="chats",
    )
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        default=None,
        db_default=None,
        on_delete=models.SET_NULL,
        help_text="The user who started the chat. Null for triggered chats.",
    )
    title = models.CharField(max_length=TITLE_MAX_LENGTH, blank=True, db_default="")
    pinned = models.BooleanField(default=False, db_default=False)
    private = models.BooleanField(
        default=False,
        db_default=False,
        help_text="Only the user who started a private conversation can see it.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IDLE,
        db_default=Status.IDLE,
    )
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.MANUAL,
        db_default=Source.MANUAL,
    )
    trigger_type = models.CharField(max_length=64, blank=True, db_default="")
    event_payload = models.JSONField(null=True, blank=True, db_default=None)
    parent_chat = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        default=None,
        db_default=None,
        on_delete=models.SET_NULL,
        related_name="child_chats",
        help_text=(
            "The conversation whose agent started this one through a tool "
            "call, when another agent did."
        ),
    )
    channel = models.ForeignKey(
        AgentChatChannel,
        null=True,
        blank=True,
        default=None,
        db_default=None,
        on_delete=models.SET_NULL,
        related_name="chats",
        help_text="The external chat channel this conversation belongs to.",
    )
    follow_up = models.ForeignKey(
        "AgentFollowUp",
        null=True,
        blank=True,
        default=None,
        db_default=None,
        on_delete=models.SET_NULL,
        related_name="chats",
        help_text="The follow-up this conversation is a check of.",
    )
    channel_session_key = models.CharField(
        max_length=255,
        blank=True,
        db_default="",
        help_text=(
            "Channel specific session identifier (e.g. Slack channel/thread) "
            "used to continue the same conversation across messages."
        ),
    )
    started_on = models.DateTimeField(null=True, blank=True, db_default=None)
    completed_on = models.DateTimeField(null=True, blank=True, db_default=None)
    error = models.TextField(blank=True, db_default="")
    message_history = models.BinaryField(
        null=True,
        blank=True,
        help_text=(
            "Serialized pydantic-ai message history (JSON bytes) for "
            "multi-turn conversation context."
        ),
    )
    total_input_tokens = models.BigIntegerField(default=0, db_default=0)
    total_cached_input_tokens = models.BigIntegerField(
        default=0,
        db_default=0,
        help_text="The part of the input the provider read from its cache.",
    )
    total_output_tokens = models.BigIntegerField(default=0, db_default=0)
    total_cost = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        default=0,
        db_default=0,
        help_text="The cost in USD of the turns with a known model price.",
    )
    unpriced_turns = models.PositiveIntegerField(
        default=0,
        db_default=0,
        help_text="Turns whose model has no known price, so their cost is missing.",
    )

    class Meta:
        indexes = [
            # The conversation list: pinned first, newest first, per agent.
            models.Index(
                fields=["agent", "-pinned", "-updated_on"],
                name="agent_chat_list_idx",
            ),
            models.Index(fields=["agent", "status"]),
            models.Index(fields=["channel", "channel_session_key"]),
            # "Last run" of an application: the newest finished trigger chat.
            models.Index(
                fields=["agent", "-completed_on"],
                condition=models.Q(source="trigger"),
                name="agent_chat_last_run_idx",
            ),
        ]

    def get_parent(self):
        return self.agent

    @property
    def is_running(self) -> bool:
        return self.status in (self.Status.IN_PROGRESS, self.Status.CANCELING)

    @property
    def is_awaiting_approval(self) -> bool:
        return self.status == self.Status.AWAITING_APPROVAL


class AgentChatMessage(
    BigAutoFieldMixin,
    HierarchicalModelMixin,
    CreatedAndUpdatedOnMixin,
    models.Model,
):
    class Role(models.TextChoices):
        HUMAN = "human", "Human"
        AI = "ai", "AI"
        # System messages carry the trigger's opening prompt so the full
        # context of a triggered run is visible in the history.
        SYSTEM = "system", "System"

    chat = models.ForeignKey(
        AgentChat,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    artifacts = models.JSONField(
        default=dict,
        blank=True,
        db_default={},
        help_text="Structured extras such as tool calls and reasoning.",
    )
    attachments = models.JSONField(
        default=list,
        blank=True,
        db_default=[],
        help_text=(
            "User files attached to this message, as a list of dicts with at "
            "least the stored user file `name`. The files are injected into "
            "the model prompt of the turn this message starts."
        ),
    )
    input_tokens = models.IntegerField(null=True, blank=True, db_default=None)
    cached_input_tokens = models.IntegerField(
        null=True,
        blank=True,
        db_default=None,
        help_text="The part of the input the provider read from its cache.",
    )
    output_tokens = models.IntegerField(null=True, blank=True, db_default=None)
    cost = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        db_default=None,
        help_text="The cost in USD, or null when the model has no known price.",
    )

    class Meta:
        ordering = ("id",)

    def get_parent(self):
        return self.chat


class AgentChatToolApproval(
    BigAutoFieldMixin,
    HierarchicalModelMixin,
    CreatedAndUpdatedOnMixin,
    models.Model,
):
    """
    A tool call that paused an agent run because it changes data and the tool
    is configured to require approval. The run resumes once every pending
    approval of the chat has been decided.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    chat = models.ForeignKey(
        AgentChat,
        on_delete=models.CASCADE,
        related_name="tool_approvals",
    )
    message = models.ForeignKey(
        AgentChatMessage,
        null=True,
        blank=True,
        default=None,
        db_default=None,
        on_delete=models.SET_NULL,
        related_name="tool_approvals",
        help_text="The AI message during which the tool call was requested.",
    )
    tool_call_id = models.CharField(max_length=255)
    tool_name = models.CharField(max_length=255)
    tool_args = models.JSONField(null=True, blank=True, db_default=None)
    preview = models.JSONField(
        null=True,
        blank=True,
        db_default=None,
        help_text=(
            "A human-readable rendering of what the call will do (resolved "
            "service fields, rows to write), built when the approval is recorded."
        ),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_default=Status.PENDING,
    )
    decided_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        default=None,
        db_default=None,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    decided_at = models.DateTimeField(null=True, blank=True, db_default=None)
    reason = models.TextField(
        blank=True,
        db_default="",
        help_text="Optional rejection reason, returned to the model.",
    )

    class Meta:
        ordering = ("id",)
        indexes = [
            models.Index(fields=["chat", "status"]),
            # Pending approvals are rare and counted per application on every
            # application listing; the partial index keeps that a tiny scan.
            models.Index(
                fields=["chat"],
                condition=models.Q(status="pending"),
                name="agent_approval_pending_idx",
            ),
        ]

    def get_parent(self):
        return self.chat


class AgentEmailMessage(models.Model):
    """
    One email that went through an email chat channel, in either direction.
    It is the index that maps a reply to its conversation (by Message-ID,
    thread id, or sender and subject) and the record of what was said.
    """

    class Direction(models.TextChoices):
        INBOUND = "inbound"
        OUTBOUND = "outbound"

    channel = models.ForeignKey(
        AgentChatChannel, on_delete=models.CASCADE, related_name="email_messages"
    )
    # The `AgentChat.channel_session_key` of the conversation.
    session_key = models.CharField(max_length=255)
    direction = models.CharField(max_length=8, choices=Direction.choices)
    message_id = models.CharField(max_length=998, blank=True, db_default="")
    in_reply_to = models.CharField(max_length=998, blank=True, db_default="")
    references = models.JSONField(default=list, blank=True, db_default=[])
    # The provider's thread id (Gmail thread, Outlook conversation), when
    # the mailbox has one.
    thread_key = models.CharField(max_length=255, blank=True, db_default="")
    # The provider's own id of the message, needed to reply through its API.
    provider_message_id = models.CharField(max_length=255, blank=True, db_default="")
    from_address = models.CharField(max_length=320, blank=True, db_default="")
    from_name = models.CharField(max_length=255, blank=True, db_default="")
    to_addresses = models.JSONField(default=list, blank=True, db_default=[])
    subject = models.CharField(max_length=998, blank=True, db_default="")
    subject_normalized = models.CharField(max_length=998, blank=True, db_default="")
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("id",)
        indexes = [
            models.Index(fields=["channel", "session_key"]),
            models.Index(fields=["channel", "message_id"]),
            models.Index(fields=["channel", "thread_key"]),
            models.Index(fields=["channel", "from_address", "subject_normalized"]),
        ]


class AgentUsage(models.Model):
    """
    The token usage and cost of an agent application per hour. It's kept apart
    from the conversations so the totals survive their deletion, and hours let
    the periods follow the viewer's timezone.
    """

    application = models.ForeignKey(
        AgentApplication, on_delete=models.CASCADE, related_name="usage"
    )
    hour = models.DateTimeField(help_text="The start of the hour, in UTC.")
    input_tokens = models.BigIntegerField(default=0, db_default=0)
    cached_input_tokens = models.BigIntegerField(
        default=0,
        db_default=0,
        help_text="The part of the input the provider read from its cache.",
    )
    output_tokens = models.BigIntegerField(default=0, db_default=0)
    cost = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        default=0,
        db_default=0,
        help_text="The cost in USD of the turns with a known model price.",
    )
    turns = models.PositiveIntegerField(default=0, db_default=0)
    unpriced_turns = models.PositiveIntegerField(default=0, db_default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["application", "hour"], name="agent_usage_unique_hour"
            )
        ]


class AgentFollowUp(CreatedAndUpdatedOnMixin, models.Model):
    """
    Something a user asked the agent to keep an eye on, like "tell me when the
    status of this issue changes". It owns its own schedule or row event,
    apart from the agent's triggers, which starts a check with the agent's
    configuration; the check notifies the user and completes the follow-up
    once its criteria are met.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"
        # Stopped after too many checks in a row failed.
        FAILED = "failed", "Failed"

    application = models.ForeignKey(
        AgentApplication, on_delete=models.CASCADE, related_name="follow_ups"
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Who asked for it, and who gets notified.",
    )
    source_chat = models.ForeignKey(
        AgentChat,
        null=True,
        blank=True,
        default=None,
        db_default=None,
        on_delete=models.SET_NULL,
        related_name="created_follow_ups",
        help_text="The conversation it was created in.",
    )
    service = models.OneToOneField(
        Service,
        null=True,
        blank=True,
        default=None,
        db_default=None,
        on_delete=models.SET_NULL,
        related_name="agent_follow_up",
        help_text=(
            "The schedule or row event starting its checks, apart from the "
            "agent's own triggers; removed once it ends."
        ),
    )
    private = models.BooleanField(
        default=False,
        db_default=False,
        help_text="Created in a private conversation, so its checks are private.",
    )
    title = models.CharField(max_length=255)
    goal = models.TextField(help_text="Why the user wants this.")
    check_instructions = models.TextField(help_text="What every check looks at.")
    done_when = models.TextField(help_text="When the follow-up is complete.")
    watch = models.JSONField(
        default=dict,
        help_text=(
            "When the checks run, kept for display after the trigger is gone: "
            "`{type: schedule, every}` or `{type: rows_*, table_id, row_ids}`."
        ),
    )
    state = models.TextField(
        blank=True,
        db_default="",
        help_text="What the checks remember between runs, e.g. the last status.",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_default=Status.ACTIVE,
    )
    outcome = models.TextField(blank=True, db_default="")
    expires_on = models.DateTimeField(
        null=True, blank=True, help_text="Null when it has no end date."
    )
    ended_on = models.DateTimeField(null=True, blank=True, db_default=None)
    last_checked_on = models.DateTimeField(null=True, blank=True, db_default=None)
    checks_count = models.PositiveIntegerField(default=0, db_default=0)
    failed_checks_in_a_row = models.PositiveIntegerField(default=0, db_default=0)
    notifications_count = models.PositiveIntegerField(default=0, db_default=0)
    total_input_tokens = models.BigIntegerField(default=0, db_default=0)
    total_cached_input_tokens = models.BigIntegerField(default=0, db_default=0)
    total_output_tokens = models.BigIntegerField(default=0, db_default=0)
    total_cost = models.DecimalField(
        max_digits=20, decimal_places=10, default=0, db_default=0
    )
    unpriced_turns = models.PositiveIntegerField(default=0, db_default=0)

    class Meta:
        ordering = ("-id",)
        indexes = [models.Index(fields=["application", "status"])]

    def get_parent(self):
        return self.application

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE
