"""Coordinates and projection constants and helpers"""
import logging
from pyproj import Proj
from pyproj import transform

from lizard_map.models import BackgroundMap
from lizard_map.models import Setting


logger = logging.getLogger(__name__)

# Proj4 projection strings.  Note: no commas between the concatenated
# strings!

# Rijksdriehoeks stelsel.
RD = ("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 "
      "+k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel "
      "+towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 "
      "+units=m +no_defs")
GOOGLE = ('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 '
          '+lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m '
          '+nadgrids=@null +no_defs +over')
WGS84 = ('+proj=latlong +datum=WGS84')

# Default map settings. Take this when no MAP_SETTINGS in django settings.
DEFAULT_OSM_LAYER_URL = 'http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png'
DEFAULT_MAP_SETTINGS = {
    'start_extent': '-14675, 6668977, 1254790, 6964942',
    'max_extent': '-20037508.34, -20037508.34, 20037508.34, 20037508.34',
    'projection': 'EPSG:900913',
    'display_projection': 'EPSG:4326',
    'googlemaps_api_key': '',  # Must be defined.
    'background_maps': [BackgroundMap(
            name='Default map',
            default=True,
            active=True,
            layer_type=BackgroundMap.LAYER_TYPE_OSM,
            layer_url=DEFAULT_OSM_LAYER_URL)],  # OSM
    }


rd_projection = Proj(RD)
google_projection = Proj(GOOGLE)
wgs84_projection = Proj(WGS84)

srs_to_mapnik_projection = {
    'EPSG:28992': RD,
    'EPSG:900913': GOOGLE,
    'EPSG:4326': WGS84,
    }


def google_to_rd(x, y):
    """Return RD coordinates from GOOGLE coordinates."""
    return transform(google_projection, rd_projection, x, y)


def rd_to_google(x, y):
    """Return GOOGLE coordinates from RD coordinates."""
    return transform(rd_projection, google_projection, x, y)


def wgs84_to_google(x, y):
    """Return GOOGLE coordinates from WGS84 coordinates."""
    return transform(wgs84_projection, google_projection, x, y)


def google_to_wgs84(x, y):
    """Return WGS84 coordinates from GOOGLE coordinates."""
    return transform(google_projection, wgs84_projection, x, y)


def rd_to_wgs84(x, y):
    """Return GOOGLE coordinates from RD coordinates."""
    return transform(rd_projection, wgs84_projection, x, y)


def wgs84_to_rd(x, y):
    """Return GOOGLE coordinates from RD coordinates."""
    return transform(wgs84_projection, rd_projection, x, y)


def srs_to_google(srs, x, y):
    """Return GOOGLE coordinates from coordinates. Coordinates are in
    srs (string), i.e. EPSG:28992."""
    if srs == 'EPSG:28992':
        google_x, google_y = rd_to_google(x, y)
    else:
        google_x, google_y = x, y
    return google_x, google_y


def google_to_srs(x, y, srs):
    """Return coordinates in srs from GOOGLE coordinates.

    Coordinates are in srs (string), i.e. EPSG:28992."""
    if srs == 'EPSG:28992':
        srs_x, srs_y = google_to_rd(x, y)
    else:
        srs_x, srs_y = x, y
    return srs_x, srs_y


def detect_prj(prj):
    """
    Inputs a prj string, output is the Proj4 projection string. If the
    string somehow cannot be parsed, we assume it is RD.
    """
    if not prj:
        return RD
    if 'GCS_WGS_1984' in prj:
        return WGS84
    return RD


class MapSettings(object):
    """
    Read background map information.

    Uses models BackgroundMap and Setting.
    """

    def __init__(self, map_settings=None):

        def setting(key):
            return Setting.get_dict(key, DEFAULT_MAP_SETTINGS[key])

        def extent_setting(key):
            """ Convert "xx0,yy0,xx1,yy1" to dictionary with extent_names."""
            extent_names = ['left', 'bottom', 'right', 'top']
            extent_list = Setting.get(
                key, DEFAULT_MAP_SETTINGS[key]).split(',')
            extent = dict(
                [(extent_names[i], s.strip())
                 for i, s in enumerate(extent_list)])
            return {key: extent}

        self.global_settings = {}

        self.global_settings.update(extent_setting('start_extent'))
        self.global_settings.update(extent_setting('max_extent'))

        self.global_settings.update(setting('googlemaps_api_key'))
        self.global_settings.update(setting('projection'))
        self.global_settings.update(setting('display_projection'))

        self.background_maps = BackgroundMap.objects.filter(active=True)

        # For the client side to determine is there is a google map.
        if self.background_maps.filter(
            layer_type=BackgroundMap.LAYER_TYPE_GOOGLE).count() > 0:

            self.global_settings.update({'has_google': True})

        if not self.background_maps:
            logger.warn("No background maps are active. Taking default.")
            self.background_maps = DEFAULT_MAP_SETTINGS['background_maps']

        self.map_settings = dict(self.global_settings)
        self.map_settings.update({'background_maps': self.background_maps})

    def mapnik_projection(self):
        """Returns the mapnik projection.
        """
        return srs_to_mapnik_projection[self.map_settings['projection']]

    @property
    def srid(self):
        """
        Return srid.

        """
        try:
            if self.map_settings['projection'][:5] == 'EPSG:':
                return int(self.map_settings['projection'][5:])
        except ValueError:
            pass
        return 4326  # wgs84 is the default

    @property
    def srs(self):
        """
        Return srs / projection.
        """
        return self.map_settings['projection']

    def convert_google_extent_map_srs(self, east, north, west, south):
        """
        Convert extent in google coordinates to srs of map settings.
        """
        extent_converted = {}
        extent_converted['east'], extent_converted['north'] = google_to_srs(
            east, north, self.srs)
        extent_converted['west'], extent_converted['south'] = google_to_srs(
            west, south, self.srs)
        return extent_converted
