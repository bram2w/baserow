from typing import Any, Dict, List

from django.contrib.auth.models import AbstractUser

from rest_framework import serializers

from baserow.api.applications.serializers import (
    InstallTemplateJobApplicationsSerializer,
    SpecificApplicationSerializer,
)
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.api.groups.serializers import GroupSerializer
from baserow.api.templates.errors import (
    ERROR_TEMPLATE_DOES_NOT_EXIST,
    ERROR_TEMPLATE_FILE_DOES_NOT_EXIST,
)
from baserow.api.templates.serializers import TemplateSerializer
from baserow.core.action.registries import action_type_registry
from baserow.core.actions import (
    DuplicateApplicationActionType,
    InstallTemplateActionType,
)
from baserow.core.exceptions import (
    GroupDoesNotExist,
    TemplateDoesNotExist,
    TemplateFileDoesNotExist,
    UserNotInGroup,
)
from baserow.core.handler import CoreHandler
from baserow.core.jobs.registries import JobType
from baserow.core.models import Application, DuplicateApplicationJob, InstallTemplateJob
from baserow.core.operations import CreateApplicationsGroupOperationType
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
        "original_application": SpecificApplicationSerializer(read_only=True),
        "duplicated_application": SpecificApplicationSerializer(read_only=True),
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

    def run(self, job: DuplicateApplicationJob, progress: Progress) -> Application:

        new_application_clone = action_type_registry.get_by_type(
            DuplicateApplicationActionType
        ).do(
            job.user,
            job.original_application,
            progress_builder=progress.create_child_builder(
                represents_progress=progress.total
            ),
        )

        # update the job with the new duplicated application
        job.duplicated_application = new_application_clone
        job.save(update_fields=("duplicated_application",))

        return new_application_clone


class InstallTemplateJobType(JobType):
    type = "install_template"
    model_class = InstallTemplateJob
    max_count = 1

    api_exceptions_map = {
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
        TemplateDoesNotExist: ERROR_TEMPLATE_DOES_NOT_EXIST,
        TemplateFileDoesNotExist: ERROR_TEMPLATE_FILE_DOES_NOT_EXIST,
    }

    request_serializer_field_names = ["group_id", "template_id"]

    request_serializer_field_overrides = {
        "group_id": serializers.IntegerField(
            help_text="The ID of the group where the template will be installed.",
        ),
        "template_id": serializers.IntegerField(
            help_text="The template ID that will be installed.",
        ),
    }

    serializer_field_names = ["group", "template", "installed_applications"]
    serializer_field_overrides = {
        "group": GroupSerializer(read_only=True),
        "template": TemplateSerializer(read_only=True),
        "installed_applications": InstallTemplateJobApplicationsSerializer(
            read_only=True
        ),
    }

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:

        handler = CoreHandler()
        group = handler.get_group(values["group_id"])
        CoreHandler().check_permissions(
            user, CreateApplicationsGroupOperationType.type, group=group, context=group
        )

        # ensure everything is ok for the installation, otherwise
        # raise an exception immediately without submitting the job
        template = handler.get_template(values["template_id"])
        handler.get_valid_template_path_or_raise(template)

        return {
            "group": group,
            "template": template,
        }

    def run(self, job: InstallTemplateJob, progress: Progress) -> List[Application]:
        progress_builder = progress.create_child_builder(
            represents_progress=progress.total
        )

        installed_applications = action_type_registry.get_by_type(
            InstallTemplateActionType
        ).do(job.user, job.group, job.template, progress_builder=progress_builder)

        job.installed_applications = [app.id for app in installed_applications]
        job.save(update_fields=("installed_applications",))

        return installed_applications
