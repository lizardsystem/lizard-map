from django.db import models


class Workspace(models.Model):
    """Collection for managing what's visible on a map."""

    def __unicode__(self):
        return u'%s' % self.id


class WorkspaceItem(models.Model):
    """Can show things on a map based on configuration in a url."""
    workspace = models.ForeignKey(Workspace,
                                  related_name='workspace_items')
    url = models.URLField(verify_exists=False)

    def __unicode__(self):
        return u'%s' % self.url
