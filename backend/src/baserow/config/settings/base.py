import os
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'CHANGE_THIS_TO_SOMETHING_SECRET_IN_PRODUCTION'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['localhost', 'backend', 'sandbox']


INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'corsheaders',
    'mjml',
    'drf_spectacular',

    'baserow.core',
    'baserow.api',
    'baserow.contrib.database'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'baserow.config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'baserow.config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'baserow'),
        'USER': os.getenv('DATABASE_USER', 'baserow'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'baserow'),
        'HOST': os.getenv('DATABASE_HOST', 'db'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}

# Should contain the database connection name of the database where the user tables
# are stored. This can be different than the default database because there are not
# going to be any relations between the application schema and the user schema.
USER_TABLE_DATABASE = 'default'

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_SCHEMA_CLASS': 'baserow.api.openapi.AutoSchema'
}

CORS_ORIGIN_ALLOW_ALL = True

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=60 * 60),
    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'baserow.api.user.jwt.'
                                    'jwt_response_payload_handler'
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Baserow API spec',
    'DESCRIPTION': '',
    'CONTACT': {
        'url': 'https://baserow.io/contact'
    },
    'LICENSE': {
        'name': 'MIT',
        'url': 'https://gitlab.com/bramw/baserow/-/blob/master/LICENSE'
    },
    'VERSION': '0.2.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {'name': 'User'},
        {'name': 'Groups'},
        {'name': 'Applications'},
        {'name': 'Database tables'},
        {'name': 'Database table fields'},
        {'name': 'Database table views'},
        {'name': 'Database table grid view'},
        {'name': 'Database table rows'}
    ],
}

DATABASE_ROUTERS = ('baserow.contrib.database.database_routers.TablesDatabaseRouter',)

MJML_BACKEND_MODE = 'tcpserver'
MJML_TCPSERVERS = [
    (os.getenv('MJML_SERVER_HOST', 'mjml'), os.getenv('MJML_SERVER_PORT', 28101)),
]

PUBLIC_BACKEND_DOMAIN = os.getenv('PUBLIC_BACKEND_DOMAIN', 'localhost:8000')
PUBLIC_BACKEND_URL = os.getenv('PUBLIC_BACKEND_URL', 'http://localhost:8000')
PUBLIC_WEB_FRONTEND_DOMAIN = os.getenv('PUBLIC_WEB_FRONTEND_DOMAIN', 'localhost:3000')
PUBLIC_WEB_FRONTEND_URL = os.getenv('PUBLIC_WEB_FRONTEND_URL', 'http://localhost:3000')

FROM_EMAIL = os.getenv('FROM_EMAIL', 'no-reply@localhost')

RESET_PASSWORD_TOKEN_MAX_AGE = 60 * 60 * 48  # 48 hours
