from baserow.config.settings.base import *
import os
import dj_database_url


INSTALLED_APPS = INSTALLED_APPS + ["storages"]

MEDIA_ROOT = "/baserow/media"

MJML_BACKEND_MODE = "cmd"
MJML_EXEC_CMD = "mjml"

CELERY_REDIS_MAX_CONNECTIONS = 5
BROKER_TRANSPORT_OPTIONS = {
    "max_connections": 5,
}
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "max_connections": 5,
}

FROM_EMAIL = f"no-reply@{PRIVATE_BACKEND_HOSTNAME}"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = False
EMAIL_HOST = os.environ["MAILGUN_SMTP_SERVER"]
EMAIL_PORT = os.environ["MAILGUN_SMTP_PORT"]
EMAIL_HOST_USER = os.environ["MAILGUN_SMTP_LOGIN"]
EMAIL_HOST_PASSWORD = os.environ["MAILGUN_SMTP_PASSWORD"]

DATABASES = {
    "default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=600)
}

if os.getenv("AWS_ACCESS_KEY_ID", "") != "":
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
        "ContentDisposition": "attachment",
    }
    AWS_S3_FILE_OVERWRITE = True
    AWS_DEFAULT_ACL = "public-read"

if os.getenv("AWS_S3_REGION_NAME", "") != "":
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")

if os.getenv("AWS_S3_ENDPOINT_URL", "") != "":
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")

if os.getenv("AWS_S3_CUSTOM_DOMAIN", "") != "":
    AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN")
