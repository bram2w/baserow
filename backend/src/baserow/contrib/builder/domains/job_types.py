from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.core.exceptions import UserNotInWorkspace
from baserow.core.jobs.registries import JobType
from baserow.core.registries import application_type_registry

from .models import PublishDomainJob


class PublishDomainJobType(JobType):
    """
    Asynchronously executes a domain publishing operation.
    """

    type = "publish_domain"
    model_class = PublishDomainJob
    max_count = 2

    api_exceptions_map = {
        UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
    }

    def transaction_atomic_context(self, job: PublishDomainJob):
        application_type = application_type_registry.get("builder")
        return application_type.export_safe_transaction_context(job.domain.builder)

    def run(self, job: PublishDomainJob, progress):
        from .service import DomainService

        DomainService().publish(job.user, job.domain, progress)
