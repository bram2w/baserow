from unittest.mock import patch
from uuid import uuid4

from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from baserow.core.exceptions import PermissionException
from baserow.core.handler import CoreHandler
from baserow_enterprise.agent_application.handler import (
    AgentApplicationHandler,
    AgentChatHandler,
)
from baserow_enterprise.agent_application.models import AgentChat
from baserow_enterprise.agent_application.operations import (
    ContinueTriggeredAgentChatOperationType,
    StartAgentChatOperationType,
)
from baserow_enterprise.agent_application.permission_manager import (
    AgentChatRolePermissionManagerType,
)


def _create_agent(user, workspace):
    application = (
        CoreHandler()
        .create_application(user, workspace, "agent", init_with_data=True, name="Agent")
        .specific
    )
    agent = AgentApplicationHandler().get_main_agent(application)
    AgentApplicationHandler().update_agent(
        agent,
        ai_generative_ai_type="test_generative_ai",
        ai_generative_ai_model="test_1",
    )
    return application, agent


def _is_allowed(user, operation, application):
    try:
        return CoreHandler().check_permissions(
            user,
            operation.type,
            workspace=application.workspace,
            context=application.application_ptr,
        )
    except PermissionException:
        return False


@pytest.mark.django_db
def test_minimum_roles_for_starting_and_continuing_chats(
    data_fixture, enable_enterprise, synced_roles
):
    admin = data_fixture.create_user()
    builder = data_fixture.create_user()
    editor = data_fixture.create_user()
    viewer = data_fixture.create_user()
    workspace = data_fixture.create_workspace(
        user=admin,
        custom_permissions=[
            (builder, "BUILDER"),
            (editor, "EDITOR"),
            (viewer, "VIEWER"),
        ],
    )
    application, _ = _create_agent(admin, workspace)

    # Editors and up by default; viewers never run conversations.
    for operation in (
        StartAgentChatOperationType,
        ContinueTriggeredAgentChatOperationType,
    ):
        assert _is_allowed(editor, operation, application)
        assert not _is_allowed(viewer, operation, application)

    application.start_chat_min_role = "BUILDER"
    application.continue_chat_min_role = "ADMIN"
    application.save()

    assert not _is_allowed(editor, StartAgentChatOperationType, application)
    assert _is_allowed(builder, StartAgentChatOperationType, application)
    assert not _is_allowed(
        builder, ContinueTriggeredAgentChatOperationType, application
    )
    assert _is_allowed(admin, ContinueTriggeredAgentChatOperationType, application)

    application.start_chat_min_role = "NOBODY"
    application.save()
    assert not _is_allowed(admin, StartAgentChatOperationType, application)


@pytest.mark.django_db
def test_minimum_roles_without_role_based_access(data_fixture):
    admin = data_fixture.create_user()
    member = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin, members=[member])
    application, _ = _create_agent(admin, workspace)
    application.start_chat_min_role = "BUILDER"
    application.continue_chat_min_role = "ADMIN"
    application.save()

    # Members may build everything without roles, so only admin-only
    # settings set them apart.
    assert _is_allowed(member, StartAgentChatOperationType, application)
    assert not _is_allowed(member, ContinueTriggeredAgentChatOperationType, application)
    assert _is_allowed(admin, ContinueTriggeredAgentChatOperationType, application)


@pytest.mark.django_db
def test_minimum_roles_permissions_object(
    data_fixture, enable_enterprise, synced_roles
):
    admin = data_fixture.create_user()
    editor = data_fixture.create_user()
    workspace = data_fixture.create_workspace(
        user=admin, custom_permissions=[(editor, "EDITOR")]
    )
    application, _ = _create_agent(admin, workspace)

    permissions = AgentChatRolePermissionManagerType().get_permissions_object(
        editor, workspace
    )
    assert permissions == {
        "default": ["EDITOR"],
        "applications": {application.id: ["EDITOR"]},
    }


@pytest.mark.django_db(transaction=True)
def test_send_message_respects_minimum_roles(
    api_client, data_fixture, enable_enterprise, synced_roles
):
    admin = data_fixture.create_user()
    editor, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(
        user=admin, custom_permissions=[(editor, "EDITOR")]
    )
    application, agent = _create_agent(admin, workspace)
    application.start_chat_min_role = "BUILDER"
    application.continue_chat_min_role = "BUILDER"
    application.save()
    triggered = AgentChatHandler().create_triggered_chat(agent, "periodic")

    def post(chat_uuid):
        return api_client.post(
            reverse(
                "api:agent:chat_messages",
                kwargs={"application_id": application.id, "chat_uuid": chat_uuid},
            ),
            {"content": "Hello"},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    with (
        patch("baserow_enterprise.agent_application.tasks.run_agent_chat.delay"),
        patch(
            "baserow_enterprise.agent_application.realtime.broadcast_to_channel_group"
        ),
    ):
        assert post(uuid4()).status_code == HTTP_401_UNAUTHORIZED
        assert post(triggered.uuid).status_code == HTTP_401_UNAUTHORIZED
        assert not AgentChat.objects.filter(source="manual").exists()

        application.start_chat_min_role = "EDITOR"
        application.continue_chat_min_role = "EDITOR"
        application.save()
        assert post(uuid4()).status_code == HTTP_202_ACCEPTED
        assert post(triggered.uuid).status_code == HTTP_202_ACCEPTED


@pytest.mark.django_db(transaction=True)
def test_private_chats_are_only_visible_to_their_owner(api_client, data_fixture):
    owner, owner_token = data_fixture.create_user_and_token()
    other, other_token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=owner, members=[other])
    application, agent = _create_agent(owner, workspace)
    chat_uuid = uuid4()

    with (
        patch("baserow_enterprise.agent_application.tasks.run_agent_chat.delay"),
        patch(
            "baserow_enterprise.agent_application.realtime.broadcast_to_channel_group"
        ) as group_mock,
        patch(
            "baserow_enterprise.agent_application.realtime.broadcast_to_users"
        ) as users_mock,
    ):
        response = api_client.post(
            reverse(
                "api:agent:chat_messages",
                kwargs={"application_id": application.id, "chat_uuid": chat_uuid},
            ),
            {"content": "Just for me", "private": True},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {owner_token}",
        )
    assert response.status_code == HTTP_202_ACCEPTED
    chat = AgentChat.objects.get(uuid=chat_uuid)
    assert chat.private is True
    # Nothing about the conversation reaches the application's page group.
    assert not [
        call
        for call in group_mock.delay.call_args_list
        if call[0][1]["type"].startswith("agent_chat")
    ]
    assert {call[0][0][0] for call in users_mock.delay.call_args_list} == {owner.id}

    list_url = reverse("api:agent:chats", kwargs={"application_id": application.id})
    owner_list = api_client.get(list_url, HTTP_AUTHORIZATION=f"JWT {owner_token}")
    assert [c["uuid"] for c in owner_list.json()["results"]] == [str(chat_uuid)]
    assert owner_list.json()["results"][0]["private"] is True
    other_list = api_client.get(list_url, HTTP_AUTHORIZATION=f"JWT {other_token}")
    assert other_list.json()["results"] == []

    transcript_url = reverse(
        "api:agent:chat_messages",
        kwargs={"application_id": application.id, "chat_uuid": chat_uuid},
    )
    response = api_client.get(transcript_url, HTTP_AUTHORIZATION=f"JWT {other_token}")
    assert response.status_code == HTTP_404_NOT_FOUND
    response = api_client.get(transcript_url, HTTP_AUTHORIZATION=f"JWT {owner_token}")
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_list_chats_filters_by_origin(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    application, agent = _create_agent(user, workspace)
    manual = AgentChat.objects.create(agent=agent, user=user)
    periodic = AgentChatHandler().create_triggered_chat(agent, "periodic")
    AgentChatHandler().create_triggered_chat(agent, "rows_created")
    service = AgentChat.objects.create(agent=agent, source=AgentChat.Source.SERVICE)

    def uuids(origin):
        response = api_client.get(
            reverse("api:agent:chats", kwargs={"application_id": application.id})
            + f"?origin={origin}",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == HTTP_200_OK
        return {chat["uuid"] for chat in response.json()["results"]}

    assert uuids("manual") == {str(manual.uuid)}
    assert uuids("trigger:periodic") == {str(periodic.uuid)}
    assert uuids("service") == {str(service.uuid)}
    assert uuids("channel:slack") == set()
    assert uuids("mine") == {str(manual.uuid)}
    assert len(uuids("")) == 4


@pytest.mark.django_db(transaction=True)
def test_only_the_starter_switches_a_chat_between_private_and_public(
    api_client, data_fixture
):
    owner, owner_token = data_fixture.create_user_and_token()
    other, other_token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=owner, members=[other])
    application, agent = _create_agent(owner, workspace)
    chat = AgentChat.objects.create(agent=agent, user=owner)
    url = reverse("api:agent:chat_item", kwargs={"chat_uuid": chat.uuid})
    list_url = reverse("api:agent:chats", kwargs={"application_id": application.id})

    response = api_client.patch(
        url, {"private": True}, format="json", HTTP_AUTHORIZATION=f"JWT {other_token}"
    )
    assert response.status_code == HTTP_403_FORBIDDEN
    assert response.json()["error"] == "ERROR_AGENT_CHAT_NOT_OWNED"

    with (
        patch(
            "baserow_enterprise.agent_application.realtime.broadcast_to_channel_group"
        ) as group_mock,
        patch("baserow_enterprise.agent_application.realtime.broadcast_to_users"),
    ):
        response = api_client.patch(
            url,
            {"private": True},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {owner_token}",
        )
    assert response.status_code == HTTP_200_OK
    assert response.json()["private"] is True
    # Everybody else drops it, the owner keeps it.
    assert {
        "type": "agent_chat_deleted",
        "chat_id": chat.id,
        "except_user_id": owner.id,
    } in [call[0][1] for call in group_mock.delay.call_args_list]
    other_list = api_client.get(list_url, HTTP_AUTHORIZATION=f"JWT {other_token}")
    assert other_list.json()["results"] == []

    with patch(
        "baserow_enterprise.agent_application.realtime.broadcast_to_channel_group"
    ):
        api_client.patch(
            url,
            {"private": False},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {owner_token}",
        )
    other_list = api_client.get(list_url, HTTP_AUTHORIZATION=f"JWT {other_token}")
    assert [c["uuid"] for c in other_list.json()["results"]] == [str(chat.uuid)]


@pytest.mark.django_db(transaction=True)
def test_a_running_chat_made_private_stops_streaming_to_others(data_fixture):
    from baserow_enterprise.agent_application.realtime import broadcast_chat_event

    owner = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=owner)
    application, agent = _create_agent(owner, workspace)
    # The runner keeps the instance it loaded when the run started.
    running = AgentChat.objects.create(agent=agent, user=owner)

    with (
        patch(
            "baserow_enterprise.agent_application.realtime.broadcast_to_channel_group"
        ),
        patch("baserow_enterprise.agent_application.realtime.broadcast_to_users"),
    ):
        AgentChatHandler().update_chat(
            AgentChat.objects.get(id=running.id), private=True
        )

    with (
        patch(
            "baserow_enterprise.agent_application.realtime.broadcast_to_channel_group"
        ) as group_mock,
        patch(
            "baserow_enterprise.agent_application.realtime.broadcast_to_users"
        ) as users_mock,
    ):
        broadcast_chat_event(running, {"type": "ai/answer_chunk", "content": "x"})

    assert not group_mock.delay.called
    assert users_mock.delay.call_args[0][0] == [owner.id]


@pytest.mark.django_db
def test_a_picked_up_triggered_chat_cannot_be_made_private(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    application, agent = _create_agent(user, workspace)
    # Writing in a triggered conversation makes the writer its user.
    chat = AgentChatHandler().create_triggered_chat(agent, "periodic")
    chat.user = user
    chat.save()

    response = api_client.patch(
        reverse("api:agent:chat_item", kwargs={"chat_uuid": chat.uuid}),
        {"private": True},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN
    chat.refresh_from_db()
    assert chat.private is False


@pytest.mark.django_db(transaction=True)
def test_steps_acting_as_the_user_are_decided_by_that_user_only(
    api_client, data_fixture, enable_enterprise, synced_roles
):
    from baserow_enterprise.agent_application.models import AgentChatToolApproval
    from baserow_enterprise.agent_application.tools.handler import AgentToolHandler
    from baserow_enterprise.agent_application.tools.service_tool import (
        get_service_tool_name,
    )

    admin = data_fixture.create_user()
    editor, editor_token = data_fixture.create_user_and_token()
    builder, builder_token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(
        user=admin, custom_permissions=[(editor, "EDITOR"), (builder, "BUILDER")]
    )
    application, agent = _create_agent(admin, workspace)
    application.act_as_user = True
    application.save()
    tool = AgentToolHandler().create_tool(
        admin, agent, "service", name="Notify", service_type_str="smtp_email"
    )

    def decide(token, tool_name):
        chat = AgentChat.objects.create(
            agent=agent, user=editor, status=AgentChat.Status.AWAITING_APPROVAL
        )
        approval = AgentChatToolApproval.objects.create(
            chat=chat, tool_call_id="c1", tool_name=tool_name, tool_args={}
        )
        with (
            patch("baserow_enterprise.agent_application.tasks.resume_agent_chat"),
            patch(
                "baserow_enterprise.agent_application.realtime."
                "broadcast_to_channel_group"
            ),
            patch(
                "baserow_enterprise.agent_application.realtime."
                "broadcast_to_permitted_users"
            ),
        ):
            return api_client.post(
                reverse("api:agent:chat_approvals", kwargs={"chat_uuid": chat.uuid}),
                {"decisions": [{"id": approval.id, "approved": True}]},
                format="json",
                HTTP_AUTHORIZATION=f"JWT {token}",
            )

    acting = get_service_tool_name(tool)
    # It spends the editor's permissions, so it's the editor's call alone.
    assert decide(builder_token, acting).status_code == HTTP_401_UNAUTHORIZED
    assert decide(editor_token, acting).status_code == HTTP_200_OK
    # Other steps keep needing the role that decides approvals.
    assert decide(editor_token, "send_email").status_code == HTTP_401_UNAUTHORIZED
    assert decide(builder_token, "send_email").status_code == HTTP_200_OK


@pytest.mark.django_db(transaction=True)
def test_run_agent_chats_need_the_continue_role(
    api_client, data_fixture, enable_enterprise, synced_roles
):
    admin = data_fixture.create_user()
    editor, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(
        user=admin, custom_permissions=[(editor, "EDITOR")]
    )
    application, agent = _create_agent(admin, workspace)
    application.continue_chat_min_role = "BUILDER"
    application.save()
    # Started by an automation: nobody owns it yet.
    chat = AgentChat.objects.create(agent=agent, source=AgentChat.Source.SERVICE)

    with (
        patch("baserow_enterprise.agent_application.tasks.run_agent_chat.delay"),
        patch(
            "baserow_enterprise.agent_application.realtime.broadcast_to_channel_group"
        ),
    ):
        response = api_client.post(
            reverse(
                "api:agent:chat_messages",
                kwargs={"application_id": application.id, "chat_uuid": chat.uuid},
            ),
            {"content": "Hello"},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    chat.refresh_from_db()
    assert chat.user_id is None
