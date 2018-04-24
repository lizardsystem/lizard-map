try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import datetime
import logging
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
from lizard_ui.layout import Action
from lizard_ui.views import UiView

from lizard_map.coordinates import DEFAULT_OSM_LAYER_URL
from lizard_map.models import BackgroundMap
from lizard_map.models import Setting


MAP_LOCATION = 'map_location'
MAP_BASE_LAYER = 'map_base_layer'  # The selected base layer

DEFAULT_START_EXTENT = '-14675, 6668977, 1254790, 6964942'
DEFAULT_PROJECTION = 'EPSG:900913'


logger = logging.getLogger(__name__)


class MapMixin(object):
    """All map stuff
    """
    # def maps(self):
    #     # Add map variables.
    #     self.map_variables = map_variables(self.request)
    #     return ""

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

    def googlemaps_api_key(self):
        return Setting.get('projection', '')  # Must be defined

    def base_layer_name(self):
        if MAP_BASE_LAYER in self.request.session:
            return self.request.session[MAP_BASE_LAYER]
        return ""

    @property
    def backgrounds(self):
        if not hasattr(self, '_backgrounds'):
            self._backgrounds = BackgroundMap.objects.filter(active=True)
        return self._backgrounds

    def has_google(self):
        # For the client side to determine is there is a google map.
        if self.backgrounds.filter(
            layer_type=BackgroundMap.LAYER_TYPE_GOOGLE).count() > 0:
            return True
        return False

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


class AppView(MapMixin, UiView):
    """Main map view (using twitter bootstrap)."""

    show_secondary_sidebar_icon = 'icon-list'
    map_show_default_zoom = getattr(settings, 'MAP_SHOW_DEFAULT_ZOOM', True)
    map_show_base_layers_menu = getattr(settings,
                                        'MAP_SHOW_BASE_LAYERS_MENU', True)
    map_show_layers_menu = getattr(settings, 'MAP_SHOW_LAYERS_MENU', True)

    @property
    def show_secondary_sidebar_title(self):
        return _('Layers')

    @property
    def show_rightbar_title(self):
        return _('Legend')

    @property
    def legends(self):
        """Return legends for the rightbar."""
        return []  # legends are determined by the blockbox view

    @property
    def _bak_content_actions(self):
        """Add default-location-zoom."""
        actions = super(AppView, self).content_actions
        if self.map_show_default_zoom and False:
            zoom_to_default = Action(
                name='',
                description=_('Zoom to default location'),
                url=reverse('lizard_map.map_location_load_default'),
                icon='icon-screenshot',
                klass='map-load-default-location')
            actions.insert(0, zoom_to_default)
        if self.map_show_base_layers_menu and False:
            show_layers = Action(
                name='',
                element_id='base-layers',
                description=_('Show base layers'),
                url="#",
                icon='icon-globe',
                klass='dropdown-toggle')
            actions.insert(0, show_layers)
        if self.map_show_layers_menu and False:
            show_layers = Action(
                name='',
                element_id='layers',
                description=_('Show map layers'),
                url="#",
                icon='icon-map-marker',
                klass='dropdown-toggle')
            actions.insert(0, show_layers)
        return actions


MapView = AppView  # BBB

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
