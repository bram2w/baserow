import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import baserow.core.fields
import baserow.core.formula.field


def remove_workspace_search_tools(apps, schema_editor):
    """
    The built-in "workspace search" tool was dropped before release; rows of
    that type would make the tool registry raise for the agents holding them.
    """

    AgentTool = apps.get_model("baserow_enterprise", "AgentTool")
    AgentTool.objects.filter(type="workspace_search").delete()


def backfill_agent_usage(apps, schema_editor):
    """
    Turns the token counts already stored on the answers into hourly usage.
    Which model answered isn't stored, so their cost stays unknown.
    """

    AgentUsage = apps.get_model("baserow_enterprise", "AgentUsage")
    AgentChatMessage = apps.get_model("baserow_enterprise", "AgentChatMessage")
    AgentChat = apps.get_model("baserow_enterprise", "AgentChat")
    AgentDefinition = apps.get_model("baserow_enterprise", "AgentDefinition")
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"""
            INSERT INTO {AgentUsage._meta.db_table}
                (application_id, hour, input_tokens, output_tokens, cost, turns,
                 unpriced_turns)
            SELECT definition.application_id,
                   date_trunc('hour', message.created_on AT TIME ZONE 'UTC')
                       AT TIME ZONE 'UTC',
                   SUM(COALESCE(message.input_tokens, 0)),
                   SUM(COALESCE(message.output_tokens, 0)),
                   0,
                   COUNT(*),
                   COUNT(*)
            FROM {AgentChatMessage._meta.db_table} message
            JOIN {AgentChat._meta.db_table} chat ON chat.id = message.chat_id
            JOIN {AgentDefinition._meta.db_table} definition
                ON definition.id = chat.agent_id
            WHERE message.input_tokens IS NOT NULL
               OR message.output_tokens IS NOT NULL
            GROUP BY 1, 2
            ON CONFLICT (application_id, hour) DO NOTHING
            """  # noqa: S608
        )
        cursor.execute(
            f"""
            UPDATE {AgentChat._meta.db_table} chat
            SET unpriced_turns = counted.turns
            FROM (
                SELECT chat_id, COUNT(*) AS turns
                FROM {AgentChatMessage._meta.db_table}
                WHERE input_tokens IS NOT NULL OR output_tokens IS NOT NULL
                GROUP BY chat_id
            ) counted
            WHERE counted.chat_id = chat.id
            """  # noqa: S608
        )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        (
            "baserow_enterprise",
            "0069_agentapplication_agentchatchannel_agentchat_and_more",
        ),
        ("core", "0127_workspaceskill"),
        ("automation", "0039_coreresponseactionnode_and_more"),
        ("builder", "0080_builderworkflowaction_trashed_and_more"),
        ("database", "0226_rowhistory_actor"),
    ]

    operations = [
        migrations.AddField(
            model_name="agenttool",
            name="identity",
            field=models.ForeignKey(
                blank=True,
                db_default=None,
                default=None,
                help_text=(
                    "The workspace agent this tool acts as instead of the "
                    "application's identity."
                ),
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="core.agent",
            ),
        ),
        migrations.AddField(
            model_name="agentchattoolapproval",
            name="preview",
            field=models.JSONField(
                blank=True,
                db_default=None,
                help_text=(
                    "A human-readable rendering of what the call will do "
                    "(resolved service fields, rows to write), built when the "
                    "approval is recorded."
                ),
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="agenttool",
            name="trashed",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="agenttrigger",
            name="trashed",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="agentchatchannel",
            name="trashed",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.CreateModel(
            name="AgentSkill",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "mode",
                    models.CharField(
                        choices=[("always", "Always"), ("on_demand", "On demand")],
                        db_default="always",
                        default="always",
                        max_length=16,
                    ),
                ),
                (
                    "order",
                    models.PositiveIntegerField(db_default=0, default=0),
                ),
                (
                    "agent",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_skills",
                        to="baserow_enterprise.agentdefinition",
                    ),
                ),
                (
                    "skill",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_skills",
                        to="core.workspaceskill",
                    ),
                ),
            ],
            options={
                "ordering": ("order", "id"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("agent", "skill"), name="unique_agent_skill"
                    )
                ],
            },
        ),
        migrations.RunPython(remove_workspace_search_tools, migrations.RunPython.noop),
        migrations.CreateModel(
            name="CoreRunAgentActionNode",
            fields=[
                (
                    "automationnode_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="automation.automationnode",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("automation.automationnode",),
        ),
        migrations.AddField(
            model_name="agentchat",
            name="parent_chat",
            field=models.ForeignKey(
                blank=True,
                db_default=None,
                default=None,
                help_text="The conversation whose agent started this one through a tool call, when another agent did.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="child_chats",
                to="baserow_enterprise.agentchat",
            ),
        ),
        migrations.AlterField(
            model_name="agentchat",
            name="source",
            field=models.CharField(
                choices=[
                    ("manual", "Manual"),
                    ("trigger", "Trigger"),
                    ("setup", "Setup"),
                    ("channel", "Channel"),
                    ("service", "Service"),
                ],
                db_default="manual",
                default="manual",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="CoreRunAgentDatabaseWorkflowAction",
            fields=[
                (
                    "databaseworkflowaction_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="database.databaseworkflowaction",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        help_text="The service which this action is associated with.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_set",
                        to="core.service",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("database.databaseworkflowaction",),
        ),
        migrations.CreateModel(
            name="CoreRunAgentService",
            fields=[
                (
                    "service_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="core.service",
                    ),
                ),
                (
                    "prompt",
                    baserow.core.formula.field.FormulaField(
                        blank=True,
                        default="",
                        help_text="The message that opens the conversation.",
                        null=True,
                    ),
                ),
                (
                    "wait_for_result",
                    models.BooleanField(
                        db_default=False,
                        default=False,
                        help_text="Whether to run the agent's turn before answering, so the agent's reply is part of the result. Otherwise the run is queued and only the conversation link is returned.",
                    ),
                ),
                (
                    "agent_application",
                    models.ForeignKey(
                        help_text="The agent application to start a conversation with.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="baserow_enterprise.agentapplication",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("core.service",),
        ),
        migrations.CreateModel(
            name="CoreRunAgentWorkflowAction",
            fields=[
                (
                    "builderworkflowaction_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="builder.builderworkflowaction",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        help_text="The service which this action is associated with.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.service",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("builder.builderworkflowaction",),
        ),
        migrations.AddField(
            model_name="agenttrigger",
            name="config",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name="AgentEmailMessage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("session_key", models.CharField(max_length=255)),
                (
                    "direction",
                    models.CharField(
                        choices=[("inbound", "Inbound"), ("outbound", "Outbound")],
                        max_length=8,
                    ),
                ),
                (
                    "message_id",
                    models.CharField(blank=True, db_default="", max_length=998),
                ),
                (
                    "in_reply_to",
                    models.CharField(blank=True, db_default="", max_length=998),
                ),
                (
                    "references",
                    models.JSONField(blank=True, db_default=[], default=list),
                ),
                (
                    "thread_key",
                    models.CharField(blank=True, db_default="", max_length=255),
                ),
                (
                    "provider_message_id",
                    models.CharField(blank=True, db_default="", max_length=255),
                ),
                (
                    "from_address",
                    models.CharField(blank=True, db_default="", max_length=320),
                ),
                (
                    "from_name",
                    models.CharField(blank=True, db_default="", max_length=255),
                ),
                (
                    "to_addresses",
                    models.JSONField(blank=True, db_default=[], default=list),
                ),
                (
                    "subject",
                    models.CharField(blank=True, db_default="", max_length=998),
                ),
                (
                    "subject_normalized",
                    models.CharField(blank=True, db_default="", max_length=998),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="email_messages",
                        to="baserow_enterprise.agentchatchannel",
                    ),
                ),
            ],
            options={
                "ordering": ("id",),
                "indexes": [
                    models.Index(
                        fields=["channel", "session_key"],
                        name="baserow_ent_channel_613a6f_idx",
                    ),
                    models.Index(
                        fields=["channel", "message_id"],
                        name="baserow_ent_channel_f66647_idx",
                    ),
                    models.Index(
                        fields=["channel", "thread_key"],
                        name="baserow_ent_channel_cd1031_idx",
                    ),
                    models.Index(
                        fields=["channel", "from_address", "subject_normalized"],
                        name="baserow_ent_channel_8ca67e_idx",
                    ),
                ],
            },
        ),
        migrations.AddField(
            model_name="agentapplication",
            name="act_as_user",
            field=models.BooleanField(
                db_default=False,
                default=False,
                help_text=(
                    "Acts on behalf of the Baserow user who started or continued "
                    "the conversation instead of an agent identity. Conversations "
                    "without such a user get no workspace access."
                ),
            ),
        ),
        migrations.AddField(
            model_name="agentapplication",
            name="start_chat_min_role",
            field=models.CharField(
                choices=[
                    ("EDITOR", "Editors and up"),
                    ("BUILDER", "Builders and up"),
                    ("ADMIN", "Admins"),
                    ("NOBODY", "Nobody"),
                ],
                db_default="EDITOR",
                default="EDITOR",
                help_text="The minimum role needed to start a conversation in Baserow.",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="agentapplication",
            name="continue_chat_min_role",
            field=models.CharField(
                choices=[
                    ("EDITOR", "Editors and up"),
                    ("BUILDER", "Builders and up"),
                    ("ADMIN", "Admins"),
                    ("NOBODY", "Nobody"),
                ],
                db_default="EDITOR",
                default="EDITOR",
                help_text=(
                    "The minimum role needed to continue a conversation that a "
                    "trigger started."
                ),
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="agentchat",
            name="private",
            field=models.BooleanField(
                db_default=False,
                default=False,
                help_text="Only the user who started a private conversation can see it.",
            ),
        ),
        migrations.AddField(
            model_name="agenttool",
            name="act_as_user",
            field=models.BooleanField(
                db_default=False,
                default=False,
                help_text=(
                    "Acts on behalf of the Baserow user of the conversation instead "
                    "of the application's identity. Unavailable without such a user."
                ),
            ),
        ),
        migrations.AddField(
            model_name="agentchat",
            name="total_cost",
            field=models.DecimalField(
                db_default=0,
                decimal_places=10,
                default=0,
                help_text="The cost in USD of the turns with a known model price.",
                max_digits=20,
            ),
        ),
        migrations.AddField(
            model_name="agentchat",
            name="unpriced_turns",
            field=models.PositiveIntegerField(
                db_default=0,
                default=0,
                help_text="Turns whose model has no known price, so their cost is "
                "missing.",
            ),
        ),
        migrations.AddField(
            model_name="agentchatmessage",
            name="cost",
            field=models.DecimalField(
                blank=True,
                db_default=None,
                decimal_places=10,
                help_text="The cost in USD, or null when the model has no known price.",
                max_digits=20,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="AgentUsage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "hour",
                    models.DateTimeField(help_text="The start of the hour, in UTC."),
                ),
                ("input_tokens", models.BigIntegerField(db_default=0, default=0)),
                ("output_tokens", models.BigIntegerField(db_default=0, default=0)),
                (
                    "cost",
                    models.DecimalField(
                        db_default=0,
                        decimal_places=10,
                        default=0,
                        help_text="The cost in USD of the turns with a known model "
                        "price.",
                        max_digits=20,
                    ),
                ),
                ("turns", models.PositiveIntegerField(db_default=0, default=0)),
                (
                    "unpriced_turns",
                    models.PositiveIntegerField(db_default=0, default=0),
                ),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="usage",
                        to="baserow_enterprise.agentapplication",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("application", "hour"), name="agent_usage_unique_hour"
                    )
                ],
            },
        ),
        migrations.RunPython(backfill_agent_usage, migrations.RunPython.noop),
        migrations.AddField(
            model_name="agentapplication",
            name="follow_up_min_role",
            field=models.CharField(
                choices=[
                    ("EDITOR", "Editors and up"),
                    ("BUILDER", "Builders and up"),
                    ("ADMIN", "Admins"),
                    ("NOBODY", "Nobody"),
                ],
                db_default="BUILDER",
                default="BUILDER",
                help_text="The minimum role needed to have the agent create a follow-up.",
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="agentchat",
            name="source",
            field=models.CharField(
                choices=[
                    ("manual", "Manual"),
                    ("trigger", "Trigger"),
                    ("setup", "Setup"),
                    ("channel", "Channel"),
                    ("service", "Service"),
                    ("follow_up", "Follow-up"),
                ],
                db_default="manual",
                default="manual",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="AgentFollowUp",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", baserow.core.fields.SyncedDateTimeField(auto_now=True)),
                (
                    "private",
                    models.BooleanField(
                        db_default=False,
                        default=False,
                        help_text="Created in a private conversation, so its checks are private.",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("goal", models.TextField(help_text="Why the user wants this.")),
                (
                    "check_instructions",
                    models.TextField(help_text="What every check looks at."),
                ),
                (
                    "done_when",
                    models.TextField(help_text="When the follow-up is complete."),
                ),
                (
                    "watch",
                    models.JSONField(
                        default=dict,
                        help_text="When the checks run, kept for display after the trigger is gone: `{type: schedule, every}` or `{type: rows_*, table_id, row_ids}`.",
                    ),
                ),
                (
                    "state",
                    models.TextField(
                        blank=True,
                        db_default="",
                        help_text="What the checks remember between runs, e.g. the last status.",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                            ("expired", "Expired"),
                            ("failed", "Failed"),
                        ],
                        db_default="active",
                        default="active",
                        max_length=16,
                    ),
                ),
                ("outcome", models.TextField(blank=True, db_default="")),
                (
                    "expires_on",
                    models.DateTimeField(
                        blank=True,
                        help_text="Null when it has no end date.",
                        null=True,
                    ),
                ),
                (
                    "ended_on",
                    models.DateTimeField(blank=True, db_default=None, null=True),
                ),
                (
                    "last_checked_on",
                    models.DateTimeField(blank=True, db_default=None, null=True),
                ),
                ("checks_count", models.PositiveIntegerField(db_default=0, default=0)),
                (
                    "failed_checks_in_a_row",
                    models.PositiveIntegerField(db_default=0, default=0),
                ),
                (
                    "notifications_count",
                    models.PositiveIntegerField(db_default=0, default=0),
                ),
                ("total_input_tokens", models.BigIntegerField(db_default=0, default=0)),
                (
                    "total_output_tokens",
                    models.BigIntegerField(db_default=0, default=0),
                ),
                (
                    "total_cost",
                    models.DecimalField(
                        db_default=0, decimal_places=10, default=0, max_digits=20
                    ),
                ),
                (
                    "unpriced_turns",
                    models.PositiveIntegerField(db_default=0, default=0),
                ),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="follow_ups",
                        to="baserow_enterprise.agentapplication",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        help_text="Who asked for it, and who gets notified.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "source_chat",
                    models.ForeignKey(
                        blank=True,
                        db_default=None,
                        default=None,
                        help_text="The conversation it was created in.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_follow_ups",
                        to="baserow_enterprise.agentchat",
                    ),
                ),
                (
                    "service",
                    models.OneToOneField(
                        blank=True,
                        db_default=None,
                        default=None,
                        help_text=(
                            "The schedule or row event starting its checks, apart "
                            "from the agent's own triggers; removed once it ends."
                        ),
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agent_follow_up",
                        to="core.service",
                    ),
                ),
            ],
            options={
                "ordering": ("-id",),
            },
        ),
        migrations.AddField(
            model_name="agentchat",
            name="follow_up",
            field=models.ForeignKey(
                blank=True,
                db_default=None,
                default=None,
                help_text="The follow-up this conversation is a check of.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="chats",
                to="baserow_enterprise.agentfollowup",
            ),
        ),
        migrations.AddIndex(
            model_name="agentfollowup",
            index=models.Index(
                fields=["application", "status"], name="baserow_ent_applica_84c7f0_idx"
            ),
        ),
    ]
