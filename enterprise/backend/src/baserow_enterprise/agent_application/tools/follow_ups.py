"""
The follow-up tools. In a conversation with a Baserow user the agent can
propose a follow-up, which always needs that user's approval, and cancel one
of theirs. A check of a follow-up gets the tools to notify the user, remember
what it found and complete the follow-up.
"""

from typing import Annotated, Literal, Optional

from asgiref.sync import sync_to_async
from pydantic import Field
from pydantic_ai import RunContext
from pydantic_ai.exceptions import ApprovalRequired
from pydantic_ai.toolsets import FunctionToolset

from ..deps import AgentRunDeps

PROPOSE_FOLLOW_UP_TOOL_NAME = "propose_follow_up"

_THOUGHT = Annotated[str, Field(description="Brief reasoning for calling this tool.")]


async def propose_follow_up(
    ctx: RunContext[AgentRunDeps],
    title: Annotated[
        str,
        Field(
            description=(
                "Short name shown to the user, e.g. 'Status of GitHub issue #123'."
            )
        ),
    ],
    goal: Annotated[
        str, Field(description="Why the user wants this, in their own terms.")
    ],
    check_instructions: Annotated[
        str,
        Field(
            description=(
                "Exactly what a check does with your tools, with the identifiers "
                "it needs (URLs, ids, table and row ids). A later check only "
                "has these instructions, not this conversation."
            )
        ),
    ],
    done_when: Annotated[
        str,
        Field(description="When the follow-up is complete and checks can stop."),
    ],
    watch: Annotated[
        Literal["schedule", "rows_created", "rows_updated", "rows_deleted"],
        Field(
            description=(
                "What starts a check. Use the row events for Baserow rows you can "
                "reach (`rows_updated`/`rows_deleted` with the `row_ids`, "
                "`rows_created` for new rows matching something), otherwise "
                "`schedule` to check periodically."
            )
        ),
    ],
    state: Annotated[
        str,
        Field(
            description=(
                "The current situation the first check compares against, e.g. "
                "'status is open, last comment from Ann on 3 May'. Look it up "
                "before proposing."
            )
        ),
    ],
    thought: _THOUGHT,
    every: Annotated[
        Optional[Literal["15_minutes", "30_minutes", "hour", "day", "week"]],
        Field(
            description=(
                "How often a `schedule` checks. Every check costs tokens: pick "
                "the slowest that still makes sense."
            )
        ),
    ] = None,
    table_id: Annotated[
        Optional[int], Field(description="The table of a row event.")
    ] = None,
    row_ids: Annotated[
        Optional[list[int]],
        Field(description="The rows to watch for `rows_updated`/`rows_deleted`."),
    ] = None,
    expires_in_days: Annotated[
        Optional[int],
        Field(
            description=(
                "Stop checking after this many days (1-365). Only use null, "
                "for no end date, when the user wants it to keep checking until "
                "it's done or they stop it."
            )
        ),
    ] = 30,
) -> dict:
    """
    Proposes a follow-up: you keep an eye on something for the user and notify
    them in Baserow when it changes or happens, like "tell me when the status
    of this issue changes" or "let me know when an order from ACME comes in".
    The user sees the details and must approve it before it exists. Only
    propose one when the user asks to be kept informed.
    """

    from ..exceptions import AgentFollowUpInvalid
    from ..follow_ups import AgentFollowUpHandler

    values = {
        "title": title,
        "goal": goal,
        "check_instructions": check_instructions,
        "done_when": done_when,
        "watch": watch,
        "every": every,
        "table_id": table_id,
        "row_ids": row_ids,
        "state": state,
        "expires_in_days": expires_in_days,
    }
    user = ctx.deps.initiating_user
    chat = ctx.deps.chat
    handler = AgentFollowUpHandler()

    if not ctx.tool_call_approved:
        try:
            await sync_to_async(handler.prepare_proposal)(user, chat, values)
        except AgentFollowUpInvalid as exc:
            return {"error": str(exc)}
        # The user decides with the details in front of them.
        raise ApprovalRequired

    try:
        follow_up = await sync_to_async(handler.create_follow_up)(user, chat, values)
    except AgentFollowUpInvalid as exc:
        return {"error": str(exc)}
    return {
        "follow_up_id": follow_up.id,
        "created": True,
        "note": "Tell the user it's set up; they can see it under Follow-ups.",
    }


async def cancel_follow_up(
    ctx: RunContext[AgentRunDeps],
    follow_up_id: Annotated[int, Field(description="The id of the follow-up.")],
    thought: _THOUGHT,
) -> dict:
    """
    Cancels one of the user's active follow-ups when they no longer want it.
    """

    from ..models import AgentFollowUp

    def cancel():
        from ..follow_ups import AgentFollowUpHandler

        follow_up = AgentFollowUp.objects.filter(
            id=follow_up_id,
            application_id=ctx.deps.agent.application_id,
            created_by=ctx.deps.initiating_user,
            status=AgentFollowUp.Status.ACTIVE,
        ).first()
        if follow_up is None:
            return {"error": "The user has no active follow-up with that id."}
        AgentFollowUpHandler().cancel_follow_up(ctx.deps.initiating_user, follow_up)
        return {"cancelled": True}

    return await sync_to_async(cancel)()


def _check_follow_up(ctx: RunContext[AgentRunDeps]):
    from ..models import AgentFollowUp

    return AgentFollowUp.objects.select_related(
        "application__workspace", "created_by"
    ).get(id=ctx.deps.chat.follow_up_id)


async def notify_user(
    ctx: RunContext[AgentRunDeps],
    message: Annotated[
        str,
        Field(
            description=(
                "What the user needs to know, short and self-contained: what "
                "changed, from what to what."
            )
        ),
    ],
    thought: _THOUGHT,
) -> dict:
    """
    Sends the user who asked for this follow-up a Baserow notification. Only
    use it when there is something they asked to hear about.
    """

    from ..follow_ups import AgentFollowUpHandler

    def notify():
        follow_up = _check_follow_up(ctx)
        AgentFollowUpHandler().notify_user(follow_up, ctx.deps.chat, message)

    await sync_to_async(notify)()
    ctx.deps.follow_up_events.add("notified")
    return {"notified": True}


async def remember_follow_up_state(
    ctx: RunContext[AgentRunDeps],
    state: Annotated[
        str,
        Field(
            description=(
                "Replaces what you remember for the next check, e.g. the "
                "current status, so it can tell what changed."
            )
        ),
    ],
    thought: _THOUGHT,
) -> dict:
    """
    Updates what the next check of this follow-up compares against.
    """

    from ..follow_ups import AgentFollowUpHandler

    def remember():
        AgentFollowUpHandler().remember_state(_check_follow_up(ctx), state)

    await sync_to_async(remember)()
    return {"remembered": True}


async def complete_follow_up(
    ctx: RunContext[AgentRunDeps],
    outcome: Annotated[
        str, Field(description="How it ended, shown in the list of follow-ups.")
    ],
    thought: _THOUGHT,
) -> dict:
    """
    Completes this follow-up so no more checks run. Notify the user first.
    """

    from ..follow_ups import AgentFollowUpHandler
    from ..models import AgentFollowUp

    def complete():
        AgentFollowUpHandler().end_follow_up(
            _check_follow_up(ctx), AgentFollowUp.Status.COMPLETED, outcome
        )

    await sync_to_async(complete)()
    ctx.deps.follow_up_events.add("ended")
    return {"completed": True}


def build_follow_up_proposal_toolset() -> FunctionToolset:
    return FunctionToolset([propose_follow_up, cancel_follow_up], max_retries=2)


def build_follow_up_check_toolset() -> FunctionToolset:
    return FunctionToolset(
        [notify_user, remember_follow_up_state, complete_follow_up], max_retries=2
    )
