import datetime
import importlib
import os
import re
from decimal import Decimal
from ipaddress import ip_network
from pathlib import Path
from urllib.parse import urljoin, urlparse

import dj_database_url
from celery.schedules import crontab
from corsheaders.defaults import default_headers

from baserow.version import VERSION

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASEROW_PLUGIN_DIR_PATH = Path(os.environ.get("BASEROW_PLUGIN_DIR", "/baserow/plugins"))

if BASEROW_PLUGIN_DIR_PATH.exists():
    BASEROW_PLUGIN_FOLDERS = [
        file
        for file in BASEROW_PLUGIN_DIR_PATH.iterdir()
        if file.is_dir() and Path(file, "backend").exists()
    ]
else:
    BASEROW_PLUGIN_FOLDERS = []

BASEROW_BACKEND_PLUGIN_NAMES = [d.name for d in BASEROW_PLUGIN_FOLDERS]


# SECURITY WARNING: keep the secret key used in production secret!
if "SECRET_KEY" in os.environ:
    SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("BASEROW_BACKEND_DEBUG", "off") == "on"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
ALLOWED_HOSTS += os.getenv("BASEROW_EXTRA_ALLOWED_HOSTS", "").split(",")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "channels",
    "drf_spectacular",
    "djcelery_email",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.contrib.migrations",
    "health_check.contrib.redis",
    "baserow.core",
    "baserow.api",
    "baserow.ws",
    "baserow.contrib.database",
    "baserow_premium",
]

BASEROW_FULL_HEALTHCHECKS = os.getenv("BASEROW_FULL_HEALTHCHECKS", None)
if BASEROW_FULL_HEALTHCHECKS is not None:
    INSTALLED_APPS += ["health_check.storage", "health_check.contrib.psutil"]

ADDITIONAL_APPS = os.getenv("ADDITIONAL_APPS", "").split(",")
if ADDITIONAL_APPS is not None:
    INSTALLED_APPS += [app.strip() for app in ADDITIONAL_APPS if app.strip() != ""]

if BASEROW_BACKEND_PLUGIN_NAMES:
    print(f"Loaded backend plugins: {','.join(BASEROW_BACKEND_PLUGIN_NAMES)}")
    INSTALLED_APPS.extend(BASEROW_BACKEND_PLUGIN_NAMES)

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "baserow.middleware.BaserowCustomHttp404Middleware",
]

ROOT_URLCONF = "baserow.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "baserow.config.wsgi.application"
ASGI_APPLICATION = "baserow.config.asgi.application"

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_USERNAME = os.getenv("REDIS_USER", "")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_PROTOCOL = os.getenv("REDIS_PROTOCOL", "redis")
REDIS_URL = os.getenv(
    "REDIS_URL",
    f"{REDIS_PROTOCOL}://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0",
)

BASEROW_GROUP_STORAGE_USAGE_ENABLED = (
    os.getenv("BASEROW_GROUP_STORAGE_USAGE_ENABLED", "false") == "true"
)

BASEROW_GROUP_STORAGE_USAGE_QUEUE = os.getenv(
    "BASEROW_GROUP_STORAGE_USAGE_QUEUE", "export"
)

BASEROW_COUNT_ROWS_ENABLED = os.getenv("BASEROW_COUNT_ROWS_ENABLED", "false") == "true"

CELERY_BROKER_URL = REDIS_URL
CELERY_TASK_ROUTES = {
    "baserow.contrib.database.export.tasks.run_export_job": {"queue": "export"},
    "baserow.contrib.database.export.tasks.clean_up_old_jobs": {"queue": "export"},
    "baserow.core.trash.tasks.mark_old_trash_for_permanent_deletion": {
        "queue": "export"
    },
    "baserow.core.trash.tasks.permanently_delete_marked_trash": {"queue": "export"},
    "baserow.core.usage.tasks": {"queue": BASEROW_GROUP_STORAGE_USAGE_QUEUE},
    "baserow.contrib.database.table.tasks.run_row_count_job": {"queue": "export"},
    "baserow.core.jobs.tasks.clean_up_jobs": {"queue": "export"},
}
CELERY_SOFT_TIME_LIMIT = 60 * 5  # 5 minutes
CELERY_TIME_LIMIT = CELERY_SOFT_TIME_LIMIT + 60  # 60 seconds

CELERY_REDBEAT_REDIS_URL = REDIS_URL
# Explicitly set the same value as the default loop interval here so we can use it
# later. CELERY_BEAT_MAX_LOOP_INTERVAL < CELERY_REDBEAT_LOCK_TIMEOUT must be kept true
# as otherwise a beat instance will acquire the lock, do scheduling, go to sleep for
# CELERY_BEAT_MAX_LOOP_INTERVAL before waking up where it assumes it still owns the lock
# however if the lock timeout is less than the interval the lock will have been released
# and the beat instance will crash as it attempts to extend the lock which it no longer
# owns.
CELERY_BEAT_MAX_LOOP_INTERVAL = os.getenv("CELERY_BEAT_MAX_LOOP_INTERVAL", 20)
# By default CELERY_REDBEAT_LOCK_TIMEOUT = 5 * CELERY_BEAT_MAX_LOOP_INTERVAL
# Only one beat instance can hold this lock and schedule tasks at any one time.
# This means if one celery-beat instance crashes any other replicas waiting to take over
# will by default wait 25 minutes until the lock times out and they can acquire
# the lock to start scheduling tasks again.
# Instead we just set it to be slightly longer than the loop interval that beat uses.
# This means beat wakes up, checks the schedule and extends the lock every
# CELERY_BEAT_MAX_LOOP_INTERVAL seconds. If it crashes or fails to wake up
# then 80 seconds after the lock was last extended it will be released and a new
# scheduler will acquire the lock and take over.
CELERY_REDBEAT_LOCK_TIMEOUT = os.getenv(
    "CELERY_REDBEAT_LOCK_TIMEOUT", CELERY_BEAT_MAX_LOOP_INTERVAL + 60
)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
if "DATABASE_URL" in os.environ:
    DATABASES = {
        "default": dj_database_url.parse(os.getenv("DATABASE_URL"), conn_max_age=600)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DATABASE_NAME", "baserow"),
            "USER": os.getenv("DATABASE_USER", "baserow"),
            "PASSWORD": os.getenv("DATABASE_PASSWORD", "baserow"),
            "HOST": os.getenv("DATABASE_HOST", "db"),
            "PORT": os.getenv("DATABASE_PORT", "5432"),
        }
    }

GENERATED_MODEL_CACHE_NAME = "generated-models"
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "baserow-default-cache",
        "VERSION": VERSION,
    },
    GENERATED_MODEL_CACHE_NAME: {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": f"baserow-{GENERATED_MODEL_CACHE_NAME}-cache",
        "VERSION": None,
    },
}

# Should contain the database connection name of the database where the user tables
# are stored. This can be different than the default database because there are not
# going to be any relations between the application schema and the user schema.
USER_TABLE_DATABASE = "default"

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "baserow.core.user.password_validation.MaximumLengthValidator",
    },
]

# We need the `AllowAllUsersModelBackend` in order to respond with a proper error
# message when the user is not active. The only thing it does, is allowing non active
# users to authenticate, but the user still can't obtain or use a JWT token or database
# token because the user needs to be active to use that.
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.AllowAllUsersModelBackend"]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", "English"),
    ("fr", "French"),
    ("nl", "Dutch"),
    ("de", "German"),
    ("es", "Spanish"),
    ("it", "Italian"),
]

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/static/"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "baserow.api.authentication.JSONWebTokenAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_SCHEMA_CLASS": "baserow.api.openapi.AutoSchema",
}

PUBLIC_VIEW_AUTHORIZATION_HEADER = "Baserow-View-Authorization"

CORS_ORIGIN_ALLOW_ALL = True
CLIENT_SESSION_ID_HEADER = "ClientSessionId"
MAX_CLIENT_SESSION_ID_LENGTH = 256

CLIENT_UNDO_REDO_ACTION_GROUP_ID_HEADER = "ClientUndoRedoActionGroupId"
MAX_UNDOABLE_ACTIONS_PER_ACTION_GROUP = 2

CORS_ALLOW_HEADERS = list(default_headers) + [
    "WebSocketId",
    PUBLIC_VIEW_AUTHORIZATION_HEADER,
    CLIENT_SESSION_ID_HEADER,
    CLIENT_UNDO_REDO_ACTION_GROUP_ID_HEADER,
]

JWT_AUTH = {
    "JWT_EXPIRATION_DELTA": datetime.timedelta(seconds=60 * 60),
    "JWT_ALLOW_REFRESH": True,
    "JWT_REFRESH_EXPIRATION_DELTA": datetime.timedelta(days=7),
    "JWT_AUTH_HEADER_PREFIX": "JWT",
    "JWT_RESPONSE_PAYLOAD_HANDLER": "baserow.api.user.jwt.jwt_response_payload_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Baserow API spec",
    "DESCRIPTION": "",
    "CONTACT": {"url": "https://baserow.io/contact"},
    "LICENSE": {
        "name": "MIT",
        "url": "https://gitlab.com/bramw/baserow/-/blob/master/LICENSE",
    },
    "VERSION": "1.12.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "Settings"},
        {"name": "User"},
        {"name": "User files"},
        {"name": "Groups"},
        {"name": "Group invitations"},
        {"name": "Templates"},
        {"name": "Trash"},
        {"name": "Applications"},
        {"name": "Snapshots"},
        {"name": "Jobs"},
        {"name": "Database tables"},
        {"name": "Database table fields"},
        {"name": "Database table views"},
        {"name": "Database table view filters"},
        {"name": "Database table view sortings"},
        {"name": "Database table view decorations"},
        {"name": "Database table grid view"},
        {"name": "Database table gallery view"},
        {"name": "Database table form view"},
        {"name": "Database table kanban view"},
        {"name": "Database table rows"},
        {"name": "Database table export"},
        {"name": "Database table webhooks"},
        {"name": "Database tokens"},
        {"name": "Admin"},
    ],
    "ENUM_NAME_OVERRIDES": {
        "NumberDecimalPlacesEnum": [
            (0, "1"),
            (1, "1.0"),
            (2, "1.00"),
            (3, "1.000"),
            (4, "1.0000"),
            (5, "1.00000"),
        ],
        "ViewTypesEnum": [
            "grid",
            "gallery",
            "form",
            "kanban",
        ],
        "FieldTypesEnum": [
            "text",
            "long_text",
            "url",
            "email",
            "number",
            "rating",
            "boolean",
            "date",
            "last_modified",
            "created_on",
            "link_row",
            "file",
            "single_select",
            "multiple_select",
            "phone_number",
            "formula",
            "lookup",
        ],
        "ViewFilterTypesEnum": [
            "equal",
            "not_equal",
            "filename_contains",
            "has_file_type",
            "contains",
            "contains_not",
            "length_is_lower_than",
            "higher_than",
            "lower_than",
            "date_equal",
            "date_before",
            "date_after",
            "date_not_equal",
            "date_equals_today",
            "date_equals_days_ago",
            "date_equals_week",
            "date_equals_month",
            "date_equals_day_of_month",
            "date_equals_year",
            "single_select_equal",
            "single_select_not_equal",
            "link_row_has",
            "link_row_has_not",
            "boolean",
            "empty",
            "not_empty",
            "multiple_select_has",
            "multiple_select_has_not",
        ],
        "EventTypesEnum": ["rows.created", "rows.updated", "rows.deleted"],
    },
}

# The storage must always overwrite existing files.
DEFAULT_FILE_STORAGE = "baserow.core.storage.OverwriteFileSystemStorage"

# Optional S3 storage configuration
if os.getenv("AWS_ACCESS_KEY_ID", "") != "":
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    AWS_S3_FILE_OVERWRITE = True
    AWS_DEFAULT_ACL = "public-read"

if os.getenv("AWS_S3_REGION_NAME", "") != "":
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")

if os.getenv("AWS_S3_ENDPOINT_URL", "") != "":
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")

if os.getenv("AWS_S3_CUSTOM_DOMAIN", "") != "":
    AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN")

BASEROW_PUBLIC_URL = os.getenv("BASEROW_PUBLIC_URL")
if BASEROW_PUBLIC_URL:
    PUBLIC_BACKEND_URL = BASEROW_PUBLIC_URL
    PUBLIC_WEB_FRONTEND_URL = BASEROW_PUBLIC_URL
    if BASEROW_PUBLIC_URL == "http://localhost":
        print(
            "WARNING: Baserow is configured to use a BASEROW_PUBLIC_URL of "
            "http://localhost. If you attempt to access Baserow on any other hostname "
            "requests to the backend will fail as they will be from an unknown host. "
            "Please set BASEROW_PUBLIC_URL if you will be accessing Baserow "
            "from any other URL then http://localhost."
        )
else:
    PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")
    PUBLIC_WEB_FRONTEND_URL = os.getenv(
        "PUBLIC_WEB_FRONTEND_URL", "http://localhost:3000"
    )
    if "PUBLIC_BACKEND_URL" not in os.environ:
        print(
            "WARNING: Baserow is configured to use a PUBLIC_BACKEND_URL of "
            "http://localhost:8000. If you attempt to access Baserow on any other "
            "hostname requests to the backend will fail as they will be from an "
            "unknown host."
            "Please ensure you set PUBLIC_BACKEND_URL if you will be accessing "
            "Baserow from any other URL then http://localhost."
        )
    if "PUBLIC_WEB_FRONTEND_URL" not in os.environ:
        print(
            "WARNING: Baserow is configured to use a default PUBLIC_WEB_FRONTEND_URL "
            "of http://localhost:3000. Emails sent by Baserow will use links pointing "
            "to http://localhost:3000 when telling users how to access your server. If "
            "this is incorrect please ensure you have set PUBLIC_WEB_FRONTEND_URL to "
            "the URL where users can access your Baserow server."
        )

PRIVATE_BACKEND_URL = os.getenv("PRIVATE_BACKEND_URL", "http://backend:8000")
PUBLIC_BACKEND_HOSTNAME = urlparse(PUBLIC_BACKEND_URL).hostname
PUBLIC_WEB_FRONTEND_HOSTNAME = urlparse(PUBLIC_WEB_FRONTEND_URL).hostname
PRIVATE_BACKEND_HOSTNAME = urlparse(PRIVATE_BACKEND_URL).hostname

if PUBLIC_BACKEND_HOSTNAME:
    ALLOWED_HOSTS.append(PUBLIC_BACKEND_HOSTNAME)

if PRIVATE_BACKEND_HOSTNAME:
    ALLOWED_HOSTS.append(PRIVATE_BACKEND_HOSTNAME)

FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@localhost")
RESET_PASSWORD_TOKEN_MAX_AGE = 60 * 60 * 48  # 48 hours

ROW_PAGE_SIZE_LIMIT = int(os.getenv("BASEROW_ROW_PAGE_SIZE_LIMIT", 200))
BATCH_ROWS_SIZE_LIMIT = int(
    os.getenv("BATCH_ROWS_SIZE_LIMIT", 200)
)  # How many rows can be modified at once.

TRASH_PAGE_SIZE_LIMIT = 200  # How many trash entries can be requested at once.
ROW_COMMENT_PAGE_SIZE_LIMIT = 200  # How many row comments can be requested at once.
# How many unique row values can be requested at once.
UNIQUE_ROW_VALUES_SIZE_LIMIT = 50

# The amount of rows that can be imported when creating a table.
INITIAL_TABLE_DATA_LIMIT = None
if "INITIAL_TABLE_DATA_LIMIT" in os.environ:
    INITIAL_TABLE_DATA_LIMIT = int(os.getenv("INITIAL_TABLE_DATA_LIMIT"))

BASEROW_INITIAL_CREATE_SYNC_TABLE_DATA_LIMIT = int(
    os.getenv("BASEROW_INITIAL_CREATE_SYNC_TABLE_DATA_LIMIT", 5000)
)

MEDIA_URL_PATH = "/media/"
MEDIA_URL = os.getenv("MEDIA_URL", urljoin(PUBLIC_BACKEND_URL, MEDIA_URL_PATH))
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/baserow/media")

# Indicates the directory where the user files and user thumbnails are stored.
USER_FILES_DIRECTORY = "user_files"
USER_THUMBNAILS_DIRECTORY = "thumbnails"
BASEROW_FILE_UPLOAD_SIZE_LIMIT_MB = int(
    Decimal(os.getenv("BASEROW_FILE_UPLOAD_SIZE_LIMIT_MB", 1024 * 1024)) * 1024 * 1024
)  # ~1TB by default

EXPORT_FILES_DIRECTORY = "export_files"
EXPORT_CLEANUP_INTERVAL_MINUTES = 5
EXPORT_FILE_EXPIRE_MINUTES = 60

USAGE_CALCULATION_INTERVAL = crontab(minute=0, hour=0)  # Midnight

ROW_COUNT_INTERVAL = crontab(minute=0, hour=0)  # Midnight

EMAIL_BACKEND = "djcelery_email.backends.CeleryEmailBackend"

if os.getenv("EMAIL_SMTP", ""):
    CELERY_EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    # EMAIL_SMTP_USE_TLS OR EMAIL_SMTP_USE_TLS for backwards compatibility after
    # fixing #448.
    EMAIL_USE_TLS = bool(os.getenv("EMAIL_SMTP_USE_TLS", "")) or bool(
        os.getenv("EMAIL_SMPT_USE_TLS", "")
    )
    EMAIL_HOST = os.getenv("EMAIL_SMTP_HOST", "localhost")
    EMAIL_PORT = os.getenv("EMAIL_SMTP_PORT", "25")
    EMAIL_HOST_USER = os.getenv("EMAIL_SMTP_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_SMTP_PASSWORD", "")
else:
    CELERY_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Configurable thumbnails that are going to be generated when a user uploads an image
# file.
USER_THUMBNAILS = {"tiny": [None, 21], "small": [48, 48], "card_cover": [None, 160]}

# The directory that contains the all the templates in JSON format. When for example
# the `sync_templates` management command is called, then the templates in the
# database will be synced with these files.
APPLICATION_TEMPLATES_DIR = os.path.join(BASE_DIR, "../../../templates")
# The template that must be selected when the user first opens the templates select
# modal.
DEFAULT_APPLICATION_TEMPLATE = "project-tracker"

MAX_FIELD_LIMIT = 1500

# If you change this default please also update the default for the web-frontend found
# in web-frontend/modules/core/module.js:55
HOURS_UNTIL_TRASH_PERMANENTLY_DELETED = os.getenv(
    "HOURS_UNTIL_TRASH_PERMANENTLY_DELETED", 24 * 3
)
OLD_TRASH_CLEANUP_CHECK_INTERVAL_MINUTES = 5

MAX_ROW_COMMENT_LENGTH = 10000

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# For now force the old os dependant behaviour of file uploads as users might be relying
# on it. See
# https://docs.djangoproject.com/en/3.2/releases/3.0/#new-default-value-for-the-file-upload-permissions-setting
FILE_UPLOAD_PERMISSIONS = None

MAX_FORMULA_STRING_LENGTH = 10000
MAX_FIELD_REFERENCE_DEPTH = 1000
DONT_UPDATE_FORMULAS_AFTER_MIGRATION = bool(
    os.getenv("DONT_UPDATE_FORMULAS_AFTER_MIGRATION", "")
)

BASEROW_WEBHOOKS_MAX_CONSECUTIVE_TRIGGER_FAILURES = int(
    os.getenv("BASEROW_WEBHOOKS_MAX_CONSECUTIVE_TRIGGER_FAILURES", 8)
)
BASEROW_WEBHOOKS_MAX_RETRIES_PER_CALL = int(
    os.getenv("BASEROW_WEBHOOKS_MAX_RETRIES_PER_CALL", 8)
)
BASEROW_WEBHOOKS_MAX_PER_TABLE = int(os.getenv("BASEROW_WEBHOOKS_MAX_PER_TABLE", 20))
BASEROW_WEBHOOKS_MAX_CALL_LOG_ENTRIES = int(
    os.getenv("BASEROW_WEBHOOKS_MAX_CALL_LOG_ENTRIES", 10)
)
BASEROW_WEBHOOKS_REQUEST_TIMEOUT_SECONDS = int(
    os.getenv("BASEROW_WEBHOOKS_REQUEST_TIMEOUT_SECONDS", 5)
)
BASEROW_WEBHOOKS_ALLOW_PRIVATE_ADDRESS = bool(
    os.getenv("BASEROW_WEBHOOKS_ALLOW_PRIVATE_ADDRESS", False)
)
BASEROW_WEBHOOKS_IP_BLACKLIST = [
    ip_network(ip.strip())
    for ip in os.getenv("BASEROW_WEBHOOKS_IP_BLACKLIST", "").split(",")
    if ip.strip() != ""
]
BASEROW_WEBHOOKS_IP_WHITELIST = [
    ip_network(ip.strip())
    for ip in os.getenv("BASEROW_WEBHOOKS_IP_WHITELIST", "").split(",")
    if ip.strip() != ""
]
BASEROW_WEBHOOKS_URL_REGEX_BLACKLIST = [
    re.compile(url_regex.strip())
    for url_regex in os.getenv("BASEROW_WEBHOOKS_URL_REGEX_BLACKLIST", "").split(",")
    if url_regex.strip() != ""
]
BASEROW_WEBHOOKS_URL_CHECK_TIMEOUT_SECS = int(
    os.getenv("BASEROW_WEBHOOKS_URL_CHECK_TIMEOUT_SECS", "10")
)

# ======== WARNING ========
# Please read and understand everything at:
# https://docs.djangoproject.com/en/3.2/ref/settings/#secure-proxy-ssl-header
# before enabling this setting otherwise you can compromise your site’s security.
# This setting will ensure the "next" urls provided by the various paginated API
# endpoints will be returned with https when appropriate.
# If using gunicorn also behind the proxy you might also need to set
# --forwarded-allow-ips='*'. See the following link for more information:
# https://stackoverflow.com/questions/62337379/how-to-append-nginx-ip-to-x-forwarded
# -for-in-kubernetes-nginx-ingress-controller

if bool(os.getenv("BASEROW_ENABLE_SECURE_PROXY_SSL_HEADER", False)):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS = bool(
    os.getenv("DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS", "")
)

BASEROW_BACKEND_LOG_LEVEL = os.getenv("BASEROW_BACKEND_LOG_LEVEL", "INFO")
BASEROW_BACKEND_DATABASE_LOG_LEVEL = os.getenv(
    "BASEROW_BACKEND_DATABASE_LOG_LEVEL", "ERROR"
)


BASEROW_JOB_EXPIRATION_TIME_LIMIT = int(
    os.getenv("BASEROW_JOB_EXPIRATION_TIME_LIMIT", 30 * 24 * 60)  # 30 days
)
BASEROW_JOB_SOFT_TIME_LIMIT = int(
    os.getenv("BASEROW_JOB_SOFT_TIME_LIMIT", 60 * 30)  # 30 minutes
)
BASEROW_JOB_CLEANUP_INTERVAL_MINUTES = int(
    os.getenv("BASEROW_JOB_CLEANUP_INTERVAL_MINUTES", 5)  # 5 minutes
)
BASEROW_MAX_ROW_REPORT_ERROR_COUNT = int(
    os.getenv("BASEROW_MAX_ROW_REPORT_ERROR_COUNT", 30)
)
BASEROW_MAX_SNAPSHOTS_PER_GROUP = int(os.getenv("BASEROW_MAX_SNAPSHOTS_PER_GROUP", -1))
BASEROW_SNAPSHOT_EXPIRATION_TIME_DAYS = int(
    os.getenv("BASEROW_SNAPSHOT_EXPIRATION_TIME_DAYS", 360)  # 360 days
)

# A comma separated list of feature flags used to enable in-progress or not ready
# features for developers. See docs/development/feature-flags.md for more info.
FEATURE_FLAGS = [flag.strip() for flag in os.getenv("FEATURE_FLAGS", "").split(",")]

OLD_ACTION_CLEANUP_INTERVAL_MINUTES = os.getenv(
    "OLD_ACTION_CLEANUP_INTERVAL_MINUTES", 5
)
MINUTES_UNTIL_ACTION_CLEANED_UP = os.getenv("MINUTES_UNTIL_ACTION_CLEANED_UP", "120")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(levelname)s %(asctime)s %(name)s.%(funcName)s:%(lineno)s- %("
            "message)s "
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "gunicorn": {
            "level": BASEROW_BACKEND_LOG_LEVEL,
            "handlers": ["console"],
            "propagate": True,
        },
        "django": {
            "handlers": ["console"],
            "level": BASEROW_BACKEND_LOG_LEVEL,
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console"],
            "level": BASEROW_BACKEND_LOG_LEVEL,
            "propagate": True,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": BASEROW_BACKEND_DATABASE_LOG_LEVEL,
            "propagate": True,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": BASEROW_BACKEND_LOG_LEVEL,
    },
}

# Now incorrectly named old variable, previously we would run `sync_templates` prior
# to starting the gunicorn server in Docker. This variable would prevent that from
# happening. Now we sync_templates in an async job triggered after migration.
# This variable if not true will now stop the async job from being triggered.
SYNC_TEMPLATES_ON_STARTUP = os.getenv("SYNC_TEMPLATES_ON_STARTUP", "true") == "true"
BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION = os.getenv(
    "BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION", None
)

if BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION is None:
    # If the new correctly named environment variable is not set, default to using
    # the old now incorrectly named SYNC_TEMPLATES_ON_STARTUP.
    BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION = SYNC_TEMPLATES_ON_STARTUP
else:
    # The new correctly named environment variable is set, so use that instead of
    # the old.
    BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION = (
        BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION == "true"
    )

BASEROW_SYNC_TEMPLATES_TIME_LIMIT = int(
    os.getenv("BASEROW_SYNC_TEMPLATES_TIME_LIMIT", 60 * 30)
)

APPEND_SLASH = False

BASEROW_DISABLE_MODEL_CACHE = bool(os.getenv("BASEROW_DISABLE_MODEL_CACHE", ""))
BASEROW_NOWAIT_FOR_LOCKS = not bool(
    os.getenv("BASEROW_WAIT_INSTEAD_OF_409_CONFLICT_ERROR", False)
)

# Indicates whether we are running the tests or not. Set to True in the test.py settings
# file used by pytest.ini
TESTS = False


# Allows accessing and setting values on a dictionary like an object. Using this
# we can pass plugin authors a `settings` object which can modify the settings like
# they expect (settings.SETTING = 'test') etc.
class AttrDict(dict):
    def __getattr__(self, item):
        return super().__getitem__(item)

    def __setattr__(self, item, value):
        return super().__setitem__(item, value)


for plugin in BASEROW_BACKEND_PLUGIN_NAMES:
    try:
        mod = importlib.import_module(plugin + ".config.settings.settings")
        # The plugin should have a setup function which accepts a 'settings' object.
        # This settings object is an AttrDict shadowing our local variables so the
        # plugin can access the Django settings and modify them prior to startup.
        result = mod.setup(AttrDict({k: v for k, v in vars().items() if k.isupper()}))
    except ImportError:
        pass
