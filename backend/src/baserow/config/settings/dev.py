from .base import *  # noqa: F403, F401


DEBUG = True
CELERY_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

try:
    from .local import *  # noqa: F403, F401
except ImportError:
    pass
