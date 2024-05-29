import pytest

from baserow.contrib.builder.domains.exceptions import DomainDoesNotExist
from baserow.contrib.builder.domains.job_types import PublishDomainJobType
from baserow.contrib.builder.domains.models import PublishDomainJob
from baserow.core.jobs.constants import JOB_FAILED, JOB_FINISHED
from baserow.core.jobs.handler import JobHandler
from baserow.core.jobs.tasks import run_async_job


@pytest.mark.django_db(transaction=True)
def test_publish_domain_job_type(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    domain1 = data_fixture.create_builder_custom_domain(builder=builder)

    publish_domain_job = JobHandler().create_and_start_job(
        user,
        PublishDomainJobType.type,
        domain=domain1,
    )

    publish_domain_job.refresh_from_db()

    assert publish_domain_job.state == JOB_FINISHED
    assert publish_domain_job.domain.published_to is not None


@pytest.mark.django_db(transaction=True)
def test_publish_domain_job_type_with_deleted_domain(data_fixture):
    user = data_fixture.create_user()
    job = PublishDomainJob.objects.create(user=user)

    with pytest.raises(DomainDoesNotExist):
        run_async_job(job.id)

    job.refresh_from_db()

    assert job.state == JOB_FAILED
    assert (
        job.error == "The Domain has been deleted prior to the execution of this task."
    )
    assert (
        job.human_readable_error
        == "Something went wrong during the publish_domain job execution."
    )
