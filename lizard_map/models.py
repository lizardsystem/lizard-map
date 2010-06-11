import os

import pkg_resources
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models as gismodels
from django.db import models
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
import simplejson

from lizard_map.symbol_manager import SymbolManager

ICON_ORIGINALS = pkg_resources.resource_filename('lizard_map', 'icons')
ADAPTER_ENTRY_POINT = 'lizard_map.adapter_class'
SEARCH_ENTRY_POINT = 'lizard_map.search_method'
LOCATION_ENTRY_POINT = 'lizard_map.location_method'


def adapter_class_names():
    """Return allowed layer method names (from entrypoints)

    in tuple of 2-tuples
    """
    entrypoints = [(entrypoint.name, entrypoint.name) for entrypoint in
                   pkg_resources.iter_entry_points(group=ADAPTER_ENTRY_POINT)]
    return tuple(entrypoints)


class AdapterClassNotFoundError(Exception):
    pass


class Workspace(models.Model):
    """Collection for managing what's visible on a map."""

    class Meta:
        verbose_name = _("Workspace")
        verbose_name_plural = _("Workspaces")

    name = models.CharField(max_length=80,
                            blank=True,
                            default='workspace')
    # TODO below: default extend values for NL?
    extent_north = models.FloatField(blank=True, null=True)
    extent_east = models.FloatField(blank=True, null=True)
    extent_south = models.FloatField(blank=True, null=True)
    extent_west = models.FloatField(blank=True, null=True)
    owner = models.ForeignKey(User, blank=True, null=True)
    visible = models.BooleanField(default=False)

    def __unicode__(self):
        return u'(%s) %s' % (self.id, self.name)

    def get_absolute_url(self):
        return reverse('lizard_map_workspace', kwargs={'workspace_id': self.id})


class WorkspaceItem(models.Model):
    """Can show things on a map based on configuration in a url."""
    class Meta:
        ordering = ['index']
        verbose_name = _("Workspace item")
        verbose_name_plural = _("Workspace items")

    name = models.CharField(max_length=80,
                            blank=True)
    workspace = models.ForeignKey(Workspace,
                                  related_name='workspace_items')
    adapter_class = models.SlugField(blank=True,
                                     choices=adapter_class_names())
    # ^^^ string that identifies a setuptools entry point that points to a
    # specific method that returns (WMS) layers.  Often only one, but it *can*
    # be more than one layer.
    adapter_layer_json = models.TextField(blank=True)
    # ^^^ Contains json (TODO: add json verification)

    index = models.IntegerField(blank=True, default=0)
    visible = models.BooleanField(default=True)

    def __unicode__(self):
        return u'(%d) name=%s ws=%s %s' % (self.id, self.name, self.workspace, self.adapter_class)

    @property
    def adapter(self):
        #search for entrypoint and bind instance
        for entrypoint in pkg_resources.iter_entry_points(group=ADAPTER_ENTRY_POINT):
            if entrypoint.name == self.adapter_class:
                return entrypoint.load()(self, layer_arguments=self.adapter_layer_arguments)
        raise AdapterClassNotFoundError(
            u'Entry point for %r not found' % self.adapter_class)            

    @property
    def adapter_layer_arguments(self):
        """Return dict of parsed adapter_layer_json.

        Converts keys to str.
        """
        json = self.adapter_layer_json
        if not json:
            return {}
        result = {}
        for k, v in simplejson.loads(json).items():
            result[str(k)] = v
        return result

    def has_adapter(self):
        """Can I provide a adapter class for i.e. WMS layer?"""
        return bool(self.adapter_class)

    @property
    def symbol_url(self):
        """return url to symbol

        TODO: not implemented yet
        """

        sm = SymbolManager(ICON_ORIGINALS, os.path.join(settings.MEDIA_ROOT,
                                                        'generated_icons'))
        output_filename = sm.get_symbol_transformed('brug.png')

        return settings.MEDIA_URL + 'generated_icons/' + output_filename

class WorkspaceCollage(models.Model):
    """A collage contains selections/locations from a workspace"""
    name = models.CharField(max_length=80,
                            default='collage')
    workspace = models.ForeignKey(Workspace,
                                  related_name='collages')

    def __unicode__(self):
        return '%s %s' % (self.workspace, self.name)
    
    @property
    def locations(self):
        """locations of all snippets
        """
        return [snippet.location for snippet in self.snippets.all()]


class WorkspaceCollageSnippet(models.Model):
    """One snippet in a collage"""
    name = models.CharField(max_length=80,
                            default='snippet')
    shortname = models.CharField(max_length=80,
                                 default='snippet')
    workspace_collage = models.ForeignKey(WorkspaceCollage,
                                          related_name='snippets')
    workspace_item = models.ForeignKey(
        WorkspaceItem)
    identifier_json = models.TextField() #format depends on workspace_item layer_method

    def __unicode__(self):
        return '%s %s %s %s' % (
            self.name,
            self.workspace_collage,
            self.workspace_item,
            self.identifier)

    def save(self, *args, **kwargs):
        """check constraint that workspace_item is in workspace of owner collage"""
        if len(self.workspace_collage.workspace.workspace_items.filter(pk=self.workspace_item.pk)) == 0:
            raise "workspace_item of snippet not in workspace of collage"
        super(WorkspaceCollageSnippet, self).save(*args, **kwargs) # Call the "real" save() method.

    @property
    def identifier(self):
        """Return dict of parsed identifier_json.

        Converts keys to str.
        """
        json = self.identifier_json
        if not json:
            return {}
        result = {}
        for k, v in simplejson.loads(json).items():
            result[str(k)] = v
        return result

    @property
    def location(self):
        return self.workspace_item.adapter.location(**self.identifier)

    def image(self, start_end_dates):
        """return image from adapter,

        start_end_dates: 2-tuple of datetimes
        """
        return self.workspace_item.adapter.image([self.identifier, ], start_end_dates)


class AttachedPoint(models.Model):
    """Point geometry attached to another model instance."""

    class Meta:
        verbose_name = _("Attached point")
        verbose_name_plural = _("Attached points")

    # The geometry.
    point = gismodels.PointField()
    # Three fields needed to attach ourselves to another model instance.
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    objects = gismodels.GeoManager()

    def __unicode__(self):
        return '(%s, %s)' % (self.point.x, self.point.y)

