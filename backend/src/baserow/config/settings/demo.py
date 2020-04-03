import datetime
from .base import *  # noqa: F403, F401


JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=1),
    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'baserow.api.v0.user.jwt.'
                                    'jwt_response_payload_handler'
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'baserow',
        'USER': 'baserow',
        'PASSWORD': 'baserow',
        'HOST': 'db',
        'PORT': '5432',
    }
}
