import pytest

from baserow.contrib.builder.domains.job_types import PublishDomainJobType
from baserow.core.jobs.constants import JOB_FINISHED
from baserow.core.jobs.handler import JobHandler


@pytest.mark.django_db(transaction=True)
def test_publish_domain_job_type(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    domain1 = data_fixture.create_builder_domain(builder=builder)

    publish_domain_job = JobHandler().create_and_start_job(
        user,
        PublishDomainJobType.type,
        domain=domain1,
    )

    publish_domain_job.refresh_from_db()

    assert publish_domain_job.state == JOB_FINISHED
    assert publish_domain_job.domain.published_to is not None
