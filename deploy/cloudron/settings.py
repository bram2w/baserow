from baserow.config.settings.base import *
import os

MEDIA_ROOT = '/app/data/media'

MJML_BACKEND_MODE = 'cmd'
MJML_EXEC_CMD = 'mjml'

FROM_EMAIL = os.environ['CLOUDRON_MAIL_FROM']
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = False
EMAIL_HOST = os.environ["CLOUDRON_MAIL_SMTP_SERVER"]
EMAIL_PORT = os.environ["CLOUDRON_MAIL_SMTP_PORT"]
EMAIL_HOST_USER = os.environ["CLOUDRON_MAIL_SMTP_USERNAME"]
EMAIL_HOST_PASSWORD = os.environ["CLOUDRON_MAIL_SMTP_PASSWORD"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['CLOUDRON_POSTGRESQL_DATABASE'],
        'USER': os.environ['CLOUDRON_POSTGRESQL_USERNAME'],
        'PASSWORD': os.environ['CLOUDRON_POSTGRESQL_PASSWORD'],
        'HOST': os.environ['CLOUDRON_POSTGRESQL_HOST'],
        'PORT': os.environ['CLOUDRON_POSTGRESQL_PORT'],
    }
}
