"""
Mapnik helper functions
"""
import logging

import mapnik
from django.conf import settings

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
                'Sorry, db name (%s) not found in multiple db configuration.' % (
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
                'Sorry, unconfigured db engine (%s) for mapnik integration.' % (
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
