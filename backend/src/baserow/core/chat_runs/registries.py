from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import AbstractUser

from baserow.core.registry import Instance, Registry

from .models import ChatRun
from .types import ChatRunOutcome

if TYPE_CHECKING:
    from .journal import ChatRunJournal


class ChatRunType(Instance):
    """Product side of a chat run: permissions, execution and saving the answer.

    Only ``execute`` runs on the worker's event loop. Every other hook is
    synchronous and may run in an HTTP request, the worker or a maintenance task.
    """

    def can_read(self, user: AbstractUser, run: ChatRun) -> bool:
        """Check whether the user may read the run and follow its output.

        :param user: The user requesting the run.
        :param run: The run to read.
        :return: Whether the user may read it. When False, the API responds as if
            the run does not exist.
        """

        raise NotImplementedError

    def can_cancel(self, user: AbstractUser, run: ChatRun) -> bool:
        """Check whether the user may stop the run.

        :param user: The user requesting the stop.
        :param run: The run to stop.
        :return: Whether the user may stop it. When False, the API responds as if
            the run does not exist.
        """

        raise NotImplementedError

    def can_follow_chat(self, user: AbstractUser, chat_id: int) -> bool:
        """Check whether the user may receive realtime updates of a chat's runs.

        :param user: The user subscribing.
        :param chat_id: The id of the chat, as identified by this run type.
        :return: Whether the user may follow the chat.
        """

        raise NotImplementedError

    async def execute(self, run: ChatRun, journal: "ChatRunJournal") -> ChatRunOutcome:
        """Produce the answer once, emitting output through the journal.

        When the journal requests a stop, let running tools finish, then return.

        :param run: The claimed run.
        :param journal: Receives the output and signals when to stop.
        :return: How the run ended, passed to ``persist_outcome``.
        :raises Exception: Any error fails the run with the ``failed`` error code.
        """

        raise NotImplementedError

    def persist_outcome(self, run: ChatRun, outcome: ChatRunOutcome) -> dict | None:
        """Save the answer in the product, in the transaction that ends the run.

        The writes roll back if the run already ended elsewhere, so avoid side
        effects outside the database.

        :param run: The run, locked for this transaction.
        :param outcome: What ``execute`` returned.
        :return: The JSON-serializable message stored as the run's outcome.
        :raises Exception: Any error rolls back the writes and fails the run with
            the ``persist_failed`` error code.
        """

        return None

    def serialize_outcome(self, run: ChatRun) -> dict | None:
        """Serialize the saved answer for clients.

        :param run: The run to serialize.
        :return: The message sent to clients, built from saved state only, never
            from the temporary output buffer.
        """

        return run.outcome

    def on_run_lost(
        self, run: ChatRun, events: list[dict[str, Any]] | None = None
    ) -> dict | None:
        """Save what is left of a run whose worker stopped renewing its lease.

        ``run.status`` and ``run.error_code`` already hold the final values.

        :param run: The run, locked for the transaction that ends it.
        :param events: The run's complete buffered output, or None when the buffer
            is missing or incomplete.
        :return: The JSON-serializable message stored as the run's outcome.
        :raises Exception: Any error rolls back the writes; the run still ends,
            without a message.
        """

        return None

    def on_run_not_started(self, run: ChatRun) -> dict | None:
        """Save the outcome of a queued run that never started.

        It was cancelled, could not be enqueued or waited too long. ``run.status``
        and ``run.error_code`` already hold the final values.

        :param run: The run, locked for the transaction that ends it.
        :return: The JSON-serializable message stored as the run's outcome.
        :raises Exception: Any error rolls back the writes; the run still ends,
            without a message.
        """

        return None

    def ensure_interruption_warning(self, run: ChatRun) -> bool:
        """Make sure the product shows that a started run did not complete.

        The run is pruned only after this returns True, so its history can still
        be rebuilt from it until then.

        :param run: The started run that did not complete.
        :return: Whether the product durably holds the warning.
        :raises Exception: Any error is logged and the run is kept.
        """

        return False


class ChatRunTypeRegistry(Registry[ChatRunType]):
    name = "chat_run_type"


chat_run_type_registry = ChatRunTypeRegistry()
