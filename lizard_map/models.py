from django.db import models
import simplejson


class Workspace(models.Model):
    """Collection for managing what's visible on a map."""

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

    def layer_method_arguments(self):
        """Return dict of parsed layer_method_json."""
        json = self.layer_method_json
        if not json:
            return {}
        return simplejson.loads(json)

    def has_layer(self):
        """Can I provide a WMS layer?"""
        return bool(self.layer_method)

    def layers(self):
        """Return layers for a mapnik map."""
        pass
