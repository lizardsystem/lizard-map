import itertools
import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
import pkg_resources

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
                            default='Workspace')
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
        layer_json = self.adapter_layer_json
        if not layer_json:
            return {}
        result = {}
        for k, v in json.loads(layer_json).items():
            result[str(k)] = v
        return result

    def has_adapter(self):
        """Can I provide a adapter class for i.e. WMS layer?"""
        return bool(self.adapter_class)

    def delete(self, *args, **kwargs):
        """
        When deleting a WorkspaceItem, delete corresponding snippets
        """
        snippets = WorkspaceCollageSnippet.objects.filter(workspace_item=self)
        # We delete snippets individually because snippets.delete()
        # will not remove empty snippet_groups.
        for snippet in snippets:
            snippet.delete()
        super(WorkspaceItem, self).delete(*args, **kwargs)


class WorkspaceCollage(models.Model):
    """A collage contains selections/locations from a workspace"""
    name = models.CharField(max_length=80,
                            default='Collage')
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
        """Return workspace items used by one of our snippets."""
        # .distinct may not be used on textfields in oracle as oracle stores
        # them as NCLOB columns...  At least, that was the problem when our
        # 'name' field was a TextField instead of a CharField.  So I reverted
        # this change as it didn't turn out to be the problem after all.
        # Leaving it here in case it turns out to be a recurring problem.
        # found = set()
        # for snippet in self.snippets.all():
        #     found.add(snippet.workspace_item)
        # return list(found)
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
                    break

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
    name = models.CharField(max_length=80, blank=True, null=True)

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
            return self.snippets_summary
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
            try:
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
                if 'percentile' in statistics_percentile75:
                    statistics_row.update(
                        {'percentile_75':
                             statistics_percentile75['percentile']})

                # add name
                statistics_row['name'] = snippet.name
                statistics.append(statistics_row)
            except NotImplementedError:
                # If the function value_aggregate is not implemented, skip
                pass
        return statistics

    def values_table(self, start_date, end_date):
        """
        Calculates a table with each location as column, each row as
        datetime. First row consist of column names. List of lists.
        """
        values_table = []

        snippets = self.snippets.all()

        # Add snippet names
        values_table.append(['Datum + tijdstip'] +
                            [snippet.name for snippet in snippets])

        # Collect all data and found_dates.
        found_dates = {}

        # Snippet_values is a dict of (dicts of dicts {'datetime': .,
        # 'value': .., 'unit': ..}, key: 'datetime').
        snippet_values = {}

        for snippet in snippets:
            values = snippet.workspace_item.adapter.values(
                identifier=snippet.identifier, start_date=start_date,
                end_date=end_date)
            snippet_values[snippet.id] = {}
            # Translate list into dict with dates.
            for row in values:
                snippet_values[snippet.id][row['datetime']] = row
            found_dates.update(snippet_values[snippet.id])
            # ^^^ The value doesn't matter.

        found_dates_sorted = found_dates.keys()
        found_dates_sorted.sort()

        # Create each row.
        for found_date in found_dates_sorted:
            value_row = [found_date, ]
            for snippet in snippets:
                single_value = snippet_values[snippet.id].get(found_date, {})
                value_row.append(single_value.get('value', None))
            values_table.append(value_row)

        return values_table

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
            result['horizontal_lines'] = [{
                    'name': _('Boundary value'),
                    'value': self.boundary_value,
                    'style': {'linewidth': 3,
                              'linestyle': '--',
                              'color': 'green'},
                    }, ]
        return result


class WorkspaceCollageSnippet(models.Model):
    """One snippet in a collage"""
    name = models.CharField(max_length=80,
                            default='Snippet')
    shortname = models.CharField(max_length=80,
                                 default='Snippet',
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

    def set_identifier(self, identifier):
        """sets dictionary identifier to property identifier_json"""
        self.identifier_json = json.dumps(identifier).replace('"', '%22')


class Color(models.Model):
    """Simple color: alpha (optional), r, g, b.

    Use values from 0 .. 255. Values are NOT checked!
    """
    a = models.IntegerField(default=255)
    r = models.IntegerField()
    g = models.IntegerField()
    b = models.IntegerField()

    def __unicode__(self):
        return '(%0x)-%0x-%0x-%0x' % (self.a, self.r, self.g, self.b)


class LegendManager(models.Manager):
    """Implements extra function 'find'
    """

    def find(self, name):
        """Tries to find matching legend. Second choice legend
        'default'. If nothing found, return None"""

        try:
            found_legend = Legend.objects.get(descriptor__icontains=name)
        except Legend.DoesNotExist:
            try:
                found_legend = Legend.objects.get(descriptor='default')
            except Legend.DoesNotExist:
                found_legend = None
        return found_legend


class Legend(models.Model):
    """Simple lineair interpolated legend with min, max, color-min,
    color-max, color < min, color > max, number of steps. Legends can
    be found using the descriptor"""

    descriptor = models.CharField(max_length=80)
    min_value = models.FloatField(default=0)
    max_value = models.FloatField(default=100)
    steps = models.IntegerField(default=10)

    min_color = models.ForeignKey(Color, related_name='min_colors')
    max_color = models.ForeignKey(Color, related_name='max_colors')
    too_low_color = models.ForeignKey(Color, related_name='too_low_colors')
    too_high_color = models.ForeignKey(Color, related_name='too_high_color')

    objects = LegendManager()

    def __unicode__(self):
        return self.descriptor

    @property
    def float_format(self):
        delta = abs(self.max_value - self.min_value) / self.steps
        if delta < 0.1:
            return '%.3f'
        if delta < 1:
            return '%.2f'
        if delta < 10:
            return '%.1f'
        return '%.0f'

    def legend_values(self):
        """Makes list of dictionaries: {'color': Color, 'low_value':
        low value, 'high_value': high value}"""
        result = []
        value_per_step = (self.max_value - self.min_value) / self.steps
        for step in range(self.steps):
            try:
                fraction = float(step) / (self.steps - 1)
            except ZeroDivisionError:
                fraction = 0
            alpha = (self.min_color.a * (1 - fraction) +
                     self.max_color.a * fraction)
            red = (self.min_color.r * (1 - fraction) +
                   self.max_color.r * fraction)
            green = (self.min_color.g * (1 - fraction) +
                     self.max_color.g * fraction)
            blue = (self.min_color.b * (1 - fraction) +
                    self.max_color.b * fraction)
            color = Color(a=alpha, r=red, g=green, b=blue)

            low_value = self.min_value + step * value_per_step
            high_value = self.min_value + (step + 1) * value_per_step
            result.append({
                    'color': color,
                    'low_value': low_value,
                    'high_value': high_value,
                    })
        return result
