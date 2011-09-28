"""Coordinates and projection constants and helpers"""
import logging
from pyproj import Proj
from pyproj import transform

from lizard_map.models import BackgroundMap


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
