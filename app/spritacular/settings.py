"""
Django settings for spritacular project.

Generated by 'django-admin startproject' using Django 4.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""


import os
import logging

from logging import handlers

from pathlib import Path
from decouple import config
from datetime import timedelta

import firebase_admin
from firebase_admin import credentials


from firebase_admin import initialize_app

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', False) == 'True'

ALLOWED_HOSTS = ['0.0.0.0', '127.0.0.1', 'localhost', 'api.spritacular.org', 'api.stage.spritacular.org',
                 '35.175.116.233', '3.235.53.246']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users.apps.UsersConfig',
    'observation.apps.ObservationConfig',
    'notification.apps.NotificationConfig',
    'blog.apps.BlogConfig',
    'quiz.apps.QuizConfig',
    'storages',
    'django_celery_beat',

    # rest_framework
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'django_rest_passwordreset',
    'rest_framework_simplejwt.token_blacklist',

    # Firebase Cloud Messaging
    'fcm_django',

    # query debug
    'silk',

    # django cleanup for image and file fields
    'django_cleanup.apps.CleanupConfig',
]

AUTH_USER_MODEL = 'users.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'silk.middleware.SilkyMiddleware',
]

# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'users.authentication.ExpiringTokenAuthentication'  # custom authentication class
#     ]
# }

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://34.205.152.253:3000",
    "https://dev.spritacular.org",
    "https://spritacular.org"
]

CSRF_TRUSTED_ORIGINS = ['https://api.spritacular.org', 'http://127.0.0.1:8000', 'https://api.stage.spritacular.org']

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'spritacular.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
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

WSGI_APPLICATION = 'spritacular.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT')
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
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

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=int(config('ACCESS_TOKEN_LIFETIME'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(config('REFRESH_TOKEN_LIFETIME'))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': config('ALGORITHM'),
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,

    'AUTH_HEADER_TYPES': (config('AUTH_HEADER_TYPES'),),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME = float(config('DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME'))

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Config
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = config('EMAIL_PORT')
EMAIL_USE_TLS = config('EMAIL_USE_TLS')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# AWS S3
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
DEFAULT_FILE_STORAGE = config('DEFAULT_FILE_STORAGE')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME')
AWS_DEFAULT_ACL = config('AWS_DEFAULT_ACL')
AWS_S3_FILE_OVERWRITE = False  # for handling files with duplicate names
AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN')

FRONTEND_URL = config('FRONTEND_URL')

# settings related to redis
# CACHE_TTL = 60 * 60  # Cache time to live is 60 minutes.
#
# CACHES = {
#     "default": {
#         "BACKEND": config('CACHE_BACKEND'),
#         "LOCATION": config('CACHE_LOCATION'),
#         "OPTIONS": {
#             "CLIENT_CLASS": config('CLIENT_CLASS')
#         },
#         "KEY_PREFIX": config('KEY_PREFIX')
#     }
# }


# CELERY STUFF
CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


FCM_DJANGO_SETTINGS = {
    "FCM_SERVER_KEY": config('FCM_SERVER_KEY'),
    "ONE_DEVICE_PER_USER": True,
    "DELETE_INACTIVE_DEVICES": True,
    "UPDATE_ON_DUPLICATE_REG_ID": True
}


# plug in local settings if any
PROJECT_APP = os.path.basename(BASE_DIR)
f = os.path.join(PROJECT_APP, 'settings.py')
if os.path.exists(f):
    import sys
    import importlib
    module_name = f'{PROJECT_APP}.settings'
    module = importlib.util.module_from_spec(module_name)
    module.__file__ = f
    sys.modules[module_name] = module
    exec(open(f, 'rb').read())

cred = credentials.Certificate(os.path.join(BASE_DIR, config('PATH_TO_FCM_CREDS')))
firebase_admin.initialize_app(cred)

print("+++ SETTINGS-August-22 +++")


# Sentry configuration
if config('USE_SENTRY') == 'True':
    sentry_sdk.init(
        dsn=config('DSN'),
        integrations=[DjangoIntegration()],

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )


# Logging configuration
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'detail': {'format': '%(asctime)s : %(levelname)s : %(message)s'}
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'detail'
#         },
#     },
#     'root': {
#         'handlers': ['console'],
#         'level': 'INFO',
#     },
# }

# create log directory
if not os.path.exists(os.path.join(BASE_DIR, 'app_logs')):
    os.makedirs(os.path.join(BASE_DIR, 'app_logs'))

log = logging.getLogger('')
log.setLevel(logging.INFO)

boto_logger = logging.getLogger('botocore')
boto_logger.setLevel(logging.DEBUG)

format = logging.Formatter(
    "%(levelname)s\n" "%(asctime)s\n" "%(pathname)s\n" "%(message)s\n" "===============================")

fh = handlers.TimedRotatingFileHandler(os.path.join(BASE_DIR, 'app_logs/debug.log'), backupCount=15, when='D')
fh.setFormatter(format)
log.addHandler(fh)

