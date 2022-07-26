from typing import Any, Dict

from django.contrib.auth.models import AbstractUser
from rest_framework import serializers

from baserow.api.applications.serializers import ApplicationSerializer
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP, ERROR_GROUP_DOES_NOT_EXIST
from baserow.core.action.registries import action_type_registry
from baserow.core.actions import DuplicateApplicationActionType
from baserow.core.exceptions import UserNotInGroup, GroupDoesNotExist
from baserow.core.handler import CoreHandler
from baserow.core.jobs.registries import JobType
from baserow.core.jobs.types import AnyJob
from baserow.core.models import Application, DuplicateApplicationJob
from baserow.core.registries import application_type_registry
from baserow.core.utils import Progress


class DuplicateApplicationJobType(JobType):
    type = "duplicate_application"
    model_class = DuplicateApplicationJob
    max_count = 1

    api_exceptions_map = {
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
    }

    request_serializer_field_names = ["application_id"]

    request_serializer_field_overrides = {
        "application_id": serializers.IntegerField(
            help_text="The application ID to duplicate.",
        ),
    }

    serializer_field_names = ["original_application", "duplicated_application"]
    serializer_field_overrides = {
        "original_application": ApplicationSerializer(read_only=True),
        "duplicated_application": ApplicationSerializer(read_only=True),
    }

    def transaction_atomic_context(self, job: "DuplicateApplicationJob"):
        application = CoreHandler().get_user_application(
            job.user, job.original_application_id
        )
        application_type = application_type_registry.get_by_model(
            application.specific_class
        )
        return application_type.export_safe_transaction_context(application)

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:

        application = CoreHandler().get_user_application(user, values["application_id"])

        return {
            "original_application": application,
        }

    def run(self, job: AnyJob, progress: Progress) -> Application:

        new_application_clone = action_type_registry.get_by_type(
            DuplicateApplicationActionType
        ).do(
            job.user,
            job.original_application,
            progress.create_child_builder(represents_progress=progress.total),
        )

        # update the job with the new duplicated application
        job.duplicated_application = new_application_clone
        job.save(update_fields=("duplicated_application",))

        return new_application_clone
