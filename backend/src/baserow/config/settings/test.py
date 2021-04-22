from .base import *  # noqa: F403, F401


CELERY_BROKER_BACKEND = "memory"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

USER_FILES_DIRECTORY = "user_files"
USER_THUMBNAILS_DIRECTORY = "thumbnails"
USER_THUMBNAILS = {"tiny": [21, 21]}

# Make sure that we are not using the `MEDIA_URL` environment variable because that
# could break the tests. They are expecting it to be 'http://localhost:8000/media/'
# because that is default value in `base.py`.
MEDIA_URL = "http://localhost:8000/media/"
