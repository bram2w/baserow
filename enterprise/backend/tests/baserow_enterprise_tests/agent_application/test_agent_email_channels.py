from unittest.mock import Mock, patch

from django.core import mail
from django.test import override_settings

import pytest
from rest_framework.exceptions import ValidationError

from baserow.contrib.integrations.core.inbound_email import InboundEmailHandler
from baserow.core.handler import CoreHandler
from baserow_enterprise.agent_application.approval_preview import (
    build_approval_preview,
)
from baserow_enterprise.agent_application.channels.email import (
    EmailReplyNotPossible,
    HostedEmailAgentChatChannelType,
    ReceivedEmail,
)
from baserow_enterprise.agent_application.channels.email_text import (
    html_to_text,
    normalize_subject,
    strip_quoted_reply,
)
from baserow_enterprise.agent_application.channels.mailbox import (
    GmailAgentChatChannelType,
    OutlookAgentChatChannelType,
    poll_mailbox_channels,
    sender_authenticated,
)
from baserow_enterprise.agent_application.channels.registries import (
    start_channel_chat,
)
from baserow_enterprise.agent_application.handler import AgentApplicationHandler
from baserow_enterprise.agent_application.models import (
    AgentChat,
    AgentChatChannel,
    AgentChatMessage,
    AgentEmailMessage,
)
from baserow_enterprise.agent_application.tools.gating import (
    ApprovalRequiredToolset,
)

from .test_agent_runner import register_runner_test_model_type

DOMAIN = "agents.example.com"
INBOUND = dict(
    INBOUND_EMAIL_DOMAIN=DOMAIN,
    INBOUND_EMAIL_WEBHOOK_SECRET="secret-secret",
    INBOUND_EMAIL_RECEIVER_URL="http://receiver:8880",
    FROM_EMAIL="no-reply@example.com",
)
TASK = "baserow_enterprise.agent_application.tasks.process_agent_channel_message.delay"
SMTP_OK = (
    "baserow.contrib.integrations.core.service_types.CoreSMTPEmailServiceType"
    ".instance_smtp_unavailable_reason"
)
MAILBOX_REQUEST = "baserow_enterprise.agent_application.channels.mailbox._json_request"


def make_mox_payload(rcpt_to, **overrides):
    """A mox `webhook.Incoming` delivery, the shape the receiver posts."""

    payload = {
        "From": [{"Name": "Sender", "Address": "sender@example.com"}],
        "To": [{"Name": "", "Address": rcpt_to}],
        "CC": [],
        "ReplyTo": [],
        "Subject": "Hello",
        "Text": "Body",
        "HTML": "",
        "MessageID": "<unique-id-123@example.com>",
        "InReplyTo": "",
        "References": [],
        "Structure": {"ContentType": "text/plain", "Parts": []},
        "Meta": {
            "MsgID": 1,
            "Received": "2026-10-07T08:00:00Z",
            "MsgFromValidated": True,
            "DKIMVerifiedDomains": ["example.com"],
            "RemoteIP": "203.0.113.5",
            "RcptTo": rcpt_to,
            "Automated": False,
        },
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def email_setup(data_fixture):
    register_runner_test_model_type()
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    application = (
        CoreHandler()
        .create_application(user, workspace, "agent", init_with_data=True, name="Help")
        .specific
    )
    agent = AgentApplicationHandler().get_main_agent(application)
    AgentApplicationHandler().update_agent(
        agent, ai_generative_ai_type="agent_runner_test", ai_generative_ai_model="m"
    )
    return user, application, agent


def _hosted_channel(application, **config):
    with override_settings(**INBOUND):
        prepared = HostedEmailAgentChatChannelType().prepare_config(
            {"localpart": "support", **config}
        )
    return AgentChatChannel.objects.create(
        application=application, type="email", name="Support mail", config=prepared
    )


def test_quoted_replies_and_subjects_are_normalized():
    assert (
        strip_quoted_reply(
            "Thanks, that works!\n\nOn Mon, Oct 6, 2026 at 9:00 AM Help <help@x.com> "
            "wrote:\n> Hello\n> Try this"
        )
        == "Thanks, that works!"
    )
    assert strip_quoted_reply("Yes please\n\n> earlier\n> lines\n") == "Yes please"
    assert strip_quoted_reply("Done.\n-- \nAnn\nCEO") == "Done."
    assert (
        strip_quoted_reply(
            "Ok\n\nFrom: Help <help@x.com>\nSent: Monday\nTo: me\nSubject: Re: x\n\nold"
        )
        == "Ok"
    )
    assert html_to_text("<p>Hi<br>there</p><style>x{}</style>&amp; bye") == (
        "Hi\nthere\n& bye"
    )
    assert normalize_subject("RE: Fwd: Re: Order 12 ") == "order 12"
    assert normalize_subject("Order 12") == "order 12"


@pytest.mark.django_db
@override_settings(**INBOUND)
def test_hosted_channel_config_validates_the_address(email_setup):
    user, application, agent = email_setup
    channel_type = HostedEmailAgentChatChannelType()
    config = channel_type.prepare_config({})
    assert len(config["token"]) == 32
    assert config["localpart"] == ""
    assert config["require_approval"] is True
    assert config["allowed_sender_domains"] == []

    with pytest.raises(ValidationError):
        channel_type.prepare_config({"localpart": "Bad Address!"})
    with pytest.raises(ValidationError):
        channel_type.prepare_config({"localpart": "postmaster"})
    with pytest.raises(ValidationError):
        channel_type.prepare_config({"localpart": "test-support"})

    channel = _hosted_channel(application, allowed_sender_domains="Example.com, x.org")
    assert channel.config["allowed_sender_domains"] == ["example.com", "x.org"]
    assert channel_type.address(channel) == f"support@{DOMAIN}"

    # Another agent cannot take the same address; the channel itself can keep it.
    with pytest.raises(ValidationError):
        channel_type.prepare_config({"localpart": "support"})
    kept = channel_type.prepare_config(
        {"localpart": "support"}, existing_config=channel.config
    )
    assert kept["token"] == channel.config["token"]

    # A copy must not answer to the original's address.
    copied = channel_type.prepare_imported_config(channel.config)
    assert copied["localpart"] == "" and copied["token"] != channel.config["token"]

    public = channel_type.get_public_config(channel)
    assert public["address"] == f"support@{DOMAIN}"
    assert public["inbound_configured"] is True

    with pytest.raises(ValidationError):
        channel_type.prepare_config({"smtp_integration_id": 5})


@pytest.mark.django_db
def test_hosted_channel_needs_inbound_email_configured(email_setup):
    with pytest.raises(ValidationError) as exc:
        HostedEmailAgentChatChannelType().prepare_config({})
    assert "not configured" in str(exc.value)


@pytest.mark.django_db
@override_settings(**INBOUND)
def test_inbound_mail_routes_to_the_channel_and_maps_replies(email_setup):
    user, application, agent = email_setup
    channel = _hosted_channel(application)
    handler = InboundEmailHandler()

    with patch(TASK) as delay:
        status = handler.handle_webhook_payload(
            make_mox_payload(
                f"support@{DOMAIN}",
                MessageID="<m1@customer.example>",
                Subject="Order 12 is late",
                Text="Where is my order?\n\n-- \nAnn",
                From=[{"Name": "Ann", "Address": "ann@customer.example"}],
            )
        )
    assert status == "accepted"
    delay.assert_called_once()
    channel_id, session_key, text, sender_name, attachments, title = (
        delay.call_args.args
    )
    assert channel_id == channel.id
    assert len(session_key) == 12
    assert text.startswith(
        "From: Ann <ann@customer.example>\nSubject: Order 12 is late"
    )
    assert text.endswith("Where is my order?")
    assert title == "Email: Order 12 is late"
    record = AgentEmailMessage.objects.get(channel=channel)
    assert record.session_key == session_key
    assert record.direction == "inbound"
    assert record.message_id == "<m1@customer.example>"

    # The same delivery again is a duplicate.
    with patch(TASK) as delay:
        assert (
            handler.handle_webhook_payload(
                make_mox_payload(f"support@{DOMAIN}", MessageID="<m1@customer.example>")
            )
            == "duplicate"
        )
    delay.assert_not_called()

    # The conversation exists once the task ran; later mail must find it.
    chat = AgentChat.objects.create(
        agent=agent,
        source=AgentChat.Source.CHANNEL,
        channel=channel,
        channel_session_key=session_key,
    )
    channel_type = HostedEmailAgentChatChannelType()

    # 1. By the reply address tag.
    assert (
        channel_type.find_session_key(
            channel,
            ReceivedEmail(
                from_address="ann@customer.example", recipient_tag=session_key
            ),
        )
        == session_key
    )
    # 2. By the threading headers, including a reference deep in the chain.
    assert (
        channel_type.find_session_key(
            channel,
            ReceivedEmail(
                from_address="other@customer.example",
                references=["<x@y>", "<m1@customer.example>"],
            ),
        )
        == session_key
    )
    # 3. By the same sender and subject within the window.
    assert (
        channel_type.find_session_key(
            channel,
            ReceivedEmail(
                from_address="Ann@Customer.example", subject="Re: order 12 is late"
            ),
        )
        == session_key
    )
    # Nothing in common: a new conversation.
    assert (
        channel_type.find_session_key(
            channel, ReceivedEmail(from_address="bob@other.example", subject="Hi")
        )
        is None
    )

    # Mail the channel sent itself, and senders outside the allowed domains,
    # are ignored.
    assert (
        channel_type.receive_email(
            channel, ReceivedEmail(from_address="no-reply@example.com", subject="x")
        )
        is False
    )
    channel.config["allowed_sender_domains"] = ["customer.example"]
    assert (
        channel_type.receive_email(
            channel, ReceivedEmail(from_address="eve@evil.example", subject="x")
        )
        is False
    )
    assert chat.id


@pytest.mark.django_db
@override_settings(
    **INBOUND, CELERY_EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
def test_hosted_reply_threads_and_records_the_message(email_setup):
    user, application, agent = email_setup
    channel = _hosted_channel(application, from_name="Help desk")
    channel_type = HostedEmailAgentChatChannelType()
    channel_type.receive_email(
        channel,
        ReceivedEmail(
            from_address="ann@customer.example",
            from_name="Ann",
            subject="Order 12 is late",
            message_id="<m1@customer.example>",
            references=["<m0@customer.example>"],
            text="Where is it?",
        ),
    )
    session_key = AgentEmailMessage.objects.get(channel=channel).session_key
    chat = AgentChat.objects.create(
        agent=agent,
        source=AgentChat.Source.CHANNEL,
        channel=channel,
        channel_session_key=session_key,
    )

    with patch(SMTP_OK, return_value=None):
        sent = channel_type.reply(channel, chat, "It ships tomorrow.\n\nHelp desk")

    assert sent == {"to": "ann@customer.example", "subject": "Re: Order 12 is late"}
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["ann@customer.example"]
    assert message.from_email == "Help desk <no-reply@example.com>"
    assert message.reply_to == [f"support+{session_key}@{DOMAIN}"]
    assert message.extra_headers["In-Reply-To"] == "<m1@customer.example>"
    assert message.extra_headers["References"] == (
        "<m0@customer.example> <m1@customer.example>"
    )
    assert message.extra_headers["Message-ID"].endswith(f"@{DOMAIN}>")
    assert message.body == "It ships tomorrow.\n\nHelp desk"

    outbound = AgentEmailMessage.objects.get(channel=channel, direction="outbound")
    assert outbound.message_id == message.extra_headers["Message-ID"]
    assert outbound.session_key == session_key
    # Ann answering our message maps back, by our own Message-ID.
    assert (
        channel_type.find_session_key(
            channel,
            ReceivedEmail(
                from_address="ann@customer.example", in_reply_to=outbound.message_id
            ),
        )
        == session_key
    )

    empty = AgentChat.objects.create(
        agent=agent,
        source=AgentChat.Source.CHANNEL,
        channel=channel,
        channel_session_key="nobody",
    )
    with pytest.raises(EmailReplyNotPossible):
        channel_type.reply(channel, empty, "hi")


@pytest.mark.django_db
@override_settings(**INBOUND)
def test_email_channel_hooks_keep_outsiders_out_of_the_loop(email_setup):
    user, application, agent = email_setup
    channel = _hosted_channel(application)
    channel_type = HostedEmailAgentChatChannelType()
    with patch(TASK):
        channel_type.receive_email(
            channel,
            ReceivedEmail(
                from_address="ann@customer.example", subject="Hi", text="Hello"
            ),
        )
    session_key = AgentEmailMessage.objects.get(channel=channel).session_key

    with patch("baserow_enterprise.agent_application.tasks.run_agent_chat"):
        message = start_channel_chat(
            channel, session_key, "From: ann\n\nHello", title="Email: Hi"
        )
    chat = message.chat
    assert chat.title == "Email: Hi"
    assert chat.channel_session_key == session_key

    # The reply tool is there, behind the approval queue by default.
    toolsets = channel_type.get_toolsets(channel, chat)
    assert len(toolsets) == 1 and isinstance(toolsets[0], ApprovalRequiredToolset)
    channel.config["require_approval"] = False
    assert not isinstance(
        channel_type.get_toolsets(channel, chat)[0], ApprovalRequiredToolset
    )

    # Run outcomes are never mailed to the person.
    channel_type.deliver_outcome(channel, chat, AgentChat.Status.ERROR, "oops")
    channel_type.deliver_outcome(channel, chat, AgentChat.Status.IDLE, "answer")
    assert (
        AgentEmailMessage.objects.filter(channel=channel, direction="outbound").count()
        == 0
    )

    # A mail during an approval is kept for the reviewer instead of refused.
    chat.status = AgentChat.Status.AWAITING_APPROVAL
    chat.save(update_fields=["status"])
    assert start_channel_chat(channel, session_key, "From: ann\n\nStill there?") is None
    assert chat.messages.filter(role=AgentChatMessage.Role.HUMAN).count() == 2

    preview = build_approval_preview(chat, None, "reply_by_email", {"body": "Yes!"})
    assert preview == {
        "kind": "email",
        "body": "Yes!",
        "to": "ann@customer.example",
        "subject": "Re: Hi",
    }
    assert channel_type.get_system_notes(channel)[0].startswith(
        "This conversation is an email thread"
    )


@pytest.mark.django_db
def test_gmail_channel_polls_the_label_and_replies_in_the_thread(
    email_setup, data_fixture
):
    user, application, agent = email_setup
    integration = data_fixture.create_google_integration(
        application=application, account_email="help@company.example"
    )
    channel_type = GmailAgentChatChannelType()
    config = channel_type.prepare_config(
        {"integration_id": integration.id, "label": "Agent", "alias": ""}
    )
    channel = AgentChatChannel.objects.create(
        application=application, type="gmail", name="Gmail", config=config
    )
    token = patch(
        "baserow_enterprise.agent_application.channels.mailbox"
        ".OAuth2IntegrationHandler.get_access_token",
        return_value="at",
    )

    # First poll only takes note of where the mailbox is.
    with token, patch(MAILBOX_REQUEST, return_value=(200, {"historyId": "100"})):
        poll_mailbox_channels()
    channel.refresh_from_db()
    assert channel.config["cursor"] == "100"

    def b64(text):
        import base64

        return base64.urlsafe_b64encode(text.encode()).decode()

    responses = {
        "labels": (200, {"labels": [{"id": "Label_7", "name": "Agent"}]}),
        "history": (
            200,
            {
                "historyId": "120",
                "history": [
                    {
                        "messagesAdded": [
                            {"message": {"id": "msg1", "labelIds": ["INBOX"]}}
                        ]
                    },
                    {
                        "messagesAdded": [
                            {"message": {"id": "sent1", "labelIds": ["SENT"]}}
                        ]
                    },
                ],
            },
        ),
        "messages/msg1": (
            200,
            {
                "id": "msg1",
                "threadId": "thread-1",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "Ann <ann@customer.example>"},
                        {"name": "To", "value": "help@company.example"},
                        {"name": "Subject", "value": "Invoice"},
                        {"name": "Message-ID", "value": "<g1@mail.gmail.com>"},
                    ],
                    "parts": [
                        {
                            "mimeType": "text/plain",
                            "body": {"data": b64("Please resend.")},
                        },
                        {
                            "mimeType": "application/pdf",
                            "filename": "invoice.pdf",
                            "body": {"attachmentId": "att1"},
                        },
                    ],
                },
            },
        ),
        "attachments/att1": (200, {"data": b64("%PDF-1.4 fake")}),
    }

    def fake_request(method, url, headers, params=None, json=None):
        for key, answer in responses.items():
            if url.endswith(key):
                assert headers["Authorization"] == "Bearer at"
                return answer
        raise AssertionError(f"unexpected request {method} {url}")

    with token, patch(MAILBOX_REQUEST, side_effect=fake_request), patch(TASK) as delay:
        poll_mailbox_channels()

    channel.refresh_from_db()
    assert channel.config["cursor"] == "120"
    assert channel.config["label_id"] == "Label_7"
    delay.assert_called_once()
    _, session_key, text, _, attachments, title = delay.call_args.args
    assert session_key == "thread-1"
    assert "Attachments: invoice.pdf" in text
    assert text.endswith("Please resend.")
    assert attachments[0]["visible_name"] == "invoice.pdf"
    record = AgentEmailMessage.objects.get(channel=channel)
    assert record.thread_key == "thread-1"
    assert record.provider_message_id == "msg1"

    chat = AgentChat.objects.create(
        agent=agent,
        source=AgentChat.Source.CHANNEL,
        channel=channel,
        channel_session_key="thread-1",
    )
    calls = []

    def send_request(method, url, headers, params=None, json=None):
        calls.append((method, url, params, json))
        if url.endswith("messages/send"):
            return 200, {"id": "sent-9"}
        return 200, {
            "payload": {"headers": [{"name": "Message-ID", "value": "<r1@gmail>"}]}
        }

    with token, patch(MAILBOX_REQUEST, side_effect=send_request):
        sent = channel_type.reply(channel, chat, "Attached again.")
    assert sent == {"to": "ann@customer.example", "subject": "Re: Invoice"}
    method, url, _, payload = calls[0]
    assert (method, url.split("/")[-2:]) == ("POST", ["messages", "send"])
    assert payload["threadId"] == "thread-1"
    import base64

    raw = base64.urlsafe_b64decode(payload["raw"]).decode()
    assert "In-Reply-To: <g1@mail.gmail.com>" in raw
    assert "References: <g1@mail.gmail.com>" in raw
    assert (
        AgentEmailMessage.objects.get(channel=channel, direction="outbound").message_id
        == "<r1@gmail>"
    )

    # The polling channel's own mail never triggers it.
    assert channel_type.own_addresses(channel) == {"help@company.example"}


@pytest.mark.django_db
def test_outlook_channel_polls_a_folder_with_delta_and_replies(
    email_setup, data_fixture
):
    user, application, agent = email_setup
    integration = data_fixture.create_microsoft_integration(
        application=application, account_email="help@contoso.example"
    )
    channel_type = OutlookAgentChatChannelType()
    config = channel_type.prepare_config(
        {
            "integration_id": integration.id,
            "folder": "inbox",
            "alias": "support@contoso.example",
        }
    )
    channel = AgentChatChannel.objects.create(
        application=application, type="outlook", name="Outlook", config=config
    )
    token = patch(
        "baserow_enterprise.agent_application.channels.mailbox"
        ".OAuth2IntegrationHandler.get_access_token",
        return_value="at",
    )

    # The first round walks the folder without reading it.
    first = [
        (200, {"value": [{"id": "old1"}], "@odata.nextLink": "https://graph/next"}),
        (
            200,
            {
                "value": [{"id": "old2"}],
                "@odata.deltaLink": "https://graph/delta?token=1",
            },
        ),
    ]
    with token, patch(MAILBOX_REQUEST, side_effect=first), patch(TASK) as delay:
        poll_mailbox_channels()
    delay.assert_not_called()
    channel.refresh_from_db()
    assert channel.config["cursor"] == "https://graph/delta?token=1"

    def fake_request(method, url, headers, params=None, json=None):
        if url == "https://graph/delta?token=1":
            return 200, {
                "value": [{"id": "new1"}, {"id": "gone", "@removed": {}}],
                "@odata.deltaLink": "https://graph/delta?token=2",
            }
        if url.endswith("/me/messages/new1"):
            return 200, {
                "id": "new1",
                "subject": "Quote request",
                "from": {
                    "emailAddress": {"name": "Bob", "address": "bob@customer.example"}
                },
                "toRecipients": [
                    {"emailAddress": {"address": "support@contoso.example"}}
                ],
                "internetMessageId": "<o1@outlook>",
                "conversationId": "conv-1",
                "body": {"contentType": "html", "content": "<p>How much for 10?</p>"},
                "hasAttachments": False,
                "internetMessageHeaders": [{"name": "In-Reply-To", "value": ""}],
            }
        raise AssertionError(f"unexpected request {url}")

    with token, patch(MAILBOX_REQUEST, side_effect=fake_request), patch(TASK) as delay:
        poll_mailbox_channels()
    channel.refresh_from_db()
    assert channel.config["cursor"] == "https://graph/delta?token=2"
    _, session_key, text, _, attachments, title = delay.call_args.args
    assert session_key == "conv-1"
    assert text.endswith("How much for 10?")
    assert attachments is None

    # Mail not addressed to the alias is left alone.
    def other_alias(method, url, headers, params=None, json=None):
        if url == "https://graph/delta?token=2":
            return 200, {
                "value": [{"id": "new2"}],
                "@odata.deltaLink": "https://graph/delta?token=3",
            }
        return 200, {
            "id": "new2",
            "subject": "Private",
            "from": {"emailAddress": {"address": "bob@customer.example"}},
            "toRecipients": [{"emailAddress": {"address": "help@contoso.example"}}],
            "internetMessageId": "<o2@outlook>",
            "conversationId": "conv-2",
            "body": {"contentType": "text", "content": "hi"},
        }

    with token, patch(MAILBOX_REQUEST, side_effect=other_alias), patch(TASK) as delay:
        poll_mailbox_channels()
    delay.assert_not_called()

    chat = AgentChat.objects.create(
        agent=agent,
        source=AgentChat.Source.CHANNEL,
        channel=channel,
        channel_session_key="conv-1",
    )
    with token, patch(MAILBOX_REQUEST, return_value=(202, None)) as request:
        sent = channel_type.reply(channel, chat, "About 100 euro.\nBest, Help")
    assert sent["to"] == "bob@customer.example"
    method, url = request.call_args.args[:2]
    assert (method, url) == (
        "POST",
        "https://graph.microsoft.com/v1.0/me/messages/new1/reply",
    )
    assert request.call_args.kwargs["json"] == {
        "comment": "About 100 euro.<br>Best, Help"
    }

    # The public config keeps the cursor to itself.
    public = channel_type.get_public_config(channel)
    assert "cursor" not in public and public["polling"] is True


def _b64(text):
    import base64

    return base64.urlsafe_b64encode(text.encode()).decode()


def _token_patch():
    return patch(
        "baserow_enterprise.agent_application.channels.mailbox"
        ".OAuth2IntegrationHandler.get_access_token",
        return_value="at",
    )


def _gmail_channel(application, data_fixture, **config):
    integration = data_fixture.create_google_integration(
        application=application, account_email="help@company.example"
    )
    prepared = GmailAgentChatChannelType().prepare_config(
        {"integration_id": integration.id, **config}
    )
    prepared["cursor"] = "100"
    return AgentChatChannel.objects.create(
        application=application, type="gmail", name="Gmail", config=prepared
    )


def _gmail_message(message_id, sender="ann@customer.example", **extra):
    return {
        "id": message_id,
        "threadId": f"thread-{message_id}",
        "payload": {
            "headers": [
                {"name": "From", "value": sender},
                {"name": "To", "value": "help@company.example"},
                {"name": "Subject", "value": f"Mail {message_id}"},
                {"name": "Message-ID", "value": f"<{message_id}@mail.gmail.com>"},
            ],
            "parts": [{"mimeType": "text/plain", "body": {"data": _b64("Hi")}}],
        },
        **extra,
    }


@pytest.mark.django_db
@override_settings(AGENT_APPLICATION_CHANNEL_RATE_LIMIT_PER_MINUTE=1000)
def test_gmail_poll_takes_a_backlog_over_several_polls(email_setup, data_fixture):
    user, application, agent = email_setup
    channel = _gmail_channel(application, data_fixture)
    # History records 101..130, one new message each, ten records a page.
    records = [
        {
            "id": str(100 + n),
            "messagesAdded": [{"message": {"id": f"m{n}", "labelIds": ["INBOX"]}}],
        }
        for n in range(1, 31)
    ]

    def fake_request(method, url, headers, params=None, json=None):
        if url.endswith("/history"):
            after = [r for r in records if int(r["id"]) > int(params["startHistoryId"])]
            offset = int(params.get("pageToken") or 0)
            body = {"historyId": "130", "history": after[offset : offset + 10]}
            if offset + 10 < len(after):
                body["nextPageToken"] = str(offset + 10)
            return 200, body
        return 200, _gmail_message(url.rsplit("/", 1)[1])

    delivered = []
    for _ in range(3):
        with (
            _token_patch(),
            patch(MAILBOX_REQUEST, side_effect=fake_request),
            patch(TASK) as delay,
        ):
            poll_mailbox_channels()
        delivered.append([call.args[1] for call in delay.call_args_list])
        channel.refresh_from_db()
        if len(delivered) == 1:
            # Resumes after the last history record that was taken.
            assert channel.config["cursor"] == "125"

    assert [len(batch) for batch in delivered] == [25, 5, 0]
    keys = [key for batch in delivered for key in batch]
    assert sorted(keys) == sorted(f"thread-m{n}" for n in range(1, 31))
    assert channel.config["cursor"] == "130"


@pytest.mark.django_db
def test_gmail_poll_skips_spam_and_trash(email_setup, data_fixture):
    user, application, agent = email_setup
    channel = _gmail_channel(application, data_fixture)
    history = [
        {
            "id": "101",
            "messagesAdded": [{"message": {"id": "spam", "labelIds": ["SPAM"]}}],
        },
        {
            "id": "102",
            "messagesAdded": [{"message": {"id": "bin", "labelIds": ["TRASH"]}}],
        },
        # Moved to the trash after the history record was written.
        {
            "id": "103",
            "messagesAdded": [{"message": {"id": "late", "labelIds": ["INBOX"]}}],
        },
        {
            "id": "104",
            "messagesAdded": [{"message": {"id": "ok", "labelIds": ["INBOX"]}}],
        },
    ]
    fetched = []

    def fake_request(method, url, headers, params=None, json=None):
        if url.endswith("/history"):
            return 200, {"historyId": "104", "history": history}
        message_id = url.rsplit("/", 1)[1]
        fetched.append(message_id)
        labels = ["TRASH"] if message_id == "late" else ["INBOX"]
        return 200, _gmail_message(message_id, labelIds=labels)

    with (
        _token_patch(),
        patch(MAILBOX_REQUEST, side_effect=fake_request),
        patch(TASK) as delay,
    ):
        poll_mailbox_channels()

    assert fetched == ["late", "ok"]
    delay.assert_called_once()
    assert delay.call_args.args[1] == "thread-ok"


@pytest.mark.django_db
def test_mail_from_a_disallowed_sender_stores_no_attachments(email_setup, data_fixture):
    from baserow.core.user_files.models import UserFile

    user, application, agent = email_setup
    channel = _gmail_channel(
        application, data_fixture, allowed_sender_domains=["customer.example"]
    )
    message = _gmail_message("evil", sender="eve@evil.example")
    message["payload"]["parts"].append(
        {
            "mimeType": "application/pdf",
            "filename": "big.pdf",
            "body": {"attachmentId": "att1"},
        }
    )
    requested = []

    def fake_request(method, url, headers, params=None, json=None):
        requested.append(url)
        if url.endswith("/history"):
            return 200, {
                "historyId": "101",
                "history": [
                    {
                        "id": "101",
                        "messagesAdded": [
                            {"message": {"id": "evil", "labelIds": ["INBOX"]}}
                        ],
                    }
                ],
            }
        if "/attachments/" in url:
            return 200, {"data": _b64("%PDF-1.4 fake")}
        return 200, message

    with (
        _token_patch(),
        patch(MAILBOX_REQUEST, side_effect=fake_request),
        patch(TASK) as delay,
    ):
        poll_mailbox_channels()

    delay.assert_not_called()
    assert not any("/attachments/" in url for url in requested)
    assert UserFile.objects.count() == 0

    # A duplicate never loads them either.
    channel_type = GmailAgentChatChannelType()
    with patch(TASK):
        assert channel_type.receive_email(
            channel,
            ReceivedEmail(
                from_address="ann@customer.example",
                message_id="<dup@x>",
                sender_verified=True,
            ),
        )
    loader = Mock(return_value=([], []))
    duplicate = ReceivedEmail(
        from_address="ann@customer.example",
        message_id="<dup@x>",
        sender_verified=True,
        load_attachments=loader,
    )
    assert channel_type.receive_email(channel, duplicate) is False
    loader.assert_not_called()


@pytest.mark.django_db
@override_settings(AGENT_APPLICATION_CHANNEL_RATE_LIMIT_PER_MINUTE=1000)
def test_outlook_poll_takes_a_backlog_and_bounds_the_first_walk(
    email_setup, data_fixture
):
    user, application, agent = email_setup
    integration = data_fixture.create_microsoft_integration(
        application=application, account_email="help@contoso.example"
    )
    channel_type = OutlookAgentChatChannelType()
    channel = AgentChatChannel.objects.create(
        application=application,
        type="outlook",
        name="Outlook",
        config=channel_type.prepare_config({"integration_id": integration.id}),
    )

    # The first round over a big folder is spread over several polls.
    def walk(method, url, headers, params=None, json=None):
        page = int(url.rsplit("page=", 1)[1]) if "page=" in url else 0
        if page == 14:
            return 200, {"value": [], "@odata.deltaLink": "https://graph/delta?t=1"}
        return 200, {
            "value": [{"id": f"old{page}"}],
            "@odata.nextLink": f"https://graph/walk?page={page + 1}",
        }

    with _token_patch(), patch(MAILBOX_REQUEST, side_effect=walk) as request:
        poll_mailbox_channels()
    assert request.call_count == 10
    channel.refresh_from_db()
    assert channel.config["sync_link"] == "https://graph/walk?page=10"
    assert not channel.config.get("cursor")
    assert "sync_link" not in channel_type.get_public_config(channel)

    with _token_patch(), patch(MAILBOX_REQUEST, side_effect=walk) as request:
        poll_mailbox_channels()
    assert request.call_args_list[0].args[1] == "https://graph/walk?page=10"
    channel.refresh_from_db()
    assert channel.config["cursor"] == "https://graph/delta?t=1"
    assert channel.config["sync_link"] == ""

    # Then 30 new messages, 25 a page.
    def delta(method, url, headers, params=None, json=None):
        if url == "https://graph/delta?t=1":
            return 200, {
                "value": [{"id": f"n{n}"} for n in range(1, 26)],
                "@odata.nextLink": "https://graph/delta?t=1&skip=25",
            }
        if url == "https://graph/delta?t=1&skip=25":
            return 200, {
                "value": [{"id": f"n{n}"} for n in range(26, 31)],
                "@odata.deltaLink": "https://graph/delta?t=2",
            }
        if url == "https://graph/delta?t=2":
            return 200, {"value": [], "@odata.deltaLink": "https://graph/delta?t=2"}
        message_id = url.rsplit("/", 1)[1]
        return 200, {
            "id": message_id,
            "subject": f"Mail {message_id}",
            "from": {"emailAddress": {"address": "bob@customer.example"}},
            "toRecipients": [{"emailAddress": {"address": "help@contoso.example"}}],
            "internetMessageId": f"<{message_id}@outlook>",
            "conversationId": f"conv-{message_id}",
            "body": {"contentType": "text", "content": "hi"},
        }

    delivered = []
    for expected_cursor in (
        "https://graph/delta?t=1&skip=25",
        "https://graph/delta?t=2",
        "https://graph/delta?t=2",
    ):
        with (
            _token_patch(),
            patch(MAILBOX_REQUEST, side_effect=delta),
            patch(TASK) as delay,
        ):
            poll_mailbox_channels()
        delivered.append([call.args[1] for call in delay.call_args_list])
        channel.refresh_from_db()
        assert channel.config["cursor"] == expected_cursor

    assert [len(batch) for batch in delivered] == [25, 5, 0]
    keys = [key for batch in delivered for key in batch]
    assert sorted(keys) == sorted(f"conv-n{n}" for n in range(1, 31))


@pytest.mark.django_db
def test_mailbox_poll_releases_only_its_own_lock(email_setup, data_fixture):
    from django.core.cache import cache

    user, application, agent = email_setup
    channel = _gmail_channel(application, data_fixture)
    lock_key = f"agent_application:mailbox:{channel.id}:poll"

    with patch.object(GmailAgentChatChannelType, "poll") as poll:
        poll_mailbox_channels()
    poll.assert_called_once()
    assert cache.get(lock_key) is None

    # The lock expired during a slow poll and another worker took it.
    def slow_poll(channel):
        cache.set(lock_key, "other-worker", timeout=60)

    with patch.object(GmailAgentChatChannelType, "poll", side_effect=slow_poll):
        poll_mailbox_channels()
    assert cache.get(lock_key) == "other-worker"
    cache.delete(lock_key)


def test_html_to_text_is_fast_on_hostile_markup():
    import time

    assert html_to_text("<STYLE>a</style>b<script>c") == "bc"
    assert html_to_text("<head><title>x</title></head><div>Hi</div>") == "Hi"
    for hostile in ("<style>" * 200_000, "<" * 1_000_000, "<p" * 500_000):
        started = time.monotonic()
        html_to_text(hostile[:500_000])
        ReceivedEmail(from_address="a@b.c", html=hostile).body
        assert time.monotonic() - started < 1


def test_authentication_results_must_vouch_for_the_from_domain():
    gmail = (
        "mx.google.com; dkim=pass header.i=@customer.example header.s=s1 "
        "header.b=abc; spf=pass (google.com: domain of ann@customer.example "
        "designates 203.0.113.5 as permitted sender) "
        "smtp.mailfrom=ann@customer.example; dmarc=pass (p=NONE sp=NONE "
        "dis=NONE) header.from=customer.example"
    )
    assert sender_authenticated(gmail, "ann@customer.example")
    assert sender_authenticated(gmail, "ann@mail.customer.example")
    assert not sender_authenticated(gmail, "ceo@company.example")

    outlook = (
        "spf=pass (sender IP is 203.0.113.5) smtp.mailfrom=customer.example; "
        "dkim=pass (signature was verified) header.d=customer.example;"
        "dmarc=pass action=none header.from=customer.example;compauth=pass "
        "reason=100"
    )
    assert sender_authenticated(outlook, "bob@customer.example")

    # Passing for the spoofer's own domain says nothing about the From.
    spoofed = (
        "mx.google.com; dkim=pass header.i=@evil.example; spf=pass "
        "smtp.mailfrom=eve@evil.example; dmarc=fail (p=NONE) "
        "header.from=customer.example"
    )
    assert not sender_authenticated(spoofed, "ann@customer.example")
    assert not sender_authenticated(
        "mx.google.com; dkim=fail header.d=customer.example; spf=softfail "
        "smtp.mailfrom=customer.example",
        "ann@customer.example",
    )
    assert not sender_authenticated("", "ann@customer.example")


@pytest.mark.django_db
@override_settings(**INBOUND)
def test_allowlisted_hosted_channel_only_takes_verified_senders(email_setup):
    user, application, agent = email_setup
    _hosted_channel(application, allowed_sender_domains=["customer.example"])
    handler = InboundEmailHandler()

    def deliver(message_id, **meta):
        payload = make_mox_payload(
            f"support@{DOMAIN}",
            MessageID=message_id,
            From=[{"Name": "Ann", "Address": "ann@customer.example"}],
        )
        payload["Meta"].update(meta)
        with patch(TASK) as delay:
            status = handler.handle_webhook_payload(payload)
        return status, delay

    status, delay = deliver(
        "<spoof@x>", MsgFromValidated=False, DKIMVerifiedDomains=["evil.example"]
    )
    assert status == "discarded"
    delay.assert_not_called()

    status, delay = deliver(
        "<dkim@x>", MsgFromValidated=False, DKIMVerifiedDomains=["customer.example"]
    )
    assert status == "accepted"
    assert "Sender verified: yes" in delay.call_args.args[2]

    status, delay = deliver("<valid@x>", MsgFromValidated=True)
    assert status == "accepted"


@pytest.mark.django_db
def test_mailbox_sender_verification_comes_from_the_providers_header(
    email_setup, data_fixture
):
    user, application, agent = email_setup
    channel = _gmail_channel(application, data_fixture)
    channel_type = GmailAgentChatChannelType()
    passing = "mx.google.com; dmarc=pass (p=REJECT) header.from=customer.example"

    def gmail(*auth_results):
        message = _gmail_message("m1")
        message["payload"]["headers"] = [
            {"name": "Authentication-Results", "value": value} for value in auth_results
        ] + message["payload"]["headers"]
        with patch(MAILBOX_REQUEST, return_value=(200, message)):
            return channel_type._fetch_message(channel, {}, "m1")

    assert gmail(passing).sender_verified is True
    assert gmail().sender_verified is False
    # A forged header further down doesn't count.
    assert (
        gmail(
            "mx.google.com; dmarc=fail header.from=customer.example", passing
        ).sender_verified
        is False
    )

    outlook_channel = AgentChatChannel.objects.create(
        application=application,
        type="outlook",
        name="Outlook",
        config=OutlookAgentChatChannelType().prepare_config(
            {
                "integration_id": data_fixture.create_microsoft_integration(
                    application=application
                ).id
            }
        ),
    )
    outlook_message = {
        "id": "o1",
        "from": {"emailAddress": {"address": "bob@customer.example"}},
        "toRecipients": [],
        "body": {"contentType": "text", "content": "hi"},
        "internetMessageHeaders": [
            {
                "name": "Authentication-Results",
                "value": "spf=pass (sender IP is 203.0.113.5) "
                "smtp.mailfrom=customer.example; dkim=none; dmarc=none",
            }
        ],
    }
    with patch(MAILBOX_REQUEST, return_value=(200, outlook_message)) as request:
        received = OutlookAgentChatChannelType()._fetch_message(
            outlook_channel, {}, "o1"
        )
    assert received.sender_verified is True
    assert "internetMessageHeaders" in request.call_args.kwargs["params"]["$select"]


@pytest.mark.django_db
def test_allowlisted_mailbox_channel_ignores_unverified_mail(email_setup, data_fixture):
    user, application, agent = email_setup
    channel = _gmail_channel(
        application, data_fixture, allowed_sender_domains=["customer.example"]
    )
    channel_type = GmailAgentChatChannelType()
    loader = Mock(return_value=([], []))
    with patch(TASK) as delay:
        assert (
            channel_type.receive_email(
                channel,
                ReceivedEmail(
                    from_address="ann@customer.example",
                    message_id="<spoof@x>",
                    load_attachments=loader,
                ),
            )
            is False
        )
        assert channel_type.receive_email(
            channel,
            ReceivedEmail(
                from_address="ann@customer.example",
                message_id="<real@x>",
                sender_verified=True,
            ),
        )
    loader.assert_not_called()
    delay.assert_called_once()

    # Without an allowlist unverified mail is taken, and says so.
    channel.config["allowed_sender_domains"] = []
    with patch(TASK) as delay:
        assert channel_type.receive_email(
            channel,
            ReceivedEmail(from_address="x@other.example", message_id="<other@x>"),
        )
    assert "Sender verified: no" in delay.call_args.args[2]


def _busy_email_chat(application, agent, status):
    channel = _hosted_channel(application)
    chat = AgentChat.objects.create(
        agent=agent,
        source=AgentChat.Source.CHANNEL,
        channel=channel,
        channel_session_key="thread",
        status=status,
    )
    return channel, chat


RUN_TASK = "baserow_enterprise.agent_application.tasks.run_agent_chat.delay"


@pytest.mark.django_db
@override_settings(**INBOUND)
@pytest.mark.parametrize(
    "busy_status", [AgentChat.Status.IN_PROGRESS, AgentChat.Status.AWAITING_APPROVAL]
)
def test_mail_for_a_busy_conversation_is_answered_afterwards(
    email_setup, busy_status, django_capture_on_commit_callbacks
):
    from baserow_enterprise.agent_application.tasks import _notify_chat_channel

    user, application, agent = email_setup
    channel, chat = _busy_email_chat(application, agent, busy_status)

    # Neither refused nor retried: both mails wait in the conversation.
    with patch(RUN_TASK) as run:
        assert start_channel_chat(channel, "thread", "From: ann\n\nOne") is None
        assert start_channel_chat(channel, "thread", "From: ann\n\nTwo") is None
    run.assert_not_called()
    first, second = chat.messages.filter(role=AgentChatMessage.Role.HUMAN)
    assert first.artifacts == {"queued_email": True}

    # The run (or the run resumed after the approval) ends: the first mail
    # gets its turn.
    chat.status = AgentChat.Status.IDLE
    chat.save(update_fields=["status"])
    with (
        patch(RUN_TASK) as run,
        django_capture_on_commit_callbacks(execute=True),
    ):
        _notify_chat_channel(chat)
    run.assert_called_once_with(chat.id, first.id)
    chat.refresh_from_db()
    first.refresh_from_db()
    assert chat.status == AgentChat.Status.IN_PROGRESS
    assert first.artifacts == {}

    # Its turn ends: the second one follows.
    chat.status = AgentChat.Status.IDLE
    chat.save(update_fields=["status"])
    with (
        patch(RUN_TASK) as run,
        django_capture_on_commit_callbacks(execute=True),
    ):
        _notify_chat_channel(chat)
    run.assert_called_once_with(chat.id, second.id)

    # Nothing left: the next end starts nothing.
    chat.status = AgentChat.Status.IDLE
    chat.save(update_fields=["status"])
    with patch(RUN_TASK) as run, django_capture_on_commit_callbacks(execute=True):
        _notify_chat_channel(chat)
    run.assert_not_called()


@pytest.mark.django_db
def test_retry_skips_mail_that_still_waits_for_its_turn(data_fixture):
    from baserow_enterprise.agent_application.channels.email import (
        QUEUED_MAIL_ARTIFACT,
    )
    from baserow_enterprise.agent_application.handler import AgentChatHandler
    from baserow_enterprise.agent_application.models import (
        AgentChat,
        AgentChatMessage,
    )

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    application = (
        CoreHandler()
        .create_application(user, workspace, "agent", init_with_data=True, name="A")
        .specific
    )
    agent = AgentApplicationHandler().get_main_agent(application)
    chat = AgentChat.objects.create(agent=agent, status=AgentChat.Status.ERROR)
    failed = AgentChatMessage.objects.create(chat=chat, role="human", content="1")
    AgentChatMessage.objects.create(
        chat=chat,
        role="human",
        content="2",
        artifacts={QUEUED_MAIL_ARTIFACT: True},
    )

    with patch(
        "baserow_enterprise.agent_application.realtime.broadcast_to_channel_group"
    ):
        retried = AgentChatHandler().retry_chat_run(chat)

    assert retried.id == failed.id
