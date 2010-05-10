from django.core.urlresolvers import reverse
import simplejson

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.gis.db import models as gismodels
import pkg_resources


ENTRY_POINT = 'lizard_map.layer_method'


def layer_method_names():
    """Return allowed layer method names (from entrypoints)

    in tuple of 2-tuples
    """
    entrypoints = [(entrypoint.name, entrypoint.name) for entrypoint in
                   pkg_resources.iter_entry_points(group=ENTRY_POINT)]
    return tuple(entrypoints)


class LayerMethodNotFoundError(Exception):
    pass


class Workspace(models.Model):
    """Collection for managing what's visible on a map."""
    name = models.CharField(max_length=80,
                            blank=True,
                            default='workspace')
    # TODO below: default extend values for NL?
    extent_north = models.FloatField(blank=True, null=True)
    extent_east = models.FloatField(blank=True, null=True)
    extent_south = models.FloatField(blank=True, null=True)
    extent_west = models.FloatField(blank=True, null=True)
    owner = models.ForeignKey(User, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.id

    def get_absolute_url(self):
        return reverse('lizard_map_workspace', kwargs={'workspace_id': self.id})


class WorkspaceItem(models.Model):
    """Can show things on a map based on configuration in a url."""
    class Meta:
        ordering = ['index']

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

    def __unicode__(self):
        return u'(%d) name=%s ws=%s %s' % (self.id, self.name, self.workspace, self.layer_method)

    #def name(self):
    #    """Return friendly name"""
    #    return u''

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
        for entrypoint in pkg_resources.iter_entry_points(group=ENTRY_POINT):
            if entrypoint.name == self.layer_method:
                return entrypoint.load()
        raise LayerMethodNotFoundError(
            u'Entry point for %r not found' % self.layer_method)

    def layers(self):
        """Return layers and styles for a mapnik map."""
        return self._layer_method_instance(**self.layer_method_arguments)


class AttachedPoint(models.Model):
    """Point geometry attached to another model instance."""
    # The geometry.
    point = gismodels.PointField()
    # Three fields needed to attach ourselves to another model instance.
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    objects = gismodels.GeoManager()

    def __unicode__(self):
        return '(%s, %s)' % (self.point.x, self.point.y)
