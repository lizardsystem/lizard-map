import simplejson

import pkg_resources
from django.db import models
from django.contrib.auth.models import User

ENTRY_POINT = 'lizard_map.layer_method'


class LayerMethodNotFoundError(Exception):
    pass


class Workspace(models.Model):
    """Collection for managing what's visible on a map."""
    name = models.CharField(max_length=80,
                            blank=True)
    extent_north = models.FloatField(blank=True, null=True)  # Default value for NL?
    extent_east = models.FloatField(blank=True, null=True)
    extent_south = models.FloatField(blank=True, null=True)
    extent_west = models.FloatField(blank=True, null=True)
    owner = models.ForeignKey(User, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.id


class WorkspaceItem(models.Model):
    """Can show things on a map based on configuration in a url."""
    workspace = models.ForeignKey(Workspace,
                                  related_name='workspace_items')
    url = models.URLField(verify_exists=False)
    layer_method = models.SlugField(blank=True,
                                    choices=(('a', 'Aaaa'),
                                             ('b', 'Bbbb')))
    # ^^^ string that identifies a setuptools entry point that points to a
    # specific method that returns (WMS) layers.  Often only one, but it *can*
    # be more than one layer.
    layer_method_json = models.TextField(blank=True)
    # ^^^ Contains json (TODO: add json verification)

    def __unicode__(self):
        return u'%s' % self.url

    def name(self):
        """Return friendly name"""
        return u''

    @property
    def layer_method_arguments(self):
        """Return dict of parsed layer_method_json."""
        json = self.layer_method_json
        if not json:
            return {}
        return simplejson.loads(json)

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
