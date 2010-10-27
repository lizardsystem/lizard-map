"""
Mapnik helper functions
"""
import mapnik
from django.conf import settings


def create_layer_from_query(query, projection, geometry_field=None, srid=None):
    """Return layer for the given table_view and projection."""

    layer = mapnik.Layer('Geometry from DB', projection)
    layer.srs = projection
    if settings.DATABASE_ENGINE == 'sqlite3':
        datasource = mapnik.SQLite
        options = {'file': settings.DATABASE_NAME}
    elif settings.DATABASE_ENGINE in (
        'postgresql_psycopg2', 'django.contrib.gis.db.backends.postgis'):
        datasource = mapnik.PostGIS
        options = {'host': settings.DATABASE_HOST,
                   'user': settings.DATABASE_USER,
                   'password': settings.DATABASE_PASSWORD,
                   'dbname': settings.DATABASE_NAME}
    else:
        raise RuntimeError(
            'Sorry, unconfigured db engine (%s) for mapnik integration.' % (
                settings.DATABASE_ENGINE))

    if geometry_field is not None:
        options['geometry_field'] = geometry_field
    if srid is not None:
        options['srid'] = srid
    layer.datasource = datasource(table=str(query), **options)
    return layer
