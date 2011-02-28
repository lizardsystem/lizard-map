from django import template
from django.conf import settings
import logging

from lizard_map.coordinates import MapSettings
from lizard_map.utility import analyze_http_user_agent
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
        map_settings = MapSettings().map_settings
        # Update map_settings with own coordinates and zoomlevel, if
        # applicable.

        if context.has_key('request'):
            session = context['request'].session
            if MAP_LOCATION in session:
                map_location = session[MAP_LOCATION]
                map_settings['startlocation_x'] = str(map_location['x'])
                map_settings['startlocation_y'] = str(map_location['y'])
                map_settings['startlocation_zoom'] = str(map_location['zoom'])
                logger.debug('Fetched map coordinates from session: '
                             '%s, %s, %s' % (
                        str(map_location['x']),
                        str(map_location['y']),
                        str(map_location['zoom'])))
        else:
            logger.warn(
                'Could not find request in context. Did you add '
                '"django.core.context_processors.request" '
                'to your TEMPLATE_CONTEXT_PROCESSORS?')

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
        result = 'other'  # default answer

        if context.has_key('request'):
            request_meta = context['request'].META
            if 'HTTP_USER_AGENT' in request_meta:
                http_user_agent = request_meta['HTTP_USER_AGENT']

                analyzed = analyze_http_user_agent(http_user_agent)
                if analyzed['device'] == 'iPad':
                    result = 'iPad'

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
