import os
import datetime
from urllib.parse import urlparse, urljoin

from corsheaders.defaults import default_headers

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_TO_SOMETHING_SECRET_IN_PRODUCTION")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["localhost"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "channels",
    "mjml",
    "drf_spectacular",
    "baserow.core",
    "baserow.api",
    "baserow.ws",
    "baserow.contrib.database",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
REDIS_URL = (
    f"{REDIS_PROTOCOL}://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
)

CELERY_BROKER_URL = REDIS_URL

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

# Should contain the database connection name of the database where the user tables
# are stored. This can be different than the default database because there are not
# going to be any relations between the application schema and the user schema.
USER_TABLE_DATABASE = "default"

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

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

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    "WebSocketId",
]


JWT_AUTH = {
    "JWT_EXPIRATION_DELTA": datetime.timedelta(seconds=60 * 60),
    "JWT_ALLOW_REFRESH": True,
    "JWT_REFRESH_EXPIRATION_DELTA": datetime.timedelta(days=7),
    "JWT_RESPONSE_PAYLOAD_HANDLER": "baserow.api.user.jwt."
    "jwt_response_payload_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Baserow API spec",
    "DESCRIPTION": "",
    "CONTACT": {"url": "https://baserow.io/contact"},
    "LICENSE": {
        "name": "MIT",
        "url": "https://gitlab.com/bramw/baserow/-/blob/master/LICENSE",
    },
    "VERSION": "1.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "Settings"},
        {"name": "User"},
        {"name": "User files"},
        {"name": "Groups"},
        {"name": "Group invitations"},
        {"name": "Templates"},
        {"name": "Applications"},
        {"name": "Database tables"},
        {"name": "Database table fields"},
        {"name": "Database table views"},
        {"name": "Database table view filters"},
        {"name": "Database table view sortings"},
        {"name": "Database table grid view"},
        {"name": "Database table rows"},
        {"name": "Database tokens"},
    ],
}

DATABASE_ROUTERS = ("baserow.contrib.database.database_routers.TablesDatabaseRouter",)

# The storage must always overwrite existing files.
DEFAULT_FILE_STORAGE = "baserow.core.storage.OverwriteFileSystemStorage"

MJML_BACKEND_MODE = "tcpserver"
MJML_TCPSERVERS = [
    (os.getenv("MJML_SERVER_HOST", "mjml"), int(os.getenv("MJML_SERVER_PORT", 28101))),
]

PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")
PUBLIC_WEB_FRONTEND_URL = os.getenv("PUBLIC_WEB_FRONTEND_URL", "http://localhost:3000")
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
ROW_PAGE_SIZE_LIMIT = 200  # Indicates how many rows can be requested at once.

# The amount of rows that can be imported when creating a table.
INITIAL_TABLE_DATA_LIMIT = None
if "INITIAL_TABLE_DATA_LIMIT" in os.environ:
    INITIAL_TABLE_DATA_LIMIT = int(os.getenv("INITIAL_TABLE_DATA_LIMIT"))

MEDIA_URL_PATH = "/media/"
MEDIA_URL = os.getenv("MEDIA_URL", urljoin(PUBLIC_BACKEND_URL, MEDIA_URL_PATH))
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/media")

# Indicates the directory where the user files and user thumbnails are stored.
USER_FILES_DIRECTORY = "user_files"
USER_THUMBNAILS_DIRECTORY = "thumbnails"
USER_FILE_SIZE_LIMIT = 1024 * 1024 * 20  # 20MB

if os.getenv("EMAIL_SMTP", ""):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_USE_TLS = bool(os.getenv("EMAIL_SMPT_USE_TLS", ""))
    EMAIL_HOST = os.getenv("EMAIL_SMTP_HOST", "localhost")
    EMAIL_PORT = os.getenv("EMAIL_SMTP_PORT", "25")
    EMAIL_HOST_USER = os.getenv("EMAIL_SMTP_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_SMTP_PASSWORD", "")


# Configurable thumbnails that are going to be generated when a user uploads an image
# file.
USER_THUMBNAILS = {"tiny": [None, 21], "small": [48, 48]}

# The directory that contains the all the templates in JSON format. When for example
# the `sync_templates` management command is called, then the templates in the
# database will be synced with these files.
APPLICATION_TEMPLATES_DIR = os.path.join(BASE_DIR, "../../../templates")
# The template that must be selected when the user first opens the templates select
# modal.
DEFAULT_APPLICATION_TEMPLATE = "project-management"
