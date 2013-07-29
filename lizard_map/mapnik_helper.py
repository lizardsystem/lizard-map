"""
Mapnik helper functions
"""
import logging
import os

import mapnik
from django.conf import settings

from lizard_map.symbol_manager import SymbolManager

logger = logging.getLogger(__name__)


def database_settings(name="default", user_settings=None):
    """
    Fetch database settings for given database name. Can also handle
    pre django 1.2 style single database configuration (this case
    ignores name).

    Returns datasource and options dictionary with relevant info.

    If old AND new config styles are used, the new config style
    overrules.
    """
    if user_settings is None:
        user_settings = settings

    if getattr(user_settings, "DATABASES", None):
        # Multiple databases configuration.
        if name in user_settings.DATABASES:
            database_settings = user_settings.DATABASES[name]
            if database_settings['ENGINE'] in (
                'postgresql_psycopg2',
                'django.contrib.gis.db.backends.postgis'):
                datasource = mapnik.PostGIS
                options = {
                    'host': database_settings["HOST"],
                    'user': database_settings["USER"],
                    'password': database_settings["PASSWORD"],
                    'dbname': database_settings["NAME"]}
            else:
                raise RuntimeError(
                    'Sorry, unconfigured db engine (%s, name=%s) for '
                    'mapnik integration.' % (
                        database_settings["ENGINE"], name))
        else:
            raise RuntimeError(
                'Sorry, db name (%s) not found in '
                'multiple db configuration.' % (
                    name))
    elif getattr(user_settings, "DATABASE_ENGINE", None):
        # Pre django 1.2 style single database configuration.
        if user_settings.DATABASE_ENGINE == 'sqlite3':
            datasource = mapnik.SQLite
            options = {'file': user_settings.DATABASE_NAME}
        elif user_settings.DATABASE_ENGINE in (
            'postgresql_psycopg2', 'django.contrib.gis.db.backends.postgis'):
            datasource = mapnik.PostGIS
            options = {'host': user_settings.DATABASE_HOST,
                       'user': user_settings.DATABASE_USER,
                       'password': user_settings.DATABASE_PASSWORD,
                       'dbname': user_settings.DATABASE_NAME}
        else:
            raise RuntimeError(
                'Sorry, unconfigured db engine (%s) for '
                'mapnik integration.' % (
                    user_settings.DATABASE_ENGINE))
    else:
        raise RuntimeError(
            'Sorry, unconfigured db (%s and %s) for mapnik integration.' % (
                user_settings.DATABASE_ENGINE, user_settings.DATABASES))
    return datasource, options


def create_layer_from_query(query, projection, geometry_field=None, srid=None,
                            user_settings=None):
    """Return layer for the given table_view and projection."""

    layer = mapnik.Layer('Geometry from DB', projection)
    layer.srs = projection
    if user_settings is None:
        user_settings = settings

    datasource, options = database_settings(user_settings=user_settings)
    if geometry_field is not None:
        options['geometry_field'] = geometry_field
    if srid is not None:
        options['srid'] = srid
    layer.datasource = datasource(table=str(query), **options)

    return layer


def symbol_filename(icon, mask, color):
    """
    Generates symbol and returns symbol filename. Uses SymbolManager
    to generate icons.

    TODO: Move ICON_ORIGINALS from lizard_map.models to here?

    Input:
    icon: icon filename, i.e. empty.png
    mask: mask filename,
    color: color tuple, i.e. (1.0, 1.0, 1.0, 1.0)
    """
    from lizard_map.models import ICON_ORIGINALS

    icon_style = {'icon': icon,
                  'mask': (mask, ),
                  'color': color.to_tuple()}
    symbol_manager = SymbolManager(
        ICON_ORIGINALS,
        os.path.join(settings.MEDIA_ROOT, 'generated_icons'))
    output_filename = symbol_manager.get_symbol_transformed(
        icon_style['icon'], **icon_style)
    return output_filename


def point_rule(icon, mask, color, mapnik_filter=None):
    """
    Makes mapnik point rule.
    """
    output_filename = symbol_filename(icon, mask, color)
    output_filename_abs = os.path.join(
        settings.MEDIA_ROOT, 'generated_icons', output_filename)

    point_looks = mapnik.PointSymbolizer()
    point_looks.filename = str(output_filename_abs)
    point_looks.allow_overlap = True
    layout_rule = mapnik.Rule()
    layout_rule.symbols.append(point_looks)
    if mapnik_filter:
        layout_rule.filter = mapnik.Filter(mapnik_filter)

    return layout_rule


def add_datasource_point(datasource, x, y, name, info, _id=0):
    """
    Use this function to compensate for Mapnik bug #402 where some
    points are lost.
    """
    # Use these coordinates to put points 'around' actual
    # coordinates, to compensate for bug #402 in mapnik.
    e = 0.000001
    around = [(0, 0), (e, 0), (-e, 0), (0, e), (0, -e)]
    for offset_x, offset_y in around:
        context = mapnik.Context()
        context.push(name)
        feature = mapnik.Feature(context, _id)
        feature[name] = info
        feature.add_geometries_from_wkt('POINT(%s %s)' % (x + offset_x,
                                                          y + offset_y))
        datasource.add_feature(feature)
