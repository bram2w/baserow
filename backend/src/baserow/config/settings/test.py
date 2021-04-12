from .base import *  # noqa: F403, F401


CELERY_BROKER_BACKEND = "memory"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

USER_FILES_DIRECTORY = "user_files"
USER_THUMBNAILS_DIRECTORY = "thumbnails"
USER_THUMBNAILS = {"tiny": [21, 21]}
