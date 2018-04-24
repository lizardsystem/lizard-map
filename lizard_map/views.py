try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import logging

from django.http import HttpResponse
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
from lizard_ui.views import UiView

from lizard_map.models import BackgroundMap
from lizard_map.models import Setting


DEFAULT_OSM_LAYER_URL = 'http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png'
MAP_LOCATION = 'map_location'
MAP_BASE_LAYER = 'map_base_layer'  # The selected base layer

DEFAULT_START_EXTENT = '-14675, 6668977, 1254790, 6964942'
DEFAULT_PROJECTION = 'EPSG:900913'


logger = logging.getLogger(__name__)


class MapView(UiView):
    """All map stuff
    """
    def max_extent(self):
        s = Setting.extent(
            'max_extent',
            '-20037508.34, -20037508.34, 20037508.34, 20037508.34')
        return s

    def start_extent(self):
        return self.request.session.get(
            MAP_LOCATION,
            Setting.extent(
                'start_extent',
                DEFAULT_START_EXTENT)  # Default
            )

    def projection(self):
        return Setting.get('projection', DEFAULT_PROJECTION)

    def display_projection(self):
        return Setting.get('projection', 'EPSG:4326')

    def base_layer_name(self):
        if MAP_BASE_LAYER in self.request.session:
            return self.request.session[MAP_BASE_LAYER]
        return ""

    @property
    def backgrounds(self):
        if not hasattr(self, '_backgrounds'):
            self._backgrounds = BackgroundMap.objects.filter(active=True)
        return self._backgrounds

    def background_maps(self):
        if self.backgrounds:
            return self.backgrounds
        logger.warn("No background maps are active. Taking default.")
        return [BackgroundMap(
                name='Default map',
                default=True,
                active=True,
                layer_type=BackgroundMap.LAYER_TYPE_OSM,
                layer_url=DEFAULT_OSM_LAYER_URL), ]

    @property
    def show_rightbar_title(self):
        return _('Legend')

    @property
    def legends(self):
        """Return legends for the rightbar."""
        return []  # legends are determined by the blockbox view


"""
Map locations are stored in the session with key MAP_SESSION. It
contains a dictionary with fields x, y and zoom.
"""

def map_location_save(request):
    """
    Save map layout in session.

    - extent as strings (POST top, left, right, bottom).
    - selected base layer name.


    """
    top = request.POST['top']
    left = request.POST['left']
    right = request.POST['right']
    bottom = request.POST['bottom']
    base_layer_name = request.POST['base_layer_name']
    request.session[MAP_LOCATION] = {
        'top': top,
        'left': left,
        'right': right,
        'bottom': bottom}
    request.session[MAP_BASE_LAYER] = base_layer_name
    return HttpResponse("")


def map_location_load_default(request):
    """
    Return start_extent
    """
    extent = Setting.extent(
        'start_extent',
        DEFAULT_START_EXTENT)

    map_location = {'extent': extent}

    request.session[MAP_BASE_LAYER] = ''  # Reset selected base layer.

    return HttpResponse(json.dumps(map_location))
