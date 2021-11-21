from .base import *  # noqa: F403, F401


DEBUG = True
CELERY_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
WEBHOOKS_MAX_CONSECUTIVE_TRIGGER_FAILURES = 4
WEBHOOKS_MAX_RETRIES_PER_CALL = 4

try:
    from .local import *  # noqa: F403, F401
except ImportError:
    pass
