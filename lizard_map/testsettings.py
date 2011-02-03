DEBUG = True
TEMPLATE_DEBUG = True
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'test.db'
SITE_ID = 1
INSTALLED_APPS = [
    'lizard_map',
    'lizard_ui',
    'staticfiles',
    'compressor',
    'django_nose',
    'piston',
    'south',
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
TEMPLATE_CONTEXT_PROCESSORS = (
    # Default items.
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    # Needs to be added for django-staticfiles to allow you to use
    # {{ STATIC_URL }}myapp/my.css in your templates.
    'staticfiles.context_processors.static_url',
    )

# Sample MAP_SETTINGS.

# MAP_SETTINGS = {
#     'base_layer_type': 'OSM',  # OSM or WMS
#     'projection': 'EPSG:900913',  # EPSG:900913, EPSG:28992
#     'display_projection': 'EPSG:4326',  # EPSG:900913/28992/4326
#     'startlocation_x': '550000',
#     'startlocation_y': '6850000',
#     'startlocation_zoom': '10',
#     'base_layer_osm': (
#         'http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png'),
#     }

# MAP_SETTINGS = {
#     'base_layer_type': 'WMS',  # OSM or WMS
#     'projection': 'EPSG:28992',  # EPSG:900913, EPSG:28992
#     'display_projection': 'EPSG:28992',  # EPSG:900913/28992/4326
#     'startlocation_x': '127000',
#     'startlocation_y': '473000',
#     'startlocation_zoom': '4',
#     'base_layer_wms': (
#         'http://nederlandwms.risicokaart.nl/wmsconnector/'
#         'com.esri.wms.Esrimap?'
#         'SERVICENAME=risicokaart_pub_nl_met_ondergrond&'),
#     'base_layer_wms_layers': (
#         'Outline_nederland,Dissolve_provincies,0,2,12,3,38,5,4,9,10'),
#     }

# Set the default period in days.
# DEFAULT_START_DAYS = -20
# DEFAULT_END_DAYS = 5

try:
    # Import local settings that aren't stored in svn.
    from lizard_map.local_testsettings import *
except ImportError:
    pass
