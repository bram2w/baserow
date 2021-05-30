from baserow.config.settings.base import *
import os
import dj_database_url

MEDIA_ROOT = '/baserow/media'

MJML_BACKEND_MODE = 'cmd'
MJML_EXEC_CMD = 'mjml'

FROM_EMAIL = 'TODO@baserow.io'
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = False
EMAIL_HOST = os.environ["MAILGUN_SMTP_SERVER"]
EMAIL_PORT = os.environ["MAILGUN_SMTP_PORT"]
EMAIL_HOST_USER = os.environ["MAILGUN_SMTP_LOGIN"]
EMAIL_HOST_PASSWORD = os.environ["MAILGUN_SMTP_PASSWORD"]

DATABASES = {
    'default': dj_database_url.parse(os.environ['DATABASE_URL'], conn_max_age=600)
}
