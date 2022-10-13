from copy import deepcopy

from .base import *  # noqa: F403, F401

TESTS = True

# This is a hardcoded key for test runs only.
SECRET_KEY = "test_hardcoded_secret_key"  # nosec
SIMPLE_JWT["SIGNING_KEY"] = "test_hardcoded_jwt_signing_key"  # noqa: F405

CELERY_BROKER_BACKEND = "memory"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# Open a second database connection that can be used to test transactions.
DATABASES["default-copy"] = deepcopy(DATABASES["default"])  # noqa: F405

USER_FILES_DIRECTORY = "user_files"
USER_THUMBNAILS_DIRECTORY = "thumbnails"
USER_THUMBNAILS = {"tiny": [21, 21]}

# Make sure that we are not using the `MEDIA_URL` environment variable because that
# could break the tests. They are expecting it to be 'http://localhost:8000/media/'
# because that is default value in `base.py`.
MEDIA_URL = "http://localhost:8000/media/"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "KEY_PREFIX": "baserow-default-cache",
        "VERSION": VERSION,  # noqa: F405
    },
    GENERATED_MODEL_CACHE_NAME: {  # noqa: F405
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "KEY_PREFIX": f"baserow-{GENERATED_MODEL_CACHE_NAME}-cache",  # noqa: F405
        "VERSION": None,
    },
}


class Everything(object):
    def __contains__(self, other):
        return True


# Overriding the FEATURE_FLAGS object in the tests because if we do `feature` in
# settings.FEATURE_FLAGS, we always want it to be enabled, otherwise the tests might
# fail.
# FEATURE_FLAGS = Everything()
