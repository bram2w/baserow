import snoop

from .base import *  # noqa: F403, F401

SECRET_KEY = os.getenv("SECRET_KEY", "dev_hardcoded_secret_key")  # noqa: F405
SIMPLE_JWT["SIGNING_KEY"] = os.getenv(  # noqa: F405
    "BASEROW_JWT_SIGNING_KEY", "test_hardcoded_jwt_signing_key"
)

DEBUG = True
BASEROW_WEBHOOKS_MAX_CONSECUTIVE_TRIGGER_FAILURES = 4
BASEROW_WEBHOOKS_MAX_RETRIES_PER_CALL = 4

INSTALLED_APPS += ["django_extensions", "silk"]  # noqa: F405

MIDDLEWARE += [  # noqa: F405
    "silk.middleware.SilkyMiddleware",
]

SILKY_ANALYZE_QUERIES = True

snoop.install()

CELERY_EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = False
EMAIL_HOST = "mailhog"
EMAIL_PORT = 1025

BASEROW_MAX_ROW_REPORT_ERROR_COUNT = 10  # To trigger this exception easily

try:
    from .local import *  # noqa: F403, F401
except ImportError:
    pass
