import itertools
import logging
import mapnik

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
from south.modelsinspector import add_introspection_rules
import pkg_resources

from lizard_map.adapter import parse_identifier_json
from lizard_map.dateperiods import ALL
from lizard_map.dateperiods import YEAR
from lizard_map.dateperiods import QUARTER
from lizard_map.dateperiods import MONTH
from lizard_map.dateperiods import WEEK
from lizard_map.dateperiods import DAY
from lizard_map.dateperiods import calc_aggregation_periods
from lizard_map.dateperiods import fancy_period
from lizard_map.mapnik_helper import point_rule

# Do not change the following items!
GROUPING_HINT = 'grouping_hint'
USER_WORKSPACES = 'user'
DEFAULT_WORKSPACES = 'default'
TEMP_WORKSPACES = 'temp'

# TODO: Can this property be moved to mapnik_helper?
ICON_ORIGINALS = pkg_resources.resource_filename('lizard_map', 'icons')

ADAPTER_ENTRY_POINT = 'lizard_map.adapter_class'
SEARCH_ENTRY_POINT = 'lizard_map.search_method'
LOCATION_ENTRY_POINT = 'lizard_map.location_method'

logger = logging.getLogger(__name__)
# Add introspection rules for ColorField
add_introspection_rules([], ["lizard_map.models.ColorField"])


def legend_values(min_value, max_value, min_color, max_color, steps):
    """Interpolates colors between min_value and max_value, calc
    corresponding colors and gives boundary values for each band.

    Makes list of dictionaries: {'color': Color, 'low_value':
    low value, 'high_value': high value}"""
    result = []
    value_per_step = (max_value - min_value) / steps
    for step in range(steps):
        try:
            fraction = float(step) / (steps - 1)
        except ZeroDivisionError:
            fraction = 0
        alpha = (min_color.a * (1 - fraction) +
                 max_color.a * fraction)
        red = (min_color.r * (1 - fraction) +
               max_color.r * fraction)
        green = (min_color.g * (1 - fraction) +
                 max_color.g * fraction)
        blue = (min_color.b * (1 - fraction) +
                max_color.b * fraction)
        color = Color('%02x%02x%02x%02x' % (red, green, blue, alpha))

        low_value = min_value + step * value_per_step
        high_value = min_value + (step + 1) * value_per_step
        result.append({
                'color': color,
                'low_value': low_value,
                'high_value': high_value,
                })
    return result


class Color(str):
    """Simple color object: r, g, b, a.

    The object is in fact a string with class variables.
    """
    def __init__(self, s):
        self.r = None
        self.g = None
        self.b = None
        if s is None:
            return
        try:
            self.r = int(s[0:2], 16)
        except ValueError:
            self.r = 128
        try:
            self.g = int(s[2:4], 16)
        except ValueError:
            self.b = 128
        try:
            self.b = int(s[4:6], 16)
        except ValueError:
            self.b = 128
        try:
            # Alpha is optional.
            self.a = int(s[6:8], 16)
        except ValueError:
            self.a = 255

    def to_tuple(self):
        """
        Returns color values in a tuple. Values are 0..1
        """
        result = (self.r / 255.0, self.g / 255.0,
                  self.b / 255.0, self.a / 255.0)
        return result

    @property
    def html(self):
        """
        Returns color in html format.
        """
        if self.r is not None and self.g is not None and self.b is not None:
            return '#%02x%02x%02x' % (self.r, self.g, self.b)
        else:
            return '#ff0000'  # Red as alarm color


class ColorField(models.CharField):
    """Custom ColorField for use in Django models. It's an extension
    of CharField."""

    default_error_messages = {
        'invalid': _(
            u'Enter a valid color code rrggbbaa, '
            'where aa is optional.'),
        }
    description = "Color representation in rgb"

    # Ensures that to_python is always called.
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 8
        super(ColorField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        return str(value)

    def to_python(self, value):
        if isinstance(value, Color):
            return value
        return Color(value)


def adapter_class_names():
    """Return allowed layer method names (from entrypoints)

    in tuple of 2-tuples
    """
    entrypoints = [(entrypoint.name, entrypoint.name) for entrypoint in
                   pkg_resources.iter_entry_points(group=ADAPTER_ENTRY_POINT)]
    return tuple(entrypoints)


class AdapterClassNotFoundError(Exception):
    pass


###### Models start here ######


class Workspace(models.Model):
    """Collection for managing what's visible on a map."""

    class Meta:
        verbose_name = _("Workspace")
        verbose_name_plural = _("Workspaces")

    name = models.CharField(max_length=80,
                            blank=True,
                            default='My Workspace')

    owner = models.ForeignKey(User, blank=True, null=True)
    visible = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s' % (self.name)

    def get_absolute_url(self):
        return reverse('lizard_map_workspace',
                       kwargs={'workspace_id': self.id})

    def extent(self):
        """
        Returns workspace extent, using extents from workspace items.
        """
        north = None
        south = None
        east = None
        west = None
        for workspace_item in self.workspace_items.all():
            wsi_extent = workspace_item.adapter.extent()
            if wsi_extent['east'] > east or east is None:
                east = wsi_extent['east']
            if wsi_extent['west'] < west or west is None:
                west = wsi_extent['west']
            if wsi_extent['south'] < south or south is None:
                south = wsi_extent['south']
            if wsi_extent['north'] > north or north is None:
                north = wsi_extent['north']
        return {'north': north, 'south': south, 'east': east, 'west': west}

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

    # Boundary value for statistics.
    boundary_value = models.FloatField(blank=True, null=True)
    # Percentile value for statistics.
    percentile_value = models.FloatField(blank=True, null=True)
    # Restrict_to_month is used to filter the data.
    restrict_to_month = models.IntegerField(blank=True, null=True)
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
        percentile and return them in a list of dicts

        Can be filtered by option restrict_to_month.
        """
        statistics = []
        for snippet in self.snippets.all():
            snippet_adapter = snippet.workspace_item.adapter

            # Calc periods based on aggregation period setting.
            periods = calc_aggregation_periods(start_date, end_date,
                                               self.aggregation_period)

            for period_start_date, period_end_date in periods:
                if not self.restrict_to_month or (
                    self.aggregation_period != MONTH) or (
                    self.aggregation_period == MONTH and
                    self.restrict_to_month == period_start_date.month):

                    # Base statistics for each period.
                    statistics_row = snippet_adapter.value_aggregate(
                        snippet.identifier,
                        {'min': None,
                         'max': None,
                         'avg': None,
                         'count_lt': self.boundary_value,
                         'count_gte': self.boundary_value,
                         'percentile': self.percentile_value},
                        start_date=period_start_date,
                        end_date=period_end_date)

                    # Add name.
                    if statistics_row:
                        statistics_row['name'] = snippet.name
                        statistics_row['period'] = fancy_period(
                            period_start_date, period_end_date,
                            self.aggregation_period)
                        statistics.append(statistics_row)

        if len(statistics) > 1:
            # Also show a 'totals' column.
            averages = [row['avg'] for row in statistics if row['avg']]
            try:
                average = float(sum(averages) / len(averages))
            except ZeroDivisionError:
                average = None
            totals = {
                'min': min([row['min'] for row in statistics]),
                'max': max([row['max'] for row in statistics]),
                'avg': average,
                'name': 'Totaal',
                }
            if statistics[0]['count_lt'] is not None:
                totals['count_lt'] = sum(
                    [row['count_lt'] for row in statistics
                     if row['count_lt']])
            else:
                totals['count_lt'] = None
            if statistics[0]['count_gte'] is not None:
                totals['count_gte'] = sum(
                    [row['count_gte'] for row in statistics
                     if row['count_gte']])
            else:
                totals['count_gte'] = None
            # We cannot calculate a meaningful total percentile here.
            totals['percentile'] = None
            statistics.append(totals)

        return statistics

    def values_table(self, start_date, end_date):
        """
        Calculates a table with each location as column, each row as
        datetime. First row consist of column names. List of lists.

        Can be filtered by option restrict_to_month.
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
                if not self.restrict_to_month or (
                    self.aggregation_period != MONTH) or (
                    self.aggregation_period == MONTH and
                    row['datetime'].month == self.restrict_to_month):

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
        if self.restrict_to_month:
            result['restrict_to_month'] = self.restrict_to_month
        if self.boundary_value is not None:
            result['horizontal_lines'] = [{
                    'name': _('Boundary value'),
                    'value': self.boundary_value,
                    'style': {'linewidth': 3,
                              'linestyle': '--',
                              'color': 'green'},
                    }, ]
        # TODO: implement percentile. Start/end date is not known here.
        # if self.percentile_value is not None:
        #     calculated_percentile = self.statistics(self.percentile_value,,)
        #     result['horizontal_lines'] = [{
        #             'name': _('Percentile value'),
        #             'value': calculated_percentile,
        #             'style': {'linewidth': 2,
        #                       'linestyle': '--',
        #                       'color': 'green'},
        #             }, ]
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
    be found using the descriptor.

    Used for mapnik lines and polygons.
    """

    descriptor = models.CharField(max_length=80)
    min_value = models.FloatField(default=0)
    max_value = models.FloatField(default=100)
    steps = models.IntegerField(default=10)

    default_color = ColorField()
    min_color = ColorField()
    max_color = ColorField()
    too_low_color = ColorField()
    too_high_color = ColorField()

    objects = LegendManager()

    def __unicode__(self):
        return self.descriptor

    @property
    def float_format(self):
        """Determines float format for defined legend. Required by legend_default."""
        delta = abs(self.max_value - self.min_value) / self.steps
        if delta < 0.1:
            return '%.3f'
        if delta < 1:
            return '%.2f'
        if delta < 10:
            return '%.1f'
        return '%.0f'

    def legend_values(self):
        """Determines legend steps and values. Required by legend_default."""
        return legend_values(
            self.min_value, self.max_value,
            self.min_color, self.max_color, self.steps)

    def update(self, updates):
        """ Updates model with updates dict. Color values have the
        following format: string rrggbb in hex """

        def makecolor(c):
            r, g, b = [int('0x%s' % c[r:r + 2], 0) for r in range(0, 6, 2)]
            a = 1
            return Color(a=a, r=r, g=g, b=b)

        for k, v in updates.items():
            if k == 'min_value':
                self.min_value = float(v)
            elif k == 'max_value':
                self.max_value = float(v)
            elif k == 'steps':
                self.steps = int(v)
            elif k == 'min_color':
                try:
                    self.min_color = makecolor(v)
                except ValueError:
                    logger.warn('Could not parse min_color (%s)' % v)
            elif k == 'max_color':
                try:
                    self.max_color = makecolor(v)
                except ValueError:
                    logger.warn('Could not parse max_color (%s)' % v)
            elif k == 'too_low_color':
                try:
                    self.too_low_color = makecolor(v)
                except ValueError:
                    logger.warn('Could not parse too_low_color (%s)' % v)
            elif k == 'too_high_color':
                try:
                    self.too_high_color = makecolor(v)
                except ValueError:
                    logger.warn('Could not parse too_high_color (%s)' % v)

    def mapnik_style(self, value_field=None):
        """Return a Mapnik line/polystyle from Legend object"""

        def mapnik_rule(color, mapnik_filter=None):
            """
            Makes mapnik rule for looks. For lines and polygons.
            """
            rule = mapnik.Rule()
            if mapnik_filter is not None:
                rule.filter = mapnik.Filter(mapnik_filter)
            mapnik_color = mapnik.Color(color.r, color.g, color.b)

            symb_line = mapnik.LineSymbolizer(mapnik_color, 3)
            rule.symbols.append(symb_line)

            symb_poly = mapnik.PolygonSymbolizer(mapnik_color)
            symb_poly.fill_opacity = 0.5
            rule.symbols.append(symb_poly)
            return rule

        mapnik_style = mapnik.Style()
        if value_field is None:
            value_field = "value"

        # Default color: red.
        rule = mapnik_rule(self.default_color)
        mapnik_style.rules.append(rule)

        # < min
        mapnik_filter = "[%s] <= %f" % (value_field, self.min_value)
        logger.debug('adding mapnik_filter: %s' % mapnik_filter)
        rule = mapnik_rule(self.too_low_color, mapnik_filter)
        mapnik_style.rules.append(rule)

        # in boundaries
        for legend_value in self.legend_values():
            mapnik_filter = "[%s] > %f and [%s] <= %f" % (
                value_field, legend_value['low_value'],
                value_field, legend_value['high_value'])
            logger.debug('adding mapnik_filter: %s' % mapnik_filter)
            rule = mapnik_rule(legend_value['color'], mapnik_filter)
            mapnik_style.rules.append(rule)

        # > max
        mapnik_filter = "[%s] > %f" % (value_field, self.max_value)
        logger.debug('adding mapnik_filter: %s' % mapnik_filter)
        rule = mapnik_rule(self.too_high_color, mapnik_filter)
        mapnik_style.rules.append(rule)

        return mapnik_style

    def mapnik_linestyle(self, value_field=None):
        """Deprecated. Use mapnik_style instead. Return a Mapnik
        line/polystyle from Legend object"""
        return mapnik_style(self, value_field=value_field)


class LegendPoint(Legend):
    """
    Legend for points.
    """

    icon = models.CharField(max_length=80, default='empty.png')
    mask = models.CharField(max_length=80, null=True, blank=True,
                            default='empty_mask.png')

    def __unicode__(self):
        return '%s' % (self.descriptor)

    def icon_style(self):
        return {'icon': self.icon,
                'mask': (self.mask, ),
                'color': (1.0, 1.0, 1.0, 1.0)}

    def mapnik_style(self, value_field=None):
        """Return a Mapnik style from Legend object. """

        mapnik_style = mapnik.Style()
        if value_field is None:
            value_field = "value"

        # Default color: red.
        mapnik_rule = point_rule(
            self.icon, self.mask, self.default_color)
        mapnik_style.rules.append(mapnik_rule)

        # < min
        mapnik_filter = "[%s] <= %f" % (value_field, self.min_value)
        logger.debug('adding mapnik_filter: %s' % mapnik_filter)
        mapnik_rule = point_rule(
            self.icon, self.mask, self.too_low_color, mapnik_filter=mapnik_filter)
        mapnik_style.rules.append(mapnik_rule)

        # in boundaries
        for legend_value in self.legend_values():
            mapnik_filter = "[%s] > %f and [%s] <= %f" % (
                value_field, legend_value['low_value'],
                value_field, legend_value['high_value'])
            logger.debug('adding mapnik_filter: %s' % mapnik_filter)
            mapnik_rule = point_rule(
                self.icon, self.mask, legend_value['color'],
                mapnik_filter=mapnik_filter)
            mapnik_style.rules.append(mapnik_rule)

        # > max
        mapnik_filter = "[%s] > %f" % (value_field, self.max_value)
        logger.debug('adding mapnik_filter: %s' % mapnik_filter)
        mapnik_rule = point_rule(
            self.icon, self.mask, self.too_high_color,
            mapnik_filter=mapnik_filter)
        mapnik_style.rules.append(mapnik_rule)

        return mapnik_style
