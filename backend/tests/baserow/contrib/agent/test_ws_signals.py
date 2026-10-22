from functools import partial
from uuid import uuid4

from django.db import transaction

import pytest

from baserow.contrib.agent.actions import (
    CreateAgentConversationActionType,
    CreateAgentMessageActionType,
)
from baserow.contrib.agent.models import AgentMessage


def conversation_write(data_fixture, user, agent, kind):
    if kind == "message":
        conversation = data_fixture.create_agent_conversation(user=user, agent=agent)
        return partial(
            CreateAgentMessageActionType.do,
            user,
            agent.id,
            conversation.uuid,
            uuid4(),
            "PRIVATE MESSAGE",
        )
    return partial(
        CreateAgentConversationActionType.do,
        user,
        agent.id,
        uuid4(),
        uuid4(),
        "PRIVATE MESSAGE",
    )


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["conversation", "message"])
def test_new_content_notifies_only_the_owner_after_commit_and_not_on_retry(
    data_fixture, configured_agent, mocker, django_capture_on_commit_callbacks, kind
):
    user = data_fixture.create_user(web_socket_id="source-tab")
    other_user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user, members=[other_user])
    agent = configured_agent(workspace=workspace)
    write = conversation_write(data_fixture, user, agent, kind)
    broadcast = mocker.patch(
        "baserow.contrib.agent.ws.signals.broadcast_to_users.delay"
    )

    with django_capture_on_commit_callbacks(execute=True):
        result = write()
        broadcast.assert_not_called()

    broadcast.assert_called_once_with(
        [user.id],
        {
            "type": "agent_conversation_updated",
            "agent_id": agent.id,
            "conversation_uuid": str(result.conversation.uuid),
        },
        ignore_web_socket_id="source-tab",
    )

    with django_capture_on_commit_callbacks(execute=True):
        retried = write()

    assert retried.message.id == result.message.id
    assert not retried.created
    broadcast.assert_called_once()


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["conversation", "message"])
def test_rolled_back_content_does_not_notify_other_sessions(
    data_fixture, configured_agent, mocker, django_capture_on_commit_callbacks, kind
):
    user = data_fixture.create_user()
    agent = configured_agent(user=user)
    write = conversation_write(data_fixture, user, agent, kind)
    broadcast = mocker.patch(
        "baserow.contrib.agent.ws.signals.broadcast_to_users.delay"
    )

    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(RuntimeError):
            with transaction.atomic():
                write()
                raise RuntimeError("Abort the outer transaction")

    assert not AgentMessage.objects.exists()
    broadcast.assert_not_called()
