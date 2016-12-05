#!/usr/bin/env python
"""
   tests.settings
   ==============

   Django settings for running tests

"""
import os

from django.conf.global_settings import *

# Some Basic Variables
# ============================================================================
PROJECT_ROOT = os.path.dirname(os.path.realpath(os.path.dirname(__file__)))


DEBUG = True
TEMPLATE_DEBUG = DEBUG

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-GB'
SITE_ID = 1
USE_L10N = True
USE_TZ = True

SECRET_KEY = 'local'

ROOT_URLCONF = 'tests.urls'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#AUTH_USER_MODEL = 'tests.AccountsUser'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

STATIC_URL = '/static'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages'
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

DJANGO_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
)

THIRD_PATH_APPS = (
    'rest_framework',
    'rest_framework.authtoken',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    #'allauth.socialaccount.providers.google',
)

LOCAL_APPS = (
    'django_accounts',
    'tests',
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PATH_APPS + LOCAL_APPS

# -------------------------------------------------------------------------- #
# django_accounts
# -------------------------------------------------------------------------- #
# Actually from django.contrib.auth  (AUTHENTICATION)
# LOGIN_URL = '/accounts/auth/login/'
# LOGIN_REDIRECT_URL = '/accounts/auth/login/'  # (global_settings.py)  '/users/profile/' - - default
LOGIN_REDIRECT_URL = '/docs/'
# One-week activation window; you may, of course, use a different value.
ACCOUNT_ACTIVATION_DAYS = 7

#REGISTRATION_OPEN = True


# http://django-allauth.readthedocs.org/en/latest/configuration.html
# Note if you change e.g. ACCOUNT_UNIQUE_EMAIL you may need to delete db before changes work

# Changing these could cause tests to fail
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True
# Note if set to true - tests will fail as we need to recreate db every test
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_ADAPTER = "django_accounts.adapter.DefaultAccountAdapter"

AUTH_USER_MODEL = 'django_accounts.AccountsUser'
REGISTRATION_OPEN = True


AUTHENTICATION_BACKENDS = (

    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

# -------------------------------------------------------------------------- #
# Templating
# -------------------------------------------------------------------------- #
# If you are running Django 1.8+, specify the context processors
# as follows:
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Already defined Django-related contexts here
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.request',
                # `allauth` needs this from django
                'django.template.context_processors.request',

            ],
            'debug': True,
        },
    },
]


PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(created)f %(filename)s %(funcName)s %(levelname)s %(module)s %(pathname)s %(process)d %(processName)s  %(lineno)s %(levelno)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
         'require_debug_false': {
             '()': 'django.utils.log.RequireDebugFalse',
         }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 30,
            'filename': 'app.log',
            'formatter': 'verbose',
        },
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    # This is the logger you use e.g. logging.getLogger(django)
    'loggers': {
        'test_logger': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}
