from rest_framework import serializers
from rest_framework.status import HTTP_404_NOT_FOUND

from baserow.core.jobs.exceptions import JobTypeAlreadyRegistered
from baserow.core.jobs.models import Job
from baserow.core.jobs.registries import JobType, job_type_registry

TEST_EXCEPTION = (
    "TEST_EXCEPTION",
    HTTP_404_NOT_FOUND,
    "...",
)


class TestException(Exception):
    ...


class TmpJobType1(JobType):
    type = "tmp_job_type_1"

    max_count = 1

    model_class = Job

    api_exceptions_map = {
        TestException: TEST_EXCEPTION,
    }

    request_serializer_field_names = [
        "test_request_field",
    ]

    request_serializer_field_overrides = {
        "test_request_field": serializers.IntegerField(
            required=True,
        ),
    }

    serializer_field_names = [
        "test_field",
    ]

    serializer_field_overrides = {
        "test_field": serializers.IntegerField(default=42),
    }

    def prepare_values(self, values, user):
        return {}

    def run(self, job, progress):
        pass


class TmpJobType2(JobType):
    type = "tmp_job_type_2"

    max_count = 3

    model_class = Job

    def run(self, job, progress):
        pass


class TmpJobType3(JobType):
    type = "tmp_job_type_3"

    model_class = Job

    max_count = 1

    api_exceptions_map = {
        TestException: TEST_EXCEPTION,
    }

    request_serializer_field_names = [
        "test_request_field",
    ]

    request_serializer_field_overrides = {
        "test_request_field": serializers.IntegerField(
            required=True,
        ),
    }

    serializer_field_names = [
        "test_field",
    ]

    serializer_field_overrides = {
        "test_field": serializers.IntegerField(default=42),
    }

    def prepare_values(self, values, user):
        raise TestException("test")

    def run(self, job, progress):
        pass


class JobFixtures:
    def register_temp_job_types(self):
        try:
            job_type_registry.register(TmpJobType1())
            job_type_registry.register(TmpJobType2())
            job_type_registry.register(TmpJobType3())
        except JobTypeAlreadyRegistered:
            pass

    def create_fake_job(self, **kwargs):
        self.register_temp_job_types()

        kwargs["user"] = kwargs.get("user", self.create_user())

        job_type_name = kwargs.pop("type", "tmp_job_type_1")
        job_type = job_type_registry.get(job_type_name)

        return job_type.model_class.objects.create(**kwargs)
