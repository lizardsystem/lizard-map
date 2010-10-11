from django import template
from django.conf import settings
import logging

register = template.Library()

logger = logging.getLogger(__name__)


class MapVariablesNode(template.Node):
    """
    This node adds lizard-map variables to the context; in the
    template those variables are finally inserted into javascript
    code.
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

        for setting, setting_value in map_settings.items():
            context[setting] = setting_value

        return ''


@register.tag
def map_variables(parser, token):
    """Display debug info on workspaces."""
    return MapVariablesNode()
