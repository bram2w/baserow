from typing import Any
from django.contrib.auth.models import AbstractUser
from django.db import models
from baserow.api.sessions import (
    get_untrusted_client_session_id,
    set_untrusted_client_session_id,
)


class JobWithUserDataMixin(models.Model):
    """
    This mixin permits to add information about the user session to the job
    in order to handle correctly the undo/redo functionality and the signals updates.
    NOTE: it only works used in subclasses of Job.
    """

    user_data_to_save = ["user_session_id", "user_websocket_id"]

    user_session_id = models.CharField(
        max_length=36,
        null=True,
        help_text="The user session uuid needed for undo/redo functionality.",
    )

    user_websocket_id = models.CharField(
        max_length=36,
        null=True,
        help_text="The user websocket uuid needed to manage signals sent correctly.",
    )

    def _save_user_data_if_not_present(self, user: AbstractUser) -> None:
        """
        Save the user session in the job so to be able to restore.
        Call this in a request context and not from a celery job or other contexts.
        """

        if self.user_session_id is None and "user_session_id" in self.user_data_to_save:
            self.user_session_id = get_untrusted_client_session_id(user)

        if (
            self.user_websocket_id is None
            and "user_websocket_id" in self.user_data_to_save
        ):
            self.user_websocket_id = getattr(user, "web_socket_id", None)

    def _restore_user_data_if_present(self, user: AbstractUser) -> None:
        if self.user_session_id and "user_session_id" in self.user_data_to_save:
            set_untrusted_client_session_id(user, self.user_session_id)

        if self.user_websocket_id and "user_websocket_id" in self.user_data_to_save:
            user.web_socket_id = self.user_websocket_id

    def save(self, *args, **kwargs):
        self._save_user_data_if_not_present(self.user)
        return super().save(*args, **kwargs)

    def __getattribute__(self, name: str) -> Any:
        value = super().__getattribute__(name)

        if name == "user":
            self._restore_user_data_if_present(value)

        return value

    class Meta:
        abstract = True
