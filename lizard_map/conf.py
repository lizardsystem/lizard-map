# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

"""Use AppConf to store sensible defaults for settings. This also documents the
settings that lizard_map defines. Each setting name automatically has
"LIZARD_MAP_" prepended to it.

By puttng the AppConf in this module and importing the Django settings
here, it is possible to import Django's settings with `from
lizard_damage.conf import settings` and be certain that the AppConf
stuff has also been loaded."""

# Use LANGUAGE_CODE = 'nl', 'en', etc. in Setting model
# to setup language per site

# Python 3 is coming
from __future__ import unicode_literals

from django.conf import settings
settings  # Pyflakes...

from appconf import AppConf


class MyAppConf(AppConf):
    # Settings used by lizard-map
    MAX_LOCATIONS = 50  # Not set in Lizard5-site's settings
    GOOGLE_TRACKING_CODE = None  # Not set in Lizard5-site's settings

    # Map settings (without "MAP_" because then it would be "LIZARD_MAP_MAP_")
    SHOW_MULTISELECT = False  # Value taken from lizard5-site's base.py
    SHOW_DATERANGE = True  # Not set in Lizard5-site's settings
    SHOW_DEFAULT_ZOOM = True  # Not set in Lizard5-site's settings
    SHOW_BASE_LAYERS_MENU = True  # Not set in Lizard5-site's settings
    SHOW_LAYERS_MENU = True  # Not set in Lizard5-site's settings

    SHOW_COLLAGE = True  # Value taken from lizard5-site's base.py

    # Defaults for the Setting model, DEFAULT_X_SETTING for Setting x
    DEFAULT_PROJECTION_SETTING = 'EPSG:3857'

    DEFAULT_DEFAULT_WORKSPACE_USER_SETTING = None
    DEFAULT_DEFAULT_WORKSPACE_ANONYMOUS_USER_SETTING = None

    DEFAULT_JAVASCRIPT_HOVER_HANDLER_SETTING = None

    DEFAULT_BOOTSTRAP_TOUR_SETTING = False

    DEFAULT_POPUP_MAX_TABS_SETTING = None

    DEFAULT_BOOTSTRAP_TOUR_SETTING = ''  # Set to 'nl' or whatever to turn on

    DEFAULT_START_EXTENT_SETTING = '-14675, 6668977, 1254790, 6964942'
    DEFAULT_MAX_EXTENT_SETTING = (
        '-20037508.34, -20037508.34, 20037508.34, 20037508.34')

    DEFAULT_DEFAULT_RANGE_TYPE_SETTING = 'week_plus_one'
    DEFAULT_DISCLAIMER_TEXT_SETTING = ''
    DEFAULT_ANON_CAN_STORE_COLLAGE_SETTING = False

    DEFAULT_LANGUAGE_CODE_SETTING = 'nl'
    DEFAULT_SHOW_LANGUAGE_PICKER_SETTING = False
