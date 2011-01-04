from django import template
from django.conf import settings
import logging

from lizard_map.views import MAP_LOCATION

register = template.Library()

logger = logging.getLogger(__name__)


class MapVariablesNode(template.Node):
    """
    This node adds lizard-map variables to the context; in the
    template those variables are finally inserted into javascript
    code.

    By default it takes coordinates from the django settings. If a
    user has custom coordinates in his session, it will take those
    coordinates and zoomlevel.

    Note: user coordinates require
    'django.core.context_processors.request' in your
    TEMPLATE_CONTEXT_PROCESSORS.

    """

    def render(self, context):
        try:
            map_settings = settings.MAP_SETTINGS
        except AttributeError:
            logger.warn(
                'Could not find MAP_SETTINGS in '
                'django settings, using default.')
            map_settings = {
                'base_layer_type': 'OSM',  # OSM or WMS
                'projection': 'EPSG:900913',  # EPSG:900913, EPSG:28992
                'display_projection': 'EPSG:4326',  # EPSG:900913/28992/4326
                'startlocation_x': '550000',
                'startlocation_y': '6850000',
                'startlocation_zoom': '10',
                'base_layer_osm': (
                    'http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png'),
                }
        # Update map_settings with own coordinates and zoomlevel, if applicable
        if context.has_key('request'):
            session = context['request'].session
            if MAP_LOCATION in session:
                map_location = session[MAP_LOCATION]
                map_settings['startlocation_x'] = str(map_location['x'])
                map_settings['startlocation_y'] = str(map_location['y'])
                map_settings['startlocation_zoom'] = str(map_location['zoom'])

        for setting, setting_value in map_settings.items():
            context[setting] = setting_value

        return ''


class DetectBrowserNode(template.Node):
    """
    This node detects the browser and adds a variable detected_browser
    to the context. Possible values:

    'iPad'
    'other'
    """

    def render(self, context):
        request_meta = context['request'].META
        http_user_agent = request_meta['HTTP_USER_AGENT']

        print 'http_user_agent: %s' % http_user_agent

        result = 'other'  # default answer
        if 'iPad' in http_user_agent:
            result = 'iPad'
            print 'iPad!'

        context['detected_browser'] = result

        return ''


@register.tag
def map_variables(parser, token):
    """Display debug info on workspaces."""
    return MapVariablesNode()


@register.tag
def detect_browser(parser, token):
    """Detects browser and sets variable "detected_browser".

    See DetectBrowserNode.
    """
    return DetectBrowserNode()
