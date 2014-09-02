import os

from lizard_ui.settingshelper import setup_logging
from lizard_ui.settingshelper import STATICFILES_FINDERS

STATICFILES_FINDERS = STATICFILES_FINDERS

DEBUG = True
TEMPLATE_DEBUG = True
DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'test.db'},
    }
SITE_ID = 1
INSTALLED_APPS = [
    'lizard_map.testmodelapp',
    # ^^^ Only for testing! Django-nose problem.
    # See https://github.com/jbalogh/django-nose/issues/15
    'lizard_map',
    'lizard_ui',
    'lizard_security',
    'django.contrib.staticfiles',
    'compressor',
    'piston',
    'south',
    'django_nose',
    'debug_toolbar',
    'rest_framework',
    'django_extensions',
    'django.contrib.gis',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    ]
ROOT_URLCONF = 'lizard_map.urls'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Used for django-staticfiles
STATIC_URL = '/static_media/'
LANGUAGES = (
    ('nl', 'Nederlands'),
    ('en', 'English'),
)
LANGUAGE_CODE = 'nl'
MIDDLEWARE_CLASSES = (
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    #'lizard_map.profilemiddleware.ProfileMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    )
INTERNAL_IPS = (
    '127.0.0.1',
    )

SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))
MEDIA_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'media')
STATIC_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'static')
MEDIA_URL = '/media/'
STATIC_URL = '/static_media/'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

LOGGING = setup_logging(BUILDOUT_DIR)
USE_TZ = True

TIME_ZONE = "Europe/Amsterdam"

#SOUTH_TESTS_MIGRATE = False

LIZARD_MAP_STANDALONE = True

# Necessary because we store objects in the session
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

SECRET_KEY = 'Does not need to be secret in testsettings'

try:
    # Import local settings that aren't stored in svn.
    from lizard_map.local_testsettings import *
except ImportError:
    pass
