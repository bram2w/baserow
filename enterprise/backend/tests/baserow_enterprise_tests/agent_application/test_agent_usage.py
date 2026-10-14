import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

import pytest
from freezegun import freeze_time
from pydantic_ai.models.function import DeltaToolCall, FunctionModel
from rest_framework.status import HTTP_200_OK

from baserow.api.generative_ai.serializers import GenerativeAIModelsSerializer
from baserow.core.generative_ai.registries import (
    GenerativeAIModelType,
    generative_ai_model_type_registry,
)
from baserow.core.handler import CoreHandler
from baserow_enterprise.agent_application.handler import (
    AgentApplicationHandler,
    AgentChatHandler,
)
from baserow_enterprise.agent_application.models import (
    AgentChat,
    AgentChatChannel,
    AgentChatMessage,
    AgentEmailMessage,
    AgentUsage,
)
from baserow_enterprise.agent_application.tasks import (
    clean_up_old_agent_chats,
    run_agent_chat,
)
from baserow_enterprise.agent_application.usage import AgentUsageHandler

from .test_agent_runner import register_runner_test_model_type

BROADCAST = "baserow_enterprise.agent_application.realtime.broadcast_to_channel_group"


class PricedModel(FunctionModel):
    """Answers like any test model, but presents itself as an OpenAI model, so
    pydantic-ai prices its responses with the public price list."""

    @property
    def system(self):
        return "openai"


async def _answer(messages, info):
    yield "Done."


async def _call_a_missing_tool_then_fail(messages, info):
    # The first request asks for a tool that doesn't exist, which makes
    # pydantic-ai ask again; the second request fails, so the turn errors
    # after one answered request.
    if len(messages) == 1:
        yield {0: DeltaToolCall(name="missing_tool", json_args="{}")}
        return
    raise RuntimeError("The model went away.")


class UsageTestModelType(GenerativeAIModelType):
    type = "agent_usage_test"

    def is_enabled(self, workspace=None):
        return True

    def get_enabled_models(
        self, workspace=None, settings_override=None, feature_type=None, state=None
    ):
        return ["priced", "failing"]

    def get_ai_model(self, model_name, workspace=None, settings_override=None):
        if model_name == "failing":
            return FunctionModel(stream_function=_call_a_missing_tool_then_fail)
        return PricedModel(stream_function=_answer, model_name="gpt-4o")

    def prompt(self, *args, **kwargs):
        return "Done."

    def get_settings_serializer(self):
        return GenerativeAIModelsSerializer


@pytest.fixture
def usage_setup(data_fixture):
    register_runner_test_model_type()
    try:
        generative_ai_model_type_registry.register(UsageTestModelType())
    except generative_ai_model_type_registry.already_registered_exception_class:
        pass
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    application = (
        CoreHandler()
        .create_application(user, workspace, "agent", init_with_data=True, name="Agent")
        .specific
    )
    agent = AgentApplicationHandler().get_main_agent(application)
    return user, token, workspace, application, agent


def _use_model(agent, model_type, model):
    AgentApplicationHandler().update_agent(
        agent, ai_generative_ai_type=model_type, ai_generative_ai_model=model
    )


def _run_turn(agent, user, content="Please do the thing.", broadcasts=None):
    chat = AgentChat.objects.create(agent=agent, user=user, title="Set")
    prompt = AgentChatHandler().create_message(
        chat, AgentChatMessage.Role.HUMAN, content
    )
    with patch(BROADCAST) as broadcast:
        run_agent_chat(chat.id, prompt.id)
    if broadcasts is not None:
        broadcasts.extend(call.args[1] for call in broadcast.delay.call_args_list)
    chat.refresh_from_db()
    return chat


def _get_usage(api_client, token, application, timezone_name="UTC"):
    response = api_client.get(
        reverse("api:agent:usage", kwargs={"application_id": application.id})
        + f"?timezone={timezone_name}",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    return response.json()


@pytest.mark.django_db(transaction=True)
def test_a_priced_turn_is_counted_everywhere(usage_setup, api_client):
    user, token, workspace, application, agent = usage_setup
    _use_model(agent, "agent_usage_test", "priced")

    broadcasts = []
    chat = _run_turn(agent, user, broadcasts=broadcasts)

    answer = chat.messages.get(role=AgentChatMessage.Role.AI)
    assert answer.input_tokens > 0
    assert answer.cost > 0

    # Broadcasts go through Celery as JSON, where a Decimal would fail.
    for payload in broadcasts:
        json.dumps(payload)
    finished = [
        payload["chat"]
        for payload in broadcasts
        if payload["type"] == "agent_chat_updated"
    ][-1]
    assert Decimal(finished["total_cost"]) == answer.cost
    assert {"type": "agent_usage_updated", "application_id": application.id} in (
        broadcasts
    )

    # The totals arrive before the answer completes, so the conversation
    # shows them at the same moment.
    events = [
        payload["event"]
        for payload in broadcasts
        if payload["type"] == "agent_chat_event"
    ]
    types = [event["type"] for event in events]
    last_usage = len(types) - 1 - types[::-1].index("ai/usage")
    assert last_usage < types.index("ai/message")
    assert events[last_usage]["total_input_tokens"] == chat.total_input_tokens
    assert Decimal(events[last_usage]["total_cost"]) == chat.total_cost
    assert chat.total_input_tokens == answer.input_tokens
    assert chat.total_output_tokens == answer.output_tokens
    assert chat.total_cost == answer.cost
    assert chat.unpriced_turns == 0

    lifetime = _get_usage(api_client, token, application)["lifetime"]
    assert lifetime["input_tokens"] == chat.total_input_tokens
    assert lifetime["output_tokens"] == chat.total_output_tokens
    assert Decimal(str(lifetime["cost"])) == chat.total_cost
    assert lifetime["turns"] == 1
    assert lifetime["unpriced_turns"] == 0


@pytest.mark.django_db(transaction=True)
def test_a_model_without_price_only_counts_tokens(usage_setup, api_client):
    user, token, workspace, application, agent = usage_setup
    _use_model(agent, "agent_runner_test", "test-model")

    # Untitled, so the generated title counts as well.
    chat = AgentChat.objects.create(agent=agent, user=user)
    prompt = AgentChatHandler().create_message(
        chat, AgentChatMessage.Role.HUMAN, "Please do the thing."
    )
    with patch(BROADCAST):
        run_agent_chat(chat.id, prompt.id)
    chat.refresh_from_db()

    answer = chat.messages.get(role=AgentChatMessage.Role.AI)
    assert answer.cost is None
    assert chat.total_cost == 0
    # The answer and the title.
    assert chat.unpriced_turns == 2
    assert chat.total_input_tokens > answer.input_tokens

    lifetime = _get_usage(api_client, token, application)["lifetime"]
    assert lifetime["input_tokens"] == chat.total_input_tokens
    assert lifetime["cost"] == 0
    assert lifetime["unpriced_turns"] == 2


@pytest.mark.django_db(transaction=True)
def test_a_failed_turn_still_counts_what_it_used(usage_setup):
    user, token, workspace, application, agent = usage_setup
    _use_model(agent, "agent_usage_test", "failing")

    chat = _run_turn(agent, user)

    assert chat.status == AgentChat.Status.ERROR
    assert chat.total_input_tokens > 0
    usage = AgentUsage.objects.get(application=application)
    assert usage.input_tokens == chat.total_input_tokens
    assert usage.turns == 1


@pytest.mark.django_db(transaction=True)
def test_lifetime_usage_survives_deleting_the_conversation(usage_setup, api_client):
    user, token, workspace, application, agent = usage_setup
    _use_model(agent, "agent_usage_test", "priced")
    chat = _run_turn(agent, user)
    tokens = chat.total_input_tokens

    with patch(BROADCAST):
        AgentChatHandler().delete_chat(chat)

    lifetime = _get_usage(api_client, token, application)["lifetime"]
    assert lifetime["input_tokens"] == tokens


@pytest.mark.django_db
def test_periods_follow_the_viewers_timezone(usage_setup, api_client, data_fixture):
    user, token, workspace, application, agent = usage_setup
    handler = AgentUsageHandler()

    def at(value):
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)

    handler.record(application.id, 1, 0, Decimal("1"), at=at("2026-09-20T12:00"))
    # Monday 12 October, the start of the week.
    handler.record(application.id, 10, 0, Decimal("2"), at=at("2026-10-12T09:00"))
    # Late on Wednesday in UTC, but already Thursday in Amsterdam.
    handler.record(application.id, 100, 0, None, at=at("2026-10-14T22:30"))
    handler.record(application.id, 1000, 0, Decimal("4"), at=at("2026-10-15T08:00"))

    with freeze_time("2026-10-15T12:00:00Z"):
        # A token from before the frozen time would have expired.
        token = data_fixture.generate_token(user)
        in_utc = _get_usage(api_client, token, application)
        in_amsterdam = _get_usage(api_client, token, application, "Europe/Amsterdam")

    assert in_utc["today"]["input_tokens"] == 1000
    assert in_amsterdam["today"]["input_tokens"] == 1100
    assert in_amsterdam["today"]["unpriced_turns"] == 1
    assert in_utc["week"]["input_tokens"] == 1110
    assert in_utc["month"]["input_tokens"] == 1110
    assert in_utc["lifetime"]["input_tokens"] == 1111
    assert in_utc["lifetime"]["cost"] == 7
    assert in_utc["lifetime"]["turns"] == 4
    # Two turns in the same hour share a row.
    handler.record(application.id, 1, 0, None, at=at("2026-10-15T08:30"))
    assert AgentUsage.objects.filter(application=application).count() == 4


@pytest.mark.django_db
def test_usage_endpoint_query_count_does_not_grow(usage_setup, api_client):
    user, token, workspace, application, agent = usage_setup
    handler = AgentUsageHandler()
    handler.record(application.id, 1, 1, None)

    def count_queries():
        with CaptureQueriesContext(connection) as queries:
            _get_usage(api_client, token, application)
        return len(queries)

    # The first request also fills some caches.
    count_queries()
    few = count_queries()
    for day in range(1, 29):
        handler.record(
            application.id,
            1,
            1,
            Decimal("0.01"),
            at=datetime(2026, 9, day, tzinfo=ZoneInfo("UTC")),
        )
    assert count_queries() == few


@pytest.mark.django_db
def test_old_email_index_rows_age_out_with_their_conversation(
    usage_setup, data_fixture
):
    user, token, workspace, application, agent = usage_setup
    channel = AgentChatChannel.objects.create(
        application=application, type="email", config={}
    )
    with freeze_time("2026-01-01T10:00:00Z"):
        gone = AgentEmailMessage.objects.create(
            channel=channel, session_key="gone", direction="inbound"
        )
        still_active = AgentEmailMessage.objects.create(
            channel=channel, session_key="active", direction="inbound"
        )
    recent = AgentEmailMessage.objects.create(
        channel=channel, session_key="gone", direction="inbound"
    )
    # The thread kept going, so its first mail is still needed for replies.
    AgentChat.objects.create(
        agent=agent,
        source=AgentChat.Source.CHANNEL,
        channel=channel,
        channel_session_key="active",
    )

    with patch(BROADCAST):
        clean_up_old_agent_chats()

    remaining = set(AgentEmailMessage.objects.values_list("id", flat=True))
    assert remaining == {still_active.id, recent.id}
    assert gone.id not in remaining
