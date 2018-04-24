import logging

from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_delete
from django.db.models.signals import post_save

logger = logging.getLogger(__name__)


class BackgroundMap(models.Model):
    """
    Defines background maps.
    """
    LAYER_TYPE_GOOGLE = 1
    LAYER_TYPE_OSM = 2
    LAYER_TYPE_WMS = 3
    LAYER_TYPE_TMS = 4

    LAYER_TYPE_CHOICES = (
        (LAYER_TYPE_GOOGLE, 'GOOGLE'),
        (LAYER_TYPE_OSM, 'OSM'),
        (LAYER_TYPE_WMS, 'WMS'),
        (LAYER_TYPE_TMS, 'TMS'),
        )

    GOOGLE_TYPE_DEFAULT = 1
    GOOGLE_TYPE_PHYSICAL = 2
    GOOGLE_TYPE_HYBRID = 3
    GOOGLE_TYPE_SATELLITE = 4

    GOOGLE_TYPE_CHOICES = (
        (GOOGLE_TYPE_DEFAULT, 'google default'),
        (GOOGLE_TYPE_PHYSICAL, 'google physical'),
        (GOOGLE_TYPE_HYBRID, 'google hybrid'),
        (GOOGLE_TYPE_SATELLITE, 'google satellite'),
        )

    name = models.CharField(max_length=20)
    index = models.IntegerField(default=100)
    default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    is_base_layer = models.BooleanField(default=True)
    is_single_tile = models.BooleanField(default=False)

    layer_type = models.IntegerField(choices=LAYER_TYPE_CHOICES)
    google_type = models.IntegerField(
        choices=GOOGLE_TYPE_CHOICES,
        null=True, blank=True,
        help_text='Choose map type in case of GOOGLE maps.')
    layer_url = models.CharField(
        max_length=200,
        null=True, blank=True,
        help_text='Tile url for use with OSM or WMS or TMS',
        default='http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png')
    layer_names = models.TextField(
        null=True, blank=True,
        help_text='Fill in layer names in case of WMS or TMS')

    class Meta:
        ordering = ('index', )

    def __unicode__(self):
        return '%s' % self.name


class Setting(models.Model):
    """
    Global settings.

    Available keys with default values:
    projection 'EPSG:900913'
    display_projection 'EPSG:4326'
    googlemaps_api_key
    """
    CACHE_KEY = 'lizard-map.Setting'

    key = models.CharField(max_length=40, unique=True)
    value = models.CharField(max_length=200)

    def __unicode__(self):
        return '%s = %s' % (self.key, self.value)

    @classmethod
    def get(cls, key, default=None):
        """
        Return value from given key.

        If the key does not exist, return None. Caches the whole
        Setting table.
        """

        # Caching.
        settings = cache.get(cls.CACHE_KEY)  # Dict
        if settings is None:
            settings = {}
            for setting in cls.objects.all():
                settings[setting.key] = setting.value
            cache.set(cls.CACHE_KEY, settings)

        # Fallback for default.
        if key not in settings:
            if default is not None:
                # Only warn if None is not a fine value: otherwise we'd warn
                # about a setting that doesn't *need* to be set.
                logger.warn('Setting "%s" does not exist, taking default '
                            'value "%s"' % (key, default))
            return default

        # Return desired result.
        return settings[key]

    @classmethod
    def get_dict(cls, key, default=None):
        """
        Return {key: value} for given key
        """
        return {key: cls.get(key, default)}

    @classmethod
    def extent(cls, key, fallback):
        """ Setting in "xx0,yy0,xx1,yy1" format.

        TODO: test"""
        extent_names = ['left', 'bottom', 'right', 'top']
        extent_list = cls.get(
            key, fallback).split(',')
        extent = dict(
            [(extent_names[i], s.strip())
             for i, s in enumerate(extent_list)])
        return extent


# For Django 1.3:
# @receiver(post_save, sender=Setting)
# @receiver(post_delete, sender=Setting)
def setting_post_save_delete(sender, **kwargs):
    """
    Invalidates cache after saving or deleting a setting.
    """
    logger.debug('Changed setting. Invalidating cache for %s...' %
                 sender.CACHE_KEY)
    cache.delete(sender.CACHE_KEY)


post_save.connect(setting_post_save_delete, sender=Setting)
post_delete.connect(setting_post_save_delete, sender=Setting)
