import logging
import os

import pkg_resources
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
import simplejson

from lizard_map.symbol_manager import SymbolManager

ICON_ORIGINALS = pkg_resources.resource_filename('lizard_map', 'icons')
ADAPTER_ENTRY_POINT = 'lizard_map.adapter_class'
SEARCH_ENTRY_POINT = 'lizard_map.search_method'
LOCATION_ENTRY_POINT = 'lizard_map.location_method'

logger = logging.getLogger('lizard_map.models')


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
        return reverse('lizard_map_workspace',
                       kwargs={'workspace_id': self.id})


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
    adapter_layer_json = models.TextField(blank=True)
    # ^^^ Contains json (TODO: add json verification)

    index = models.IntegerField(blank=True, default=0)
    visible = models.BooleanField(default=True)

    def __unicode__(self):
        return u'(%d) name=%s ws=%s %s' % (self.id, self.name, self.workspace,
                                           self.adapter_class)

    @property
    def adapter(self):
        """Return adapter instance for entrypoint"""
        for entrypoint in pkg_resources.iter_entry_points(
            group=ADAPTER_ENTRY_POINT):
            if entrypoint.name == self.adapter_class:
                try:
                    real_adapter = entrypoint.load()
                except ImportError, e:
                    logger.critical("Invalid entry point: %s", e)
                    raise
                return real_adapter(
                    self,
                    layer_arguments=self.adapter_layer_arguments)
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

        sm = SymbolManager(ICON_ORIGINALS, os.path.join(
                settings.MEDIA_ROOT,
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

    @property
    def workspace_items(self):
        return WorkspaceItem.objects.filter(
            workspacecollagesnippet__in=self.snippets.all()).distinct()


class WorkspaceCollageSnippet(models.Model):
    """One snippet in a collage"""
    name = models.CharField(max_length=80,
                            default='snippet')
    shortname = models.CharField(max_length=80,
                                 default='snippet',
                                 blank=True,
                                 null=True)
    workspace_collage = models.ForeignKey(WorkspaceCollage,
                                          related_name='snippets')
    workspace_item = models.ForeignKey(
        WorkspaceItem)
    identifier_json = models.TextField()
    # ^^^ Format depends on workspace_item layer_method

    def __unicode__(self):
        return u'%s' % self.name

    def save(self, *args, **kwargs):
        """Save model and run an extra check.

        Check the constraint that workspace_item is in workspace of owner
        collage.

        """
        if len(self.workspace_collage.workspace.workspace_items.filter(
                pk=self.workspace_item.pk)) == 0:
            raise "workspace_item of snippet not in workspace of collage"
        # Call the "real" save() method.
        super(WorkspaceCollageSnippet, self).save(*args, **kwargs)

    @property
    def identifier(self):
        """Return dict of parsed identifier_json.

        Converts keys to str.
        TODO: .replace('%22', '"') in a better way

        """
        json = self.identifier_json.replace('%22', '"')
        if not json:
            return {}
        result = {}
        for k, v in simplejson.loads(json).items():
            result[str(k)] = v
        return result

    @property
    def location(self):
        return self.workspace_item.adapter.location(**self.identifier)

    def image(self, start_end_dates, width=None, height=None):
        """Return image from adapter.

        start_end_dates: 2-tuple of datetimes

        """
        return self.workspace_item.adapter.image([self.identifier],
                                                 start_end_dates,
                                                 width=width, height=height)
