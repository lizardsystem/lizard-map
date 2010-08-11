import itertools
import logging
import pkg_resources

from django.contrib.auth.models import User
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
import simplejson

from lizard_map.adapter import parse_identifier_json

# Do not change the following items!
GROUPING_HINT = 'grouping_hint'
USER_WORKSPACES = 'user'
DEFAULT_WORKSPACES = 'default'
TEMP_WORKSPACES = 'temp'

ICON_ORIGINALS = pkg_resources.resource_filename('lizard_map', 'icons')
ADAPTER_ENTRY_POINT = 'lizard_map.adapter_class'
SEARCH_ENTRY_POINT = 'lizard_map.search_method'
LOCATION_ENTRY_POINT = 'lizard_map.location_method'

ALL = 1
YEAR = 2
QUARTER = 3
MONTH = 4
WEEK = 5
DAY = 6

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
        return u'%s' % (self.name)

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


class WorkspaceCollage(models.Model):
    """A collage contains selections/locations from a workspace"""
    name = models.CharField(max_length=80,
                            default='collage')
    workspace = models.ForeignKey(Workspace,
                                  related_name='collages')

    def __unicode__(self):
        return '%s' % (self.name)

    @property
    def locations(self):
        """locations of all snippets
        """
        snippets_in_groups = [snippet_group.snippets.all()
                              for snippet_group in self.snippet_groups.all()]
        # Flatten snippets in groups:
        snippets = list(itertools.chain(*snippets_in_groups))
        return [snippet.location for snippet in snippets]

    @property
    def workspace_items(self):
        return WorkspaceItem.objects.filter(
            workspacecollagesnippet__in=self.snippets.all()).distinct()

    def get_or_create_snippet(self, workspace_item, identifier_json,
                              shortname, name):
        """
        Makes snippet in a snippet group. Finds or creates
        corresponding snippet group (see below)
        """
        found_snippet_group = None
        identifier = parse_identifier_json(identifier_json)
        snippet_groups = self.snippet_groups.all()

        # Try to find most appropriate snippet group:

        # (1) check for the 'group' property in snippet identifier: if
        # at least one snippet in a group has this property, then the
        # group matches. Solves problem with grouping on 'parameter'
        if GROUPING_HINT in identifier:
            for snippet_group in snippet_groups:
                for snippet in snippet_group.snippets.all():
                    if snippet.identifier.get(
                        GROUPING_HINT) == identifier[GROUPING_HINT]:
                        found_snippet_group = snippet_group
                        break

        # (2) find an item in a group with the same
        # workspace_item. This is a backup grouping mechanism
        if not found_snippet_group:
            for snippet_group in snippet_groups:
                if snippet_group.snippets.filter(
                    workspace_item=workspace_item).exists():
                    found_snippet_group = snippet_group

        # (3) No existing snippet group: make one.
        if not found_snippet_group:
            found_snippet_group = self.snippet_groups.create()

        snippet, snippet_created = found_snippet_group.snippets.get_or_create(
            workspace_item=workspace_item,
            identifier_json=identifier_json,
            shortname=shortname,
            name=name)
        return snippet, snippet_created


class WorkspaceCollageSnippetGroup(models.Model):
    """Contains a group of snippets, belongs to one collage"""
    AGGREGATION_PERIOD_CHOICES = (
        (ALL, _('all')),
        (YEAR, _('year')),
        (QUARTER, _('quarter')),
        (MONTH, _('month')),
        (WEEK, _('week')),
        (DAY, _('day')),
        )

    workspace_collage = models.ForeignKey(WorkspaceCollage,
                                          related_name='snippet_groups')
    index = models.IntegerField(default=1000)  # larger = lower in the list
    name = models.TextField(blank=True, null=True)

    # boundary value for statistics
    boundary_value = models.FloatField(blank=True, null=True)
    aggregation_period = models.IntegerField(
        choices=AGGREGATION_PERIOD_CHOICES, default=ALL)

    layout_title = models.CharField(max_length=80, blank=True, null=True)
    layout_x_label = models.CharField(max_length=80, blank=True, null=True)
    layout_y_label = models.CharField(max_length=80, blank=True, null=True)
    layout_y_min = models.FloatField(blank=True, null=True)
    layout_y_max = models.FloatField(blank=True, null=True)

    class Meta:
        verbose_name = _('Collage snippet group')
        verbose_name_plural = _('Collage snippet groups')
        ordering = ['name', ]

    def __unicode__(self):
        if self.snippets_summary:
            return self.snippets_summary[:80]
        else:
            return '(empty snippet_group)'

    @property
    def workspace(self):
        return self.workspace_collage.workspace

    @property
    def snippets_summary(self):
        return ', '.join([snippet.__unicode__() for snippet
                          in self.snippets.all()])

    def statistics(self, start_date, end_date):
        """
        Calcs standard statistics: min, max, avg, count_lt, count_gte,
        percentile 25, percentile 75 and return them in a list of dicts
        """
        statistics = []
        for snippet in self.snippets.all():
            snippet_adapter = snippet.workspace_item.adapter
            # base statistics
            statistics_row = snippet_adapter.value_aggregate(
                snippet.identifier,
                {'min': None, 'max': None, 'avg': None,
                 'count_lt': self.boundary_value,
                 'count_gte': self.boundary_value,
                 'percentile': 25},
                start_date=start_date,
                end_date=end_date)
            # add 75 percentile
            statistics_percentile75 = snippet_adapter.value_aggregate(
                snippet.identifier,
                {'percentile': 75},
                start_date=start_date,
                end_date=end_date)
            statistics_row.update(
                {'percentile_75': statistics_percentile75['percentile']})

            # add name
            statistics_row['name'] = snippet.name
            statistics.append(statistics_row)
        return statistics

    def layout(self):
        """Returns layout properties of this snippet_group. Used in
        snippet.identifier['layout']"""
        result = {}
        if self.layout_y_label:
            result['y_label'] = self.layout_y_label
        if self.layout_x_label:
            result['x_label'] = self.layout_x_label
        if self.layout_y_min is not None:
            result['y_min'] = self.layout_y_min
        if self.layout_y_max is not None:
            result['y_max'] = self.layout_y_max
        if self.layout_title:
            result['title'] = self.layout_title
        if self.boundary_value is not None:
            result['horizontal_lines'] = [{'name': _('Boundary value'),
                                           'value': self.boundary_value,
                                           'style': {'linewidth': 3, 'linestyle': ':',
                                                     'color': 'green'}
                                           }, ]
        return result


class WorkspaceCollageSnippet(models.Model):
    """One snippet in a collage"""
    name = models.CharField(max_length=80,
                            default='snippet')
    shortname = models.CharField(max_length=80,
                                 default='snippet',
                                 blank=True,
                                 null=True)
    snippet_group = models.ForeignKey(WorkspaceCollageSnippetGroup,
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
        workspace = self.snippet_group.workspace_collage.workspace
        if len(workspace.workspace_items.filter(
                pk=self.workspace_item.pk)) == 0:
            raise "workspace_item of snippet not in workspace of collage"
        # Call the "real" save() method.
        super(WorkspaceCollageSnippet, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete model, also deletes snippet_group if that's empty"""
        snippet_group = self.snippet_group
        super(WorkspaceCollageSnippet, self).delete(*args, **kwargs)
        if not snippet_group.snippets.exists():
            snippet_group.delete()

    @property
    def identifier(self):
        """Return dict of parsed identifier_json.

        """
        return parse_identifier_json(self.identifier_json)

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
