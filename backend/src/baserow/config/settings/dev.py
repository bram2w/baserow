from .base import *  # noqa: F403, F401
import snoop

DEBUG = True
CELERY_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
WEBHOOKS_MAX_CONSECUTIVE_TRIGGER_FAILURES = 4
WEBHOOKS_MAX_RETRIES_PER_CALL = 4

INSTALLED_APPS += ["django_extensions", "silk"]  # noqa: F405

MIDDLEWARE += [  # noqa: F405
    "silk.middleware.SilkyMiddleware",
]

SILKY_ANALYZE_QUERIES = True

snoop.install()

try:
    from .local import *  # noqa: F403, F401
except ImportError:
    pass
