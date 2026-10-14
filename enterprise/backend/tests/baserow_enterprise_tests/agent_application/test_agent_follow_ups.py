import json
from datetime import timedelta
from unittest.mock import patch

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

import pytest
from freezegun import freeze_time
from pydantic_ai.messages import ToolReturnPart
from pydantic_ai.models.function import DeltaToolCall, FunctionModel
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)

from baserow.api.generative_ai.serializers import GenerativeAIModelsSerializer
from baserow.contrib.database.rows.handler import RowHandler
from baserow.core.generative_ai.registries import (
    GenerativeAIModelType,
    generative_ai_model_type_registry,
)
from baserow.core.handler import CoreHandler
from baserow.core.notifications.models import Notification
from baserow.core.services.models import Service
from baserow.core.services.registries import service_type_registry
from baserow_enterprise.agent_application.exceptions import AgentFollowUpInvalid
from baserow_enterprise.agent_application.follow_ups import AgentFollowUpHandler
from baserow_enterprise.agent_application.handler import (
    AgentApplicationHandler,
    AgentChatHandler,
)
from baserow_enterprise.agent_application.models import (
    AgentChat,
    AgentChatMessage,
    AgentFollowUp,
    AgentTrigger,
)
from baserow_enterprise.agent_application.tasks import (
    clean_up_old_agent_chats,
    run_agent_chat,
)
from baserow_enterprise.agent_application.triggers.handler import (
    AgentTriggerHandler,
)

BROADCAST = "baserow_enterprise.agent_application.realtime.broadcast_to_channel_group"
BROADCAST_TO_USERS = "baserow_enterprise.agent_application.realtime.broadcast_to_users"

# The tool calls the model makes, one per request, until it answers. Each test
# picks its script.
SCRIPT = []


def _tool_results(messages) -> int:
    return sum(
        isinstance(part, ToolReturnPart)
        for message in messages
        for part in getattr(message, "parts", [])
    )


async def _stream(messages, info):
    step = _tool_results(messages)
    if step < len(SCRIPT):
        name, args = SCRIPT[step]
        yield {
            0: DeltaToolCall(
                name=name, json_args=json.dumps(args), tool_call_id=f"call_{step}"
            )
        }
    else:
        yield "Done."


class FollowUpTestModelType(GenerativeAIModelType):
    type = "agent_follow_up_test"

    def is_enabled(self, workspace=None):
        return True

    def get_enabled_models(
        self, workspace=None, settings_override=None, feature_type=None, state=None
    ):
        return ["test-model"]

    def get_ai_model(self, model_name, workspace=None, settings_override=None):
        return FunctionModel(stream_function=_stream)

    def prompt(self, *args, **kwargs):
        return "Done."

    def get_settings_serializer(self):
        return GenerativeAIModelsSerializer


@pytest.fixture
def follow_up_setup(data_fixture):
    try:
        generative_ai_model_type_registry.register(FollowUpTestModelType())
    except generative_ai_model_type_registry.already_registered_exception_class:
        pass
    SCRIPT.clear()
    user, token = data_fixture.create_user_and_token(first_name="Ann")
    workspace = data_fixture.create_workspace(user=user)
    application = (
        CoreHandler()
        .create_application(user, workspace, "agent", init_with_data=True, name="Agent")
        .specific
    )
    agent = AgentApplicationHandler().get_main_agent(application)
    AgentApplicationHandler().update_agent(
        agent,
        ai_generative_ai_type="agent_follow_up_test",
        ai_generative_ai_model="test-model",
    )
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database, name="Issues")
    status = data_fixture.create_text_field(table=table, name="Status", primary=True)
    rows = (
        RowHandler()
        .create_rows(
            user,
            table,
            rows_values=[
                {f"field_{status.id}": "open"},
                {f"field_{status.id}": "open"},
            ],
        )
        .created_rows
    )
    return user, token, workspace, application, agent, table, status, rows


def _proposal(**overrides):
    return {
        "title": "Status of issue 1",
        "goal": "Ann wants to know when issue 1 is closed.",
        "check_instructions": "Read row 1 of the Issues table and its Status.",
        "done_when": "The status is closed.",
        "watch": "schedule",
        "every": "hour",
        "state": "Status is open.",
        "thought": "The user asked to be reminded.",
        **overrides,
    }


def _send(agent, user, content="Remind me when it's closed.", chat=None):
    chat = chat or AgentChat.objects.create(agent=agent, user=user, title="Issues")
    prompt = AgentChatHandler().create_message(
        chat, AgentChatMessage.Role.HUMAN, content
    )
    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        run_agent_chat(chat.id, prompt.id)
    chat.refresh_from_db()
    return chat


def _approve(api_client, chat, token, approved=True):
    approval = chat.tool_approvals.get()
    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        return api_client.post(
            reverse("api:agent:chat_approvals", kwargs={"chat_uuid": chat.uuid}),
            {"decisions": [{"id": approval.id, "approved": approved}]},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )


def _update_rows(user, table, rows_values):
    # As in a request, so the row signals fire once the transaction commits.
    with transaction.atomic():
        RowHandler().update_rows(user, table, rows_values)


def _create_follow_up(user, chat, **overrides) -> AgentFollowUp:
    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        return AgentFollowUpHandler().create_follow_up(
            user, chat, _proposal(**overrides)
        )


@pytest.mark.django_db(transaction=True)
def test_a_proposed_follow_up_only_exists_once_the_user_approves(
    follow_up_setup, api_client
):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    SCRIPT.append(("propose_follow_up", _proposal()))

    chat = _send(agent, user)

    assert chat.status == AgentChat.Status.AWAITING_APPROVAL
    assert not AgentFollowUp.objects.exists()
    preview = chat.tool_approvals.get().preview
    assert preview["kind"] == "follow_up"
    assert preview["watch"] == {"type": "schedule", "every": "hour"}
    assert preview["checks_per_day"] == 24
    assert preview["notify"] == "Ann"
    assert preview["state"] == "Status is open."

    response = _approve(api_client, chat, token)

    assert response.status_code == HTTP_200_OK, response.json()
    follow_up = AgentFollowUp.objects.get()
    assert follow_up.status == AgentFollowUp.Status.ACTIVE
    assert follow_up.created_by == user
    assert follow_up.source_chat == chat
    assert follow_up.service.specific.interval == "HOUR"
    assert follow_up.expires_on > timezone.now() + timedelta(days=29)
    # Its schedule is its own; the agent's triggers are untouched.
    assert not AgentTrigger.objects_and_trash.exists()


@pytest.mark.django_db(transaction=True)
def test_only_the_conversations_user_approves_a_follow_up(
    follow_up_setup, api_client, data_fixture
):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    admin, admin_token = data_fixture.create_user_and_token()
    CoreHandler().add_user_to_workspace(workspace, admin, permissions="ADMIN")
    SCRIPT.append(("propose_follow_up", _proposal()))
    chat = _send(agent, user)

    response = _approve(api_client, chat, admin_token)

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert not AgentFollowUp.objects.exists()


@pytest.mark.django_db
def test_a_proposal_is_checked_before_the_user_sees_it(follow_up_setup):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    chat = AgentChat.objects.create(agent=agent, user=user)
    handler = AgentFollowUpHandler()

    with pytest.raises(AgentFollowUpInvalid):
        handler.prepare_proposal(user, chat, _proposal(every="minute"))
    with pytest.raises(AgentFollowUpInvalid):
        handler.prepare_proposal(
            user, chat, _proposal(watch="rows_updated", table_id=table.id)
        )
    prepared = handler.prepare_proposal(
        user,
        chat,
        _proposal(
            watch="rows_updated",
            table_id=table.id,
            row_ids=[rows[0].id],
            expires_in_days=1000,
        ),
    )
    assert prepared["watch"]["table_name"] == "Issues"
    assert prepared["expires_in_days"] == 365
    # Only no end date when asked for explicitly.
    assert handler.prepare_proposal(user, chat, _proposal())["expires_in_days"] == 30
    assert (
        handler.prepare_proposal(user, chat, _proposal(expires_in_days=None))[
            "expires_in_days"
        ]
        is None
    )

    for _ in range(10):
        _create_follow_up(user, chat)
    with pytest.raises(AgentFollowUpInvalid):
        handler.prepare_proposal(user, chat, _proposal())


@pytest.mark.django_db
def test_the_minimum_role_decides_who_may_create_follow_ups(
    enable_enterprise, synced_roles, follow_up_setup, data_fixture
):
    from baserow_enterprise.role.handler import RoleAssignmentHandler
    from baserow_enterprise.role.models import Role

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    editor = data_fixture.create_user()
    CoreHandler().add_user_to_workspace(workspace, editor)
    RoleAssignmentHandler().assign_role(
        editor, workspace, role=Role.objects.get(uid="EDITOR")
    )
    handler = AgentFollowUpHandler()

    assert not handler.can_create(editor, application)
    assert handler.can_create(user, application)

    application.follow_up_min_role = "EDITOR"
    application.save()
    assert handler.can_create(editor, application)


@pytest.mark.django_db(transaction=True)
def test_a_watched_row_starts_a_check_that_notifies_and_completes(follow_up_setup):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    chat = AgentChat.objects.create(agent=agent, user=user)
    follow_up = _create_follow_up(
        user, chat, watch="rows_updated", table_id=table.id, row_ids=[rows[0].id]
    )
    service_id = follow_up.service_id
    SCRIPT.extend(
        [
            ("notify_user", {"message": "Issue 1 is closed.", "thought": "."}),
            ("complete_follow_up", {"outcome": "It was closed.", "thought": "."}),
        ]
    )

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        # Another row changing doesn't concern this follow-up.
        _update_rows(user, table, [{"id": rows[1].id, f"field_{status.id}": "closed"}])
        assert not AgentChat.objects.filter(follow_up=follow_up).exists()

        _update_rows(user, table, [{"id": rows[0].id, f"field_{status.id}": "closed"}])

    check = AgentChat.objects.get(follow_up=follow_up)
    assert check.source == AgentChat.Source.FOLLOW_UP
    assert check.user == user
    # The check only sees the watched row.
    assert [row["id"] for row in check.event_payload["results"]] == [rows[0].id]
    follow_up.refresh_from_db()
    assert follow_up.status == AgentFollowUp.Status.COMPLETED
    assert follow_up.outcome == "It was closed."
    assert follow_up.service_id is None
    assert not Service.objects.filter(id=service_id).exists()
    assert follow_up.checks_count == 1
    assert follow_up.notifications_count == 1
    assert follow_up.total_input_tokens > 0
    notification = Notification.objects.get(type="agent_follow_up")
    assert notification.data["message"] == "Issue 1 is closed."
    assert notification.data["chat_uuid"] == str(check.uuid)
    assert list(notification.recipients.all()) == [user]


@pytest.mark.django_db(transaction=True)
def test_a_check_that_finds_nothing_leaves_no_conversation(follow_up_setup):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    chat = AgentChat.objects.create(agent=agent, user=user)
    follow_up = _create_follow_up(
        user, chat, watch="rows_updated", table_id=table.id, row_ids=[rows[0].id]
    )
    SCRIPT.append(
        ("remember_follow_up_state", {"state": "Status is pending.", "thought": "."})
    )

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        _update_rows(user, table, [{"id": rows[0].id, f"field_{status.id}": "pending"}])

    follow_up.refresh_from_db()
    assert follow_up.status == AgentFollowUp.Status.ACTIVE
    assert follow_up.state == "Status is pending."
    assert follow_up.checks_count == 1
    assert follow_up.total_input_tokens > 0
    assert not AgentChat.objects.filter(follow_up=follow_up).exists()
    assert not Notification.objects.exists()


@pytest.mark.django_db
def test_failing_checks_stop_the_follow_up(follow_up_setup):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    chat = AgentChat.objects.create(agent=agent, user=user)
    follow_up = _create_follow_up(user, chat)
    handler = AgentFollowUpHandler()

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        for _ in range(3):
            check = AgentChat.objects.create(
                agent=agent,
                user=user,
                source=AgentChat.Source.FOLLOW_UP,
                follow_up=follow_up,
                status=AgentChat.Status.ERROR,
            )
            handler.finish_check(check, notified=False, ended=False)

    follow_up.refresh_from_db()
    assert follow_up.status == AgentFollowUp.Status.FAILED
    # Failed checks are kept to see what went wrong.
    assert follow_up.chats.count() == 3
    assert Notification.objects.get(type="agent_follow_up").data["status"] == ("failed")


@pytest.mark.django_db
def test_expired_and_orphaned_follow_ups_are_ended(follow_up_setup, data_fixture):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    other = data_fixture.create_user()
    CoreHandler().add_user_to_workspace(workspace, other)
    chat = AgentChat.objects.create(agent=agent, user=user)
    expiring = _create_follow_up(user, chat, expires_in_days=1)
    leaving = _create_follow_up(other, chat)
    staying = _create_follow_up(user, chat)
    CoreHandler().leave_workspace(other, workspace)

    with (
        freeze_time(timezone.now() + timedelta(days=2)),
        patch(BROADCAST),
        patch(BROADCAST_TO_USERS),
    ):
        staying.expires_on = timezone.now() + timedelta(days=5)
        staying.save()
        clean_up_old_agent_chats()

    statuses = dict(AgentFollowUp.objects.values_list("id", "status"))
    assert statuses == {
        expiring.id: AgentFollowUp.Status.EXPIRED,
        leaving.id: AgentFollowUp.Status.CANCELLED,
        staying.id: AgentFollowUp.Status.ACTIVE,
    }


@pytest.mark.django_db
def test_follow_ups_are_listed_and_cancelled_by_who_may(
    enable_enterprise, synced_roles, follow_up_setup, api_client, data_fixture
):
    from baserow_enterprise.role.handler import RoleAssignmentHandler
    from baserow_enterprise.role.models import Role

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    editor, editor_token = data_fixture.create_user_and_token()
    CoreHandler().add_user_to_workspace(workspace, editor)
    RoleAssignmentHandler().assign_role(
        editor, workspace, role=Role.objects.get(uid="EDITOR")
    )
    application.follow_up_min_role = "EDITOR"
    application.save()
    private_chat = AgentChat.objects.create(agent=agent, user=editor, private=True)
    editors = _create_follow_up(editor, private_chat, title="Editor's secret")
    owners = _create_follow_up(
        user, AgentChat.objects.create(agent=agent, user=user), title="Builder's"
    )
    url = reverse("api:agent:follow_ups", kwargs={"application_id": application.id})

    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
    by_id = {item["id"]: item for item in response.json()}
    assert set(by_id) == {editors.id, owners.id}
    # Someone else's private follow-up only shows that it exists.
    assert by_id[editors.id]["title"] == ""
    assert by_id[editors.id]["created_by"]["id"] == editor.id

    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {editor_token}")
    assert [item["title"] for item in response.json()] == ["Editor's secret"]

    def cancel(follow_up, auth_token):
        with patch(BROADCAST), patch(BROADCAST_TO_USERS):
            return api_client.delete(
                reverse(
                    "api:agent:follow_up_item", kwargs={"follow_up_id": follow_up.id}
                ),
                HTTP_AUTHORIZATION=f"JWT {auth_token}",
            )

    assert cancel(owners, editor_token).status_code == HTTP_401_UNAUTHORIZED
    response = cancel(editors, token)
    assert response.status_code == HTTP_200_OK
    assert response.json()["status"] == "cancelled"
    assert response.json()["title"] == ""
    assert cancel(owners, token).json()["status"] == "cancelled"

    response = api_client.get(url + "?status=active", HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.json() == []


@pytest.mark.django_db
def test_follow_ups_are_not_exported(follow_up_setup):
    from baserow.core.registries import ImportExportConfig, application_type_registry

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    _create_follow_up(user, AgentChat.objects.create(agent=agent, user=user))

    serialized = application_type_registry.get("agent").export_serialized(
        application, ImportExportConfig(include_permission_data=False)
    )

    assert serialized["triggers"] == []
    assert serialized["follow_up_min_role"] == "BUILDER"


@pytest.mark.django_db
def test_the_agents_schedule_and_a_follow_ups_schedule_run_apart(follow_up_setup):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        AgentTriggerHandler().create_trigger(
            user, application, "periodic", service_values={"interval": "HOUR"}
        )
        follow_up = _create_follow_up(
            user, AgentChat.objects.create(agent=agent, user=user)
        )

    with (
        freeze_time(timezone.now() + timedelta(hours=2)),
        patch(BROADCAST),
        patch(BROADCAST_TO_USERS),
        patch("baserow_enterprise.agent_application.tasks.run_agent_chat.delay"),
        transaction.atomic(),
    ):
        service_type_registry.get("periodic").call_periodic_services_that_are_due()

    # Each schedule starts its own run: the agent's a triggered conversation
    # with its instructions, the follow-up's a check.
    started = AgentChat.objects.exclude(source=AgentChat.Source.MANUAL)
    assert sorted(started.values_list("source", "follow_up_id")) == [
        (AgentChat.Source.FOLLOW_UP, follow_up.id),
        (AgentChat.Source.TRIGGER, None),
    ]


@pytest.mark.django_db(transaction=True)
def test_a_follow_up_can_be_checked_right_away(
    enable_enterprise, synced_roles, follow_up_setup, api_client, data_fixture
):
    from baserow_enterprise.role.handler import RoleAssignmentHandler
    from baserow_enterprise.role.models import Role

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    editor, editor_token = data_fixture.create_user_and_token()
    CoreHandler().add_user_to_workspace(workspace, editor)
    RoleAssignmentHandler().assign_role(
        editor, workspace, role=Role.objects.get(uid="EDITOR")
    )
    follow_up = _create_follow_up(
        user, AgentChat.objects.create(agent=agent, user=user)
    )
    url = reverse("api:agent:follow_up_check", kwargs={"follow_up_id": follow_up.id})

    def check(auth_token):
        with patch(BROADCAST), patch(BROADCAST_TO_USERS):
            return api_client.post(url, HTTP_AUTHORIZATION=f"JWT {auth_token}")

    assert check(editor_token).status_code == HTTP_401_UNAUTHORIZED

    response = check(token)

    assert response.status_code == HTTP_200_OK, response.json()
    # Kept although nothing changed, so the person who asked sees the outcome.
    chat = AgentChat.objects.get(uuid=response.json()["uuid"])
    assert chat.follow_up == follow_up
    assert chat.status == AgentChat.Status.IDLE
    follow_up.refresh_from_db()
    assert follow_up.checks_count == 1

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        AgentFollowUpHandler().cancel_follow_up(user, follow_up)
    response = check(token)
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_AGENT_FOLLOW_UP_NOT_ACTIVE"


@pytest.mark.django_db
def test_stopping_a_follow_up_can_be_undone_while_it_is_still_valid(
    follow_up_setup, data_fixture
):
    import uuid

    from baserow.core.action.handler import ActionHandler
    from baserow.core.action.registries import action_type_registry
    from baserow.core.action.scopes import ApplicationActionScopeType
    from baserow_enterprise.agent_application.actions import (
        StopAgentFollowUpActionType,
    )

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    session_id = str(uuid.uuid4())
    user.untrusted_client_session_id = session_id
    chat = AgentChat.objects.create(agent=agent, user=user)
    follow_up = _create_follow_up(user, chat, expires_in_days=None)
    scope = ApplicationActionScopeType.value(application.id)

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        action_type_registry.get_by_type(StopAgentFollowUpActionType).do(
            user, follow_up
        )
        follow_up.refresh_from_db()
        assert follow_up.status == AgentFollowUp.Status.CANCELLED
        assert follow_up.service_id is None
        assert follow_up.expires_on is None

        ActionHandler.undo(user, [scope], session_id)

        follow_up.refresh_from_db()
        assert follow_up.status == AgentFollowUp.Status.ACTIVE
        assert follow_up.outcome == ""
        assert follow_up.service.specific.interval == "HOUR"

        ActionHandler.redo(user, [scope], session_id)
        follow_up.refresh_from_db()
        assert follow_up.status == AgentFollowUp.Status.CANCELLED

        # It can't come back once it would have expired in the meantime.
        follow_up.expires_on = timezone.now() - timedelta(minutes=1)
        follow_up.save()
        ActionHandler.undo(user, [scope], session_id)
    follow_up.refresh_from_db()
    assert follow_up.status == AgentFollowUp.Status.CANCELLED
    assert follow_up.service_id is None


@pytest.mark.django_db(transaction=True)
def test_writing_in_a_check_allows_asking_for_a_new_follow_up(follow_up_setup):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    follow_up = _create_follow_up(
        user, AgentChat.objects.create(agent=agent, user=user)
    )
    SCRIPT.append(("complete_follow_up", {"outcome": "Done.", "thought": "."}))
    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        check = AgentFollowUpHandler().check_now(user, follow_up)
    follow_up.refresh_from_db()
    assert follow_up.status == AgentFollowUp.Status.COMPLETED

    # The check itself couldn't propose anything; once the user writes in it,
    # it's their conversation.
    SCRIPT[:] = [("propose_follow_up", _proposal(title="Active again"))]
    chat = _send(agent, user, "Remind me when it's open again.", chat=check)

    assert chat.status == AgentChat.Status.AWAITING_APPROVAL
    assert chat.tool_approvals.get().preview["title"] == "Active again"


def _role(uid):
    from baserow_enterprise.role.models import Role

    return Role.objects.get(uid=uid)


def _builder_and_editor(workspace, application, data_fixture):
    from baserow_enterprise.role.handler import RoleAssignmentHandler

    builder, builder_token = data_fixture.create_user_and_token()
    editor, editor_token = data_fixture.create_user_and_token()
    for member, uid in ((builder, "BUILDER"), (editor, "EDITOR")):
        CoreHandler().add_user_to_workspace(workspace, member)
        RoleAssignmentHandler().assign_role(member, workspace, role=_role(uid))
    application.follow_up_min_role = "EDITOR"
    application.save()
    return builder, builder_token, editor, editor_token


@pytest.mark.django_db(transaction=True)
def test_checking_someone_elses_private_follow_up_reveals_nothing(
    enable_enterprise, synced_roles, follow_up_setup, api_client, data_fixture
):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    builder, builder_token, editor, editor_token = _builder_and_editor(
        workspace, application, data_fixture
    )
    private_chat = AgentChat.objects.create(agent=agent, user=editor, private=True)
    follow_up = _create_follow_up(editor, private_chat, title="Editor secret")

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        response = api_client.post(
            reverse("api:agent:follow_up_check", kwargs={"follow_up_id": follow_up.id}),
            HTTP_AUTHORIZATION=f"JWT {builder_token}",
        )

    assert response.status_code == HTTP_200_OK
    assert set(response.json()) == {"id", "uuid", "status"}
    assert "Editor secret" not in json.dumps(response.json())


@pytest.mark.django_db(transaction=True)
def test_a_check_never_runs_with_access_its_creator_lost(
    enable_enterprise, synced_roles, follow_up_setup, data_fixture
):
    from baserow_enterprise.role.handler import RoleAssignmentHandler

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    builder, builder_token, editor, editor_token = _builder_and_editor(
        workspace, application, data_fixture
    )
    follow_up = _create_follow_up(
        editor,
        AgentChat.objects.create(agent=agent, user=editor),
        watch="rows_updated",
        table_id=table.id,
        row_ids=[rows[0].id],
    )
    RoleAssignmentHandler().assign_role(
        editor, workspace, role=_role("NO_ACCESS"), scope=table
    )

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        _update_rows(user, table, [{"id": rows[0].id, f"field_{status.id}": "secret"}])

    follow_up.refresh_from_db()
    assert follow_up.status == AgentFollowUp.Status.CANCELLED
    assert "no longer has access to the table" in follow_up.outcome
    assert not AgentChat.objects.filter(follow_up=follow_up).exists()
    notification = Notification.objects.get(type="agent_follow_up")
    assert "secret" not in json.dumps(notification.data)


@pytest.mark.django_db
def test_lost_access_to_the_agent_ends_follow_ups_in_the_clean_up(
    enable_enterprise, synced_roles, follow_up_setup, data_fixture
):
    from baserow_enterprise.role.handler import RoleAssignmentHandler

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    builder, builder_token, editor, editor_token = _builder_and_editor(
        workspace, application, data_fixture
    )
    follow_up = _create_follow_up(
        editor, AgentChat.objects.create(agent=agent, user=editor)
    )
    RoleAssignmentHandler().assign_role(
        editor, workspace, role=_role("NO_ACCESS"), scope=application.application_ptr
    )

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        clean_up_old_agent_chats()

    follow_up.refresh_from_db()
    assert follow_up.status == AgentFollowUp.Status.CANCELLED
    assert "no longer has access to the agent" in follow_up.outcome


@pytest.mark.django_db
def test_a_deleted_watched_table_ends_the_follow_up(follow_up_setup):
    from baserow.core.trash.handler import TrashHandler

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    follow_up = _create_follow_up(
        user,
        AgentChat.objects.create(agent=agent, user=user),
        watch="rows_updated",
        table_id=table.id,
        row_ids=[rows[0].id],
        expires_in_days=None,
    )

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        TrashHandler.trash(user, workspace, table.database, table)
        clean_up_old_agent_chats()
        follow_up.refresh_from_db()
        # In the trash it can still come back, so the follow-up waits.
        assert follow_up.status == AgentFollowUp.Status.ACTIVE

        TrashHandler.permanently_delete(table)
        clean_up_old_agent_chats()

    follow_up.refresh_from_db()
    assert follow_up.status == AgentFollowUp.Status.CANCELLED
    assert "was deleted" in follow_up.outcome


@pytest.mark.django_db
def test_permanently_deleting_the_agent_leaves_no_follow_up_services(
    follow_up_setup,
):
    from baserow.core.trash.handler import TrashHandler

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    chat = AgentChat.objects.create(agent=agent, user=user)
    scheduled = _create_follow_up(user, chat)
    watching = _create_follow_up(
        user, chat, watch="rows_updated", table_id=table.id, row_ids=[rows[0].id]
    )
    service_ids = [scheduled.service_id, watching.service_id]

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        TrashHandler.trash(user, workspace, application, application)
        TrashHandler.permanently_delete(application)

    assert not Service.objects.filter(id__in=service_ids).exists()


@pytest.mark.django_db
def test_schedules_below_the_instance_minimum_are_never_proposed(follow_up_setup):
    from django.test import override_settings

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    chat = AgentChat.objects.create(agent=agent, user=user)
    handler = AgentFollowUpHandler()

    with override_settings(INTEGRATIONS_PERIODIC_MINUTE_MIN=30):
        assert handler.get_allowed_schedules() == ["30_minutes", "hour", "day", "week"]
        with pytest.raises(AgentFollowUpInvalid):
            handler.prepare_proposal(user, chat, _proposal(every="15_minutes"))
        assert handler.prepare_proposal(user, chat, _proposal(every="30_minutes"))


@pytest.mark.django_db
def test_follow_ups_of_a_trashed_agent_wait(follow_up_setup, api_client):
    from baserow.core.trash.handler import TrashHandler

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    follow_up = _create_follow_up(
        user, AgentChat.objects.create(agent=agent, user=user), expires_in_days=1
    )

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        TrashHandler.trash(user, workspace, application, application)
        response = api_client.post(
            reverse("api:agent:follow_up_check", kwargs={"follow_up_id": follow_up.id}),
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == 404
        with freeze_time(timezone.now() + timedelta(days=2)):
            clean_up_old_agent_chats()

    follow_up.refresh_from_db()
    assert follow_up.status == AgentFollowUp.Status.ACTIVE
    assert not Notification.objects.exists()


@pytest.mark.django_db
def test_a_follow_up_that_already_ended_is_not_announced_again(follow_up_setup):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    follow_up = _create_follow_up(
        user, AgentChat.objects.create(agent=agent, user=user)
    )
    handler = AgentFollowUpHandler()

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        for _ in range(2):
            handler.finish_check(
                AgentChat.objects.create(
                    agent=agent,
                    user=user,
                    source=AgentChat.Source.FOLLOW_UP,
                    follow_up=follow_up,
                    status=AgentChat.Status.ERROR,
                ),
                notified=False,
                ended=False,
            )
        # Stopped while the third failing check ran.
        handler.cancel_follow_up(user, follow_up)
        handler.finish_check(
            AgentChat.objects.create(
                agent=agent,
                user=user,
                source=AgentChat.Source.FOLLOW_UP,
                follow_up=follow_up,
                status=AgentChat.Status.ERROR,
            ),
            notified=False,
            ended=False,
        )
        assert handler.notify_user(follow_up, None, "Too late.") is False

    follow_up.refresh_from_db()
    assert follow_up.status == AgentFollowUp.Status.CANCELLED
    assert follow_up.checks_count == 2
    assert not Notification.objects.exists()


@pytest.mark.django_db
def test_a_check_the_user_took_over_doesnt_hold_back_the_next(follow_up_setup):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    follow_up = _create_follow_up(
        user, AgentChat.objects.create(agent=agent, user=user)
    )
    taken_over = AgentChat.objects.create(
        agent=agent,
        user=user,
        source=AgentChat.Source.FOLLOW_UP,
        follow_up=follow_up,
        status=AgentChat.Status.AWAITING_APPROVAL,
    )
    AgentChatMessage.objects.create(
        chat=taken_over, role=AgentChatMessage.Role.HUMAN, content="And also…"
    )

    assert not AgentFollowUpHandler().is_checking(follow_up)


@pytest.mark.django_db
def test_a_stuck_check_counts_as_failed(follow_up_setup):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    follow_up = _create_follow_up(
        user, AgentChat.objects.create(agent=agent, user=user)
    )
    with freeze_time(timezone.now() - timedelta(days=1)):
        AgentChat.objects.create(
            agent=agent,
            user=user,
            source=AgentChat.Source.FOLLOW_UP,
            follow_up=follow_up,
            status=AgentChat.Status.IN_PROGRESS,
        )

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        clean_up_old_agent_chats()

    follow_up.refresh_from_db()
    assert follow_up.checks_count == 1
    assert follow_up.failed_checks_in_a_row == 1


@pytest.mark.django_db
def test_undoing_a_stop_after_losing_access_keeps_it_stopped(
    enable_enterprise, synced_roles, follow_up_setup, data_fixture
):
    from baserow_enterprise.agent_application.exceptions import (
        AgentFollowUpNotActive,
    )
    from baserow_enterprise.role.handler import RoleAssignmentHandler

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    builder, builder_token, editor, editor_token = _builder_and_editor(
        workspace, application, data_fixture
    )
    follow_up = _create_follow_up(
        editor,
        AgentChat.objects.create(agent=agent, user=editor),
        watch="rows_updated",
        table_id=table.id,
        row_ids=[rows[0].id],
    )
    handler = AgentFollowUpHandler()
    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        handler.cancel_follow_up(editor, follow_up)
    RoleAssignmentHandler().assign_role(
        editor, workspace, role=_role("NO_ACCESS"), scope=table
    )

    with pytest.raises(AgentFollowUpNotActive):
        handler.resume_follow_up(editor, follow_up)
    follow_up.refresh_from_db()
    assert follow_up.status == AgentFollowUp.Status.CANCELLED


@pytest.mark.django_db
def test_private_follow_ups_stay_out_of_shared_places(follow_up_setup):
    import uuid

    from baserow.core.action.models import Action
    from baserow.core.action.registries import action_type_registry
    from baserow_enterprise.agent_application.actions import (
        StopAgentFollowUpActionType,
    )
    from baserow_enterprise.agent_application.runner import AgentRunner

    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    user.untrusted_client_session_id = str(uuid.uuid4())
    private = _create_follow_up(
        user,
        AgentChat.objects.create(agent=agent, user=user, private=True),
        title="Private plans",
    )
    _create_follow_up(
        user, AgentChat.objects.create(agent=agent, user=user), title="Shared plans"
    )

    shared_runner = AgentRunner(AgentChat.objects.create(agent=agent, user=user))
    notes = "\n".join(shared_runner.deps.system_notes)
    assert "Shared plans" in notes
    assert "Private plans" not in notes

    with patch(BROADCAST), patch(BROADCAST_TO_USERS):
        action_type_registry.get_by_type(StopAgentFollowUpActionType).do(user, private)
    assert "Private plans" not in json.dumps(Action.objects.get().params)


@pytest.mark.django_db
def test_follow_up_updates_only_reach_whom_the_list_shows_them(
    follow_up_setup, django_capture_on_commit_callbacks
):
    user, token, workspace, application, agent, table, status, rows = follow_up_setup
    with (
        patch(BROADCAST) as to_group,
        patch(
            "baserow_enterprise.agent_application.realtime.broadcast_to_permitted_users"
        ) as to_permitted,
        patch(BROADCAST_TO_USERS) as to_users,
        django_capture_on_commit_callbacks(execute=True),
    ):
        _create_follow_up(user, AgentChat.objects.create(agent=agent, user=user))

    assert not to_group.delay.called
    workspace_id, operation, scope, scope_id, payload = (
        to_permitted.delay.call_args.args
    )
    assert operation == "agent_application.list_follow_ups"
    assert scope_id == application.id
    assert to_users.delay.call_args.args[0] == [user.id]
