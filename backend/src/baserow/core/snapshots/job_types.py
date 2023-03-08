from baserow.api.errors import (
    ERROR_MAX_LOCKS_PER_TRANSACTION_EXCEEDED,
    ERROR_USER_NOT_IN_GROUP,
)
from baserow.api.snapshots.errors import ERROR_SNAPSHOT_DOES_NOT_EXIST
from baserow.contrib.database.exceptions import (
    DatabaseSnapshotMaxLocksExceededException,
)
from baserow.core.action.registries import action_type_registry
from baserow.core.exceptions import UserNotInGroup
from baserow.core.handler import CoreHandler
from baserow.core.jobs.registries import JobType
from baserow.core.registries import application_type_registry
from baserow.core.snapshots.exceptions import SnapshotDoesNotExist

from .models import CreateSnapshotJob, RestoreSnapshotJob


class CreateSnapshotJobType(JobType):
    type = "create_snapshot"
    model_class = CreateSnapshotJob
    max_count = 1

    api_exceptions_map = {
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        SnapshotDoesNotExist: ERROR_SNAPSHOT_DOES_NOT_EXIST,
        DatabaseSnapshotMaxLocksExceededException: ERROR_MAX_LOCKS_PER_TRANSACTION_EXCEEDED,
    }

    job_exceptions_map = {
        DatabaseSnapshotMaxLocksExceededException: DatabaseSnapshotMaxLocksExceededException.message
    }

    def transaction_atomic_context(self, job: CreateSnapshotJob):
        application = (
            CoreHandler()
            .get_user_application(job.user, job.snapshot.snapshot_from_application.id)
            .specific
        )
        application_type = application_type_registry.get_by_model(application)
        return application_type.export_safe_transaction_context(application)

    def run(self, job: CreateSnapshotJob, progress):
        from .actions import CreateSnapshotActionType

        action_type_registry.get(CreateSnapshotActionType.type).do(
            job.user, job.snapshot, progress
        )


class RestoreSnapshotJobType(JobType):
    type = "restore_snapshot"
    model_class = RestoreSnapshotJob
    max_count = 1

    api_exceptions_map = {
        UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        SnapshotDoesNotExist: ERROR_SNAPSHOT_DOES_NOT_EXIST,
    }

    def run(self, job: RestoreSnapshotJob, progress):
        from .actions import RestoreSnapshotActionType

        action_type_registry.get(RestoreSnapshotActionType.type).do(
            job.user, job.snapshot, progress
        )
