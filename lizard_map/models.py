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
LAYER_ENTRY_POINT = 'lizard_map.layer_method'
SEARCH_ENTRY_POINT = 'lizard_map.search_method'


def layer_method_names():
    """Return allowed layer method names (from entrypoints)

    in tuple of 2-tuples
    """
    entrypoints = [(entrypoint.name, entrypoint.name) for entrypoint in
                   pkg_resources.iter_entry_points(group=LAYER_ENTRY_POINT)]
    return tuple(entrypoints)


class LayerMethodNotFoundError(Exception):
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
    layer_method = models.SlugField(blank=True,
                                    choices=layer_method_names())
    # ^^^ string that identifies a setuptools entry point that points to a
    # specific method that returns (WMS) layers.  Often only one, but it *can*
    # be more than one layer.
    layer_method_json = models.TextField(blank=True)
    # ^^^ Contains json (TODO: add json verification)

    index = models.IntegerField(blank=True, default=0)
    visible = models.BooleanField(default=True)

    def __unicode__(self):
        return u'(%d) name=%s ws=%s %s' % (self.id, self.name, self.workspace, self.layer_method)

    @property
    def layer_method_arguments(self):
        """Return dict of parsed layer_method_json.

        Converts keys to str.
        """
        json = self.layer_method_json
        if not json:
            return {}
        result = {}
        for k, v in simplejson.loads(json).items():
            result[str(k)] = v
        return result

    def has_layer(self):
        """Can I provide a WMS layer?"""
        return bool(self.layer_method)

    @property
    def _layer_method_instance(self):
        for entrypoint in pkg_resources.iter_entry_points(group=LAYER_ENTRY_POINT):
            if entrypoint.name == self.layer_method:
                return entrypoint.load()
        raise LayerMethodNotFoundError(
            u'Entry point for %r not found' % self.layer_method)

    @property
    def _search_method_instance(self):
        for entrypoint in pkg_resources.iter_entry_points(group=SEARCH_ENTRY_POINT):
            if entrypoint.name == self.layer_method:
                return entrypoint.load()
        return None

    def layers(self):
        """Return layers and styles for a mapnik map."""
        return self._layer_method_instance(**self.layer_method_arguments)

    def search(self, x, y, radius=None):
        """Return item(s) found at x, y."""
        search_method = self._search_method_instance
        if not search_method:
            return []
        return search_method(x, y, radius=radius, **self.layer_method_arguments)

    @property
    def symbol_url(self):
        """return url to symbol

        TODO: not implemented yet
        """

        sm = SymbolManager(ICON_ORIGINALS, os.path.join(settings.MEDIA_ROOT,
                                                        'generated_icons'))
        output_filename = sm.get_symbol_transformed('brug.png')

        return settings.MEDIA_URL + 'generated_icons/' + output_filename

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

# TODO: move the workspacemanager elsewhere as it is not a model.


class WorkspaceManager:

    def __init__(self, request):
        self.request = request
        self.workspaces = {}

    def save_workspaces(self):
        """save workspaces to session"""
        workspaces_id = {}
        for k, workspace_list in self.workspaces.items():
            workspaces_id[k] = [workspace.id for workspace in workspace_list]
        self.request.session['workspaces'] = workspaces_id

    def load_workspaces(self, workspaces_id=None):
        """load workspaces from session

        returns number of workspaces that could not be loaded"""
        errors = 0
        # TODO: fix up workspaces_id and workspace_ids as those terms are too
        # similar.  They will lead to coding errors.
        if workspaces_id is None:
            workspaces_id = self.request.session['workspaces']
        for k, workspace_ids in workspaces_id.items():
            self.workspaces[k] = []
            for workspace_id in workspace_ids:
                try:
                    new_workspace = Workspace.objects.get(pk=workspace_id)
                    self.workspaces[k].append(new_workspace)
                except Workspace.DoesNotExist:
                    errors += 1
        return errors

    def load_or_create(self):
        """load workspaces references by session['workspaces'] or
        create new workspace

        workspaces are returned in a dictionary:
        {
        'default': [...default layers],
        'temp': workspace_temp,
        'user': [...user workspaces]
        }

        they are stored in the session as a dictionary of ids:
        {
        'default': [id1, id2, ...],
        'temp': [id, ],
        'user': [id3, id4, ...],
        }
        """

        self.workspaces = {}
        changes = False
        if self.request.session.has_key('workspaces'):
            changes = self.load_workspaces()

        #check if components exist, else create them
        if not 'default' in self.workspaces:
            try:
                self.workspaces['default'] = [Workspace.objects.get(name='achtergrond'), ]
            except Workspace.DoesNotExist:
                pass
            changes = True

        if not 'temp' in self.workspaces:
            workspace_temp = Workspace(name='temp')
            workspace_temp.save()
            self.workspaces['temp'] = [workspace_temp, ]
            changes = True
        else:
            #clear all items in temp workspace
            for workspace in self.workspaces['temp']:
                workspace.workspace_items.all().delete()

        if not 'user' in self.workspaces:
            workspace_user = Workspace()
            workspace_user.save()
            self.workspaces['user'] = [workspace_user, ]
            changes = True

        if changes:
            self.save_workspaces()
        return self.workspaces
