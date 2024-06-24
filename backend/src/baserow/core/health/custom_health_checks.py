from django.conf import settings

from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import ServiceWarning


class DebugModeHealthCheck(BaseHealthCheckBackend):
    critical_service = False

    def check_status(self):
        if settings.DEBUG:
            raise ServiceWarning(
                "DEBUG is enabled, this is insecure for production or public usage."
            )

    def identifier(self):
        return self.__class__.__name__


class HerokuExternalFileStorageConfiguredHealthCheck(BaseHealthCheckBackend):
    critical_service = False

    def check_status(self):
        if settings.BASE_FILE_STORAGE == "django.core.files.storage.FileSystemStorage":
            raise ServiceWarning(
                "Any uploaded files will be lost on dyno restart because you have "
                "not configured an external file storage service. Please set "
                "AWS_ACCESS_KEY_ID and related env vars to prevent file loss."
            )

    def identifier(self):
        return self.__class__.__name__
