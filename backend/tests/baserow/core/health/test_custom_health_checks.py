from django.test.utils import override_settings

import pytest
from health_check.exceptions import ServiceWarning

from baserow.core.health.custom_health_checks import (
    DebugModeHealthCheck,
    HerokuExternalFileStorageConfiguredHealthCheck,
)


@override_settings(DEBUG=True)
def test_debug_health_check_raises_when_debug_true():
    with pytest.raises(ServiceWarning):
        DebugModeHealthCheck().check_status()


@override_settings(DEBUG=False)
def test_debug_health_check_does_not_raise_when_debug_false():
    DebugModeHealthCheck().check_status()


@override_settings(BASE_FILE_STORAGE="django.core.files.storage.FileSystemStorage")
def test_heroku_health_check_raises_when_default_storage_set():
    with pytest.raises(ServiceWarning):
        HerokuExternalFileStorageConfiguredHealthCheck().check_status()


@override_settings(BASE_FILE_STORAGE="storages.backends.s3boto3.S3Boto3Storage")
def test_heroku_health_check_doesnt_raise_when_boto_set():
    HerokuExternalFileStorageConfiguredHealthCheck().check_status()
