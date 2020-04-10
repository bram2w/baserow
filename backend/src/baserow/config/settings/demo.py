from .base import *  # noqa: F403, F401


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
