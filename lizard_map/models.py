import itertools
import logging
import mapnik

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.db.models.signals import post_delete
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
OTHER_WORKSPACES = 'other'  # for flexible adding workspaces of others

# TODO: Can this property be moved to mapnik_helper?
ICON_ORIGINALS = pkg_resources.resource_filename('lizard_map', 'icons')

ADAPTER_ENTRY_POINT = 'lizard_map.adapter_class'
SEARCH_ENTRY_POINT = 'lizard_map.search_method'
LOCATION_ENTRY_POINT = 'lizard_map.location_method'

# WMS is a special kind of adapter: the client side behaves different.
ADAPTER_CLASS_WMS = 'wms'

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


class WorkspaceItemError(Exception):
    """To be raised when a WorkspaceItem is out of date.

    A WorkspaceItem can represent something that does no longer exist.
    For example, it may refer to a shape that has been deleted from
    the database. This error may trigger deletion of such orphans.
    """
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

    def wms_layers(self):
        """
        Returns a list of wms_layers. Each wms_layer is a dict with keys:
        wms_id, name, url, params, options. They are used in wms.html
        """
        result = []
        for workspace_item in self.workspace_items.filter(
            adapter_class=ADAPTER_CLASS_WMS, visible=True):

            # The special WMS layer arguments provides name, url,
            # params, options.
            layer_arguments = workspace_item.adapter_layer_arguments
            layer_arguments.update(
                {'wms_id': '%d_%d' % (self.id, workspace_item.id)})
            result.append(layer_arguments)

        result.reverse()
        return result

    @property
    def is_animatable(self):
        """Determine if any visible workspace_item is animatable."""
        for workspace_item in self.workspace_items.filter(visible=True):
            if workspace_item.adapter.is_animatable:
                return True
        return False


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
        if self.id is None:
            # We've already been deleted...
            return u'DELETED WORKSPACEITEM'
        return u'(%d) name=%s ws=%s %s' % (self.id, self.name, self.workspace,
                                           self.adapter_class)

    @property
    def adapter(self):
        """Return adapter instance for entrypoint"""
        # TODO: this happens more often than needed! Cache it.
        for entrypoint in pkg_resources.iter_entry_points(
            group=ADAPTER_ENTRY_POINT):
            if entrypoint.name == self.adapter_class:
                try:
                    real_adapter = entrypoint.load()
                    real_adapter = real_adapter(self,
                        layer_arguments=self.adapter_layer_arguments)
                except ImportError, e:
                    logger.critical("Invalid entry point: %s", e)
                    raise
                except WorkspaceItemError:
                    logger.warning(
                        "Deleting problematic WorkspaceItem: %s", self)
                    # Trac #2470. Return a NullAdapter instead?
                    self.delete()
                    return None
                return real_adapter
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
        try:
            decoded_json = json.loads(layer_json)
        except json.JSONDecodeError:
            raise WorkspaceItemError("Undecodable json: %s", layer_json)
        for k, v in decoded_json.items():
            result[str(k)] = v
        return result

    def has_adapter(self):
        """Can I provide a adapter class for i.e. WMS layer?"""
        return bool(self.adapter_class)

    def has_extent(self):
        """
        Return true if workspace item has an extent function.

        Note: no performance changes seen after changing "return True"
        to getattr.
        """
        return getattr(self.adapter, 'extent', None) is not None

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

    def visible_snippet_groups(self):
        """Return only snippet_groups that have visible snippets."""
        return self.snippet_groups.filter(snippets__visible=True).distinct()

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
        for snippet in self.snippets.filter(visible=True):
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

        Can be filtered by option restrict_to_month. Only visible snippets
        are included.
        """
        values_table = []

        snippets = self.snippets.filter(visible=True)

        # Add snippet names
        values_table.append(['Datum + tijdstip'] +
                            [snippet.name for snippet in snippets])

        # Collect all data and found_dates.
        found_dates = {}

        # Snippet_values is a dict of (dicts of dicts {'datetime': .,
        # 'value': .., 'unit': ..}, key: 'datetime').
        snippet_values = {}

        for snippet in snippets:
            adapter = snippet.workspace_item.adapter
            try:
                values = adapter.values(
                    identifier=snippet.identifier, start_date=start_date,
                    end_date=end_date)
            except NotImplementedError:
                # If adapter.value is not implemented, just ignore.
                pass
            else:
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
    visible = models.BooleanField(default=True)

    # ^^^ Format depends on workspace_item layer_method

    class Meta:
        ordering = ['name', ]

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
        """Determine float format for defined legend.

        Required by legend_default."""
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
        return self.mapnik_style(self, value_field=value_field)


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
            self.icon, self.mask, self.too_low_color,
            mapnik_filter=mapnik_filter)
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


class BackgroundMap(models.Model):
    """
    Defines background maps.
    """
    LAYER_TYPE_GOOGLE = 1
    LAYER_TYPE_OSM = 2
    LAYER_TYPE_WMS = 3

    LAYER_TYPE_CHOICES = (
        (LAYER_TYPE_GOOGLE, 'GOOGLE'),
        (LAYER_TYPE_OSM, 'OSM'),
        (LAYER_TYPE_WMS, 'WMS'),
        )

    GOOGLE_TYPE_DEFAULT = 1
    GOOGLE_TYPE_PHYSICAL = 2
    GOOGLE_TYPE_HYBRID = 3
    GOOGLE_TYPE_SATELLITE = 4

    GOOGLE_TYPE_CHOICES = (
        (GOOGLE_TYPE_DEFAULT, 'google default'),
        (GOOGLE_TYPE_PHYSICAL, 'google physical'),
        (GOOGLE_TYPE_HYBRID, 'google hybrid'),
        (GOOGLE_TYPE_SATELLITE, 'google satellite'),
        )

    name = models.CharField(max_length=20)
    index = models.IntegerField(default=100)
    default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    layer_type = models.IntegerField(choices=LAYER_TYPE_CHOICES)
    google_type = models.IntegerField(
        choices=GOOGLE_TYPE_CHOICES,
        null=True, blank=True,
        help_text='Choose map type in case of GOOGLE maps.')
    layer_url = models.CharField(
        max_length=200,
        null=True, blank=True,
        help_text='Tile url for use with OSM or WMS',
        default='http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png')
    layer_names = models.TextField(
        null=True, blank=True,
        help_text='Fill in layer names in case of WMS')

    class Meta:
        ordering = ('index', )

    def __unicode__(self):
        return '%s' % self.name


class Setting(models.Model):
    """
    Global settings.

    Available keys with default values:
    projection 'EPSG:900913'
    display_projection 'EPSG:4326'
    googlemaps_api_key
    """
    CACHE_KEY = 'lizard-map.Setting'

    key = models.CharField(max_length=40, unique=True)
    value = models.CharField(max_length=200)

    def __unicode__(self):
        return '%s = %s' % (self.key, self.value)

    @classmethod
    def get(cls, key, default=None):
        """
        Return value from given key.

        If the key does not exist, return None. Caches the whole
        Setting table.
        """

        # Caching.
        settings = cache.get(cls.CACHE_KEY)  # Dict
        if settings is None:
            settings = {}
            for setting in cls.objects.all():
                settings[setting.key] = setting.value
            cache.set(cls.CACHE_KEY, settings)

        # Fallback for default.
        if key not in settings:
            if default is not None:
                # Only warn if None is not a fine value: otherwise we'd warn
                # about a setting that doesn't *need* to be set.
                logger.warn('Setting "%s" does not exist, taking default '
                            'value "%s"' % (key, default))
            return default

        # Return desired result.
        return settings[key]

    @classmethod
    def get_dict(cls, key, default=None):
        """
        Return {key: value} for given key
        """
        return {key: cls.get(key, default)}


# For Django 1.3:
# @receiver(post_save, sender=Setting)
# @receiver(post_delete, sender=Setting)
def setting_post_save_delete(sender, **kwargs):
    """
    Invalidates cache after saving or deleting a setting.
    """
    logger.debug('Changed setting. Invalidating cache for %s...' %
                 sender.CACHE_KEY)
    cache.delete(sender.CACHE_KEY)


post_save.connect(setting_post_save_delete, sender=Setting)
post_delete.connect(setting_post_save_delete, sender=Setting)
