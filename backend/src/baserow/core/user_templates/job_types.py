from contextlib import nullcontext
from functools import partial
from typing import Any, Dict

from django.contrib.auth.models import AbstractUser

from loguru import logger
from rest_framework import serializers

from baserow.api.errors import (
    ERROR_FEATURE_DISABLED,
    ERROR_GROUP_DOES_NOT_EXIST,
    ERROR_PERMISSION_DENIED,
    ERROR_USER_NOT_IN_GROUP,
)
from baserow.api.templates.errors import (
    ERROR_INVALID_TEMPLATE_CATEGORY,
    ERROR_INVALID_TEMPLATE_ICON,
    ERROR_NO_APPLICATIONS_SELECTED,
)
from baserow.core.action.registries import action_type_registry
from baserow.core.exceptions import (
    FeatureDisabledException,
    PermissionException,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
)
from baserow.core.handler import CoreHandler
from baserow.core.jobs.constants import JOB_CANCELLED
from baserow.core.jobs.exceptions import JobCancelled
from baserow.core.jobs.handler import JobHandler
from baserow.core.jobs.registries import JobType
from baserow.core.user_templates.actions import CreateUserTemplateActionType
from baserow.core.user_templates.constants import (
    USER_TEMPLATE_DESCRIPTION_MAX_LENGTH,
    USER_TEMPLATE_ICON_MAX_LENGTH,
)
from baserow.core.user_templates.exceptions import (
    InvalidTemplateCategory,
    InvalidTemplateIcon,
    NoApplicationsSelected,
)
from baserow.core.user_templates.handler import UserTemplateHandler
from baserow.core.user_templates.models import CreateUserTemplateJob
from baserow.core.user_templates.service import UserTemplateService
from baserow.core.utils import Progress


def _get_id_field_overrides(response: bool) -> Dict[str, serializers.Field]:
    """
    The id fields of the request, which are sent back read-only in the response.
    The other fields of the request are serialized from the model.
    """

    read_only = {"read_only": True} if response else {}
    return {
        "workspace_id": serializers.IntegerField(
            **({"source": "source_workspace_id"} if response else {}),
            **read_only,
            help_text="The ID of the workspace the applications are copied from.",
        ),
        "application_ids": serializers.ListField(
            child=serializers.IntegerField(),
            **(read_only or {"min_length": 1}),
            help_text="The IDs of the applications copied into the template.",
        ),
        "category_ids": serializers.ListField(
            child=serializers.IntegerField(),
            **read_only,
            help_text=(
                "The IDs of the existing categories of the template, at least one "
                "unless there are none."
            ),
        ),
    }


class CreateUserTemplateJobType(JobType):
    type = "create_user_template"
    model_class = CreateUserTemplateJob
    max_count = 1
    # Committing the template is the point of no return: a cancellation is
    # noticed before it, which rolls the template and its action back, or refused
    # after it, so that the audit log always matches what's kept.
    lock_on_cancel = True

    api_exceptions_map = {
        UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
        InvalidTemplateIcon: ERROR_INVALID_TEMPLATE_ICON,
        InvalidTemplateCategory: ERROR_INVALID_TEMPLATE_CATEGORY,
        NoApplicationsSelected: ERROR_NO_APPLICATIONS_SELECTED,
    }

    job_exceptions_map = {
        # Covers losing access to the workspace after the job was created too.
        PermissionException: ERROR_PERMISSION_DENIED[2],
        FeatureDisabledException: ERROR_FEATURE_DISABLED[2],
        WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST[2],
        InvalidTemplateIcon: ERROR_INVALID_TEMPLATE_ICON[2],
        InvalidTemplateCategory: ERROR_INVALID_TEMPLATE_CATEGORY[2],
        NoApplicationsSelected: ERROR_NO_APPLICATIONS_SELECTED[2],
    }

    request_serializer_field_names = [
        "workspace_id",
        "application_ids",
        "name",
        "description",
        "icon",
        "category_ids",
    ]
    request_serializer_field_overrides = {
        **_get_id_field_overrides(response=False),
        "name": serializers.CharField(
            max_length=64, help_text="The name of the template."
        ),
        "description": serializers.CharField(
            max_length=USER_TEMPLATE_DESCRIPTION_MAX_LENGTH,
            allow_blank=True,
            default="",
            help_text="The description of the template.",
        ),
        "icon": serializers.CharField(
            max_length=USER_TEMPLATE_ICON_MAX_LENGTH,
            help_text="The iconoir class name of the icon of the template.",
        ),
    }

    # The request is sent back, so that the wizard can show a running job again.
    serializer_field_names = [*request_serializer_field_names, "template"]
    serializer_field_overrides = {
        **_get_id_field_overrides(response=True),
        "template": serializers.PrimaryKeyRelatedField(
            read_only=True, help_text="The ID of the created template."
        ),
    }

    def transaction_atomic_context(self, job: CreateUserTemplateJob):
        """
        The export needs its own `repeatable_read` transaction per application and
        the import creates one per application, so the job runs without an outer
        transaction. Whatever was created is removed by `on_error` and
        `on_cancelled` instead of a rollback.
        """

        return nullcontext()

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:
        workspace = CoreHandler().get_workspace(values["workspace_id"])
        application_ids = values.get("application_ids") or []
        applications = UserTemplateService().get_exportable_applications(
            user, workspace, application_ids
        )
        category_ids = values.get("category_ids") or []
        categories = UserTemplateHandler().validate_icon_and_categories(
            values.get("icon"), category_ids
        )

        return {
            "source_workspace": workspace,
            "application_ids": [application.id for application in applications],
            "name": values["name"],
            "description": values.get("description", ""),
            "icon": values["icon"],
            "category_ids": [category.id for category in categories],
        }

    def run(self, job: CreateUserTemplateJob, progress: Progress):
        if job.source_workspace is None:
            raise WorkspaceDoesNotExist("The source workspace does not exist.")

        try:
            return action_type_registry.get_by_type(CreateUserTemplateActionType).do(
                job.user,
                job.source_workspace,
                job.application_ids,
                name=job.name,
                description=job.description,
                icon=job.icon,
                category_ids=job.category_ids,
                progress_builder=progress.create_child_builder(
                    represents_progress=progress.total
                ),
                track_content=partial(self._track_content, job),
                before_commit=partial(self._save_template, job),
            )
        except BaseException:
            try:
                # The template is only set when its transaction committed.
                job.refresh_from_db(fields=["template"])
            except CreateUserTemplateJob.DoesNotExist:
                self._delete_content_of_deleted_job(job)
            raise

    def _delete_content_of_deleted_job(self, job: CreateUserTemplateJob) -> None:
        """
        A job deleted while it runs, with its user, can't be saved as failed, so
        `on_error` doesn't run, and its deletion only saw what it tracked by then.
        What it tracked since is still on the instance.
        """

        try:
            UserTemplateHandler().delete_content_of_deleted_job(
                job.template_workspace_id, job.archive_name
            )
        except Exception:
            logger.exception(
                f"Deleting the content of deleted create user template job {job.id} "
                "failed."
            )

    def _save_template(self, job: CreateUserTemplateJob, template) -> None:
        """
        Sets the template on the job in the transaction that creates it. The job
        is locked first, so that a cancellation either lands before, and is noticed
        here, or waits for the commit and is refused by `is_cancellable`. The state
        is read from the locked row, because a progress update of this job can
        overwrite the cancelled state in the cache.
        """

        if JobHandler.lock_job(job).state == JOB_CANCELLED:
            raise JobCancelled()
        job.template = template
        job.save(update_fields=["template"])

    def is_cancellable(self, job: CreateUserTemplateJob) -> bool:
        return job.template_id is None

    def _track_content(self, job: CreateUserTemplateJob, **content) -> None:
        """
        Stores the workspace and the archive on the job as soon as they exist, so
        that the cleanup finds them whatever happens next.
        """

        for field_name, value in content.items():
            setattr(job, field_name, value)
        job.save(update_fields=list(content))

    def on_error(self, job: CreateUserTemplateJob, error: Exception):
        # A template that was committed is kept with its action, like a
        # cancellation is refused after the commit.
        UserTemplateHandler().delete_content_without_template(
            job.template_workspace_id, job.archive_name
        )

    def on_cancelled(self, job: CreateUserTemplateJob):
        # The template was rolled back, see `lock_on_cancel`. Whatever can't be
        # deleted here is left to the sweep of unfinished jobs.
        try:
            UserTemplateHandler().delete_content_without_template(
                job.template_workspace_id, job.archive_name
            )
        except Exception:
            logger.exception(
                f"Deleting the content of create user template job {job.id} failed."
            )
