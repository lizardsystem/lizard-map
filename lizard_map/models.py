# Unchecked imports start here
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

from lizard_map.dateperiods import ALL
from lizard_map.dateperiods import YEAR
from lizard_map.dateperiods import QUARTER
from lizard_map.dateperiods import MONTH
from lizard_map.dateperiods import WEEK
from lizard_map.dateperiods import DAY
from lizard_map.dateperiods import calc_aggregation_periods
from lizard_map.dateperiods import fancy_period
from lizard_map.mapnik_helper import point_rule
# Unchecked end here

from adapter import adapter_layer_arguments
from adapter import adapter_entrypoint
from adapter import adapter_class_names
from adapter import adapter_serialize

# Temporary, because fewsjdbc api handler imports this.
from adapter import ADAPTER_ENTRY_POINT
ADAPTER_ENTRY_POINT

# New imports
import datetime
from django.core.serializers.json import DjangoJSONEncoder

from lizard_map.adapter import AdapterClassNotFoundError
#from jsonfield.fields import JSONField


# Do not change the following items!
GROUPING_HINT = 'grouping_hint'
USER_WORKSPACES = 'user'
DEFAULT_WORKSPACES = 'default'
TEMP_WORKSPACES = 'temp'
OTHER_WORKSPACES = 'other'  # for flexible adding workspaces of others

# TODO: Can this property be moved to mapnik_helper?
ICON_ORIGINALS = pkg_resources.resource_filename('lizard_map', 'icons')

#ADAPTER_ENTRY_POINT = 'lizard_map.adapter_class'
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


#From:
#https://github.com/bradjasper/django-jsonfield/blob/master/jsonfield/fields.py
#Using djang-jsonfield results in an error in admin pages using this
#field.

# Add south introspection rules.
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^lizard_map\.models\.JSONField"])
except:
    # South is not used.
    pass


class JSONField(models.TextField):
    """JSONField is a generic textfield that neatly serializes/unserializes
JSON objects seamlessly"""

    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""

        if value == "":
            return None

        try:
            if isinstance(value, basestring):
                return json.loads(value)
        except ValueError:
            pass

        return value

    def get_db_prep_save(self, value, connection):
        """Convert our JSON object to a string before we save"""

        if not value or value == "":
            return None

        if isinstance(value, (dict, list)):
            value = json.dumps(value, cls=DjangoJSONEncoder)

        # Changed connection to kwarg to fix error.
        return super(JSONField, self).get_db_prep_save(
            value, connection=connection)


class WorkspaceItemError(Exception):
    """To be raised when a WorkspaceItem is out of date.

    A WorkspaceItem can represent something that does no longer exist.
    For example, it may refer to a shape that has been deleted from
    the database. This error may trigger deletion of such orphans.
    """
    pass


###### Models start here ######

#### L3 models ####


class PeriodMixin(models.Model):
    """
    Define a period and time, relative or absolute.
    """

    # Datetime.
    dt_start = models.DateTimeField(blank=True, null=True)
    dt_end = models.DateTimeField(blank=True, null=True)
    dt = models.DateTimeField(blank=True, null=True)

    # All relative dates are "normalized to days".
    # Timedelta.
    td_start = models.FloatField(blank=True, null=True)
    td_end = models.FloatField(blank=True, null=True)
    td = models.FloatField(blank=True, null=True)

    # Take datetime or timedelta.
    absolute = models.BooleanField(default=False)

    # Take dt (True) or dt_end (False) (or td or td_end)
    custom_time = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def _dt_fallback(self, now=None):
        """Return 3-tuple with fallbacks for dt, dt_start and dt_end.
        """
        if now is None:
            now = datetime.datetime.now()
        return (
            now,
            now + datetime.timedelta(-10.0),
            now + datetime.timedelta(1.0))

    def period(self, now=None, fallback=False):
        """
        Return specified period. Depends on absolute and custom_time.
        """
        try:
            if self.absolute:
                dt_start, dt_end = self.dt_start, self.dt_end
            else:
                if now is None:
                    now = datetime.datetime.now()
                dt_start = now + datetime.timedelta(self.td_start)
                dt_end = now + datetime.timedelta(self.td_end)
        except TypeError:
            if fallback:
                _, dt_start, dt_end = self._dt_fallback(now=now)
            else:
                dt_start, dt_end = None, None
        return dt_start, dt_end

    def time(self, now=None, fallback=False):
        """
        Return specified time. Depends on absolute and custom_time.
        """
        try:
            if self.absolute:
                if self.custom_time:
                    dt = self.dt
                else:
                    dt = self.dt_end
            else:
                if now is None:
                    now = datetime.datetime.now()
                if self.custom_time:
                    dt = now + datetime.timedelta(self.td)
                else:
                    dt = now + datetime.timedelta(self.td_end)
        except TypeError:
            if fallback:
                dt, _, _ = self._dt_fallback(now=now)
            else:
                dt = None
        return dt


class ExtentMixin(models.Model):
    # Extent.
    x_min = models.FloatField(default=-14675)
    y_min = models.FloatField(default=6668977)
    x_max = models.FloatField(default=1254790)
    y_max = models.FloatField(default=6964942)

    class Meta:
        abstract = True

    def extent(self):
        """Return extent as (xmin, ymin, xmax, ymax)"""
        return (self.x_min, self.y_min, self.x_max, self.y_max)


class BackgroundMapMixin(models.Model):
    """
    Workspace stuff

    - Default background map
    """

    # Background map, fall back to default.
    background_map = models.ForeignKey(
        'BackgroundMap', null=True, blank=True)

    class Meta:
        abstract = True


class WorkspaceItemMixin(models.Model):
    """
    Workspace item

    # URL: points to an adapter
    """
    name = models.CharField(max_length=80,
                            blank=True)
    adapter_class = models.SlugField(choices=adapter_class_names())
    adapter_layer_json = models.TextField(blank=True)

    index = models.IntegerField(blank=True, default=100)
    visible = models.BooleanField(default=True)
    clickable = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ('index', 'visible', 'name', )

    @property
    def _adapter_layer_arguments(self):
        try:
            layer_arguments = adapter_layer_arguments(self.adapter_layer_json)
        except (ValueError, AttributeError):
            raise WorkspaceItemError("Undecodable json: %s",
                                     self.adapter_layer_json)
        return layer_arguments

    @property
    def adapter(self):
        try:
            layer_arguments = self._adapter_layer_arguments
            current_adapter = adapter_entrypoint(
                self.adapter_class, layer_arguments, self)
        except (WorkspaceItemError, AdapterClassNotFoundError):
            logger.exception(
                "Deleting problematic WorkspaceItem: %s", self)
                # Trac #2470. Return a NullAdapter instead?
            if self.id is not None:
                # Only delete if it is not saved in the first place.
                self.delete()
            return None
        return current_adapter

    def __unicode__(self):
        return self.name

    def _as_new_object(self, obj, workspace):
        """Return self as a new object with the same properties except
        workspace.

        Used when duplicating WorkspaceStorageItems to
        WorkspaceEditItems and vice versa."""
        delete_fields = ['_state', '_workspace_cache', 'workspace_id', 'id']

        # Get current data in dict.
        kwargs = self.__dict__
        for delete_me in delete_fields:
            if delete_me in kwargs:
                del kwargs[delete_me]

        # Put data in new object.
        workspace_item = obj(**kwargs)
        workspace_item.workspace = workspace
        return workspace_item

    def _url_arguments(self, identifiers):
        """for img_url, csv_url"""
        layer_json = self.adapter_layer_json.replace('"', '%22')
        url_arguments = [
            'adapter_layer_json=%s' % layer_json, ]
        url_arguments.extend([
                'identifier=%s' % adapter_serialize(
                    identifier) for identifier in identifiers])
        return url_arguments

    def url(self, url_name, identifiers, extra_kwargs=None):
        """fetch url to adapter (img, csv, ...)

        example url_name: "lizard_map_adapter_image"
        """
        kwargs = {'adapter_class': self.adapter_class}
        if extra_kwargs is not None:
            kwargs.update(extra_kwargs)
        url = reverse(
            url_name,
            kwargs=kwargs,
            )
        url += '?' + '&'.join(self._url_arguments(identifiers))
        return url


class UserSessionMixin(models.Model):
    """For objects that are bound to a user and/or session.
    """
    user = models.ForeignKey(User, null=True, blank=True, unique=True)
    session_key = models.CharField(
        max_length=40, unique=True, blank=True, null=True)

    @classmethod
    def get_or_create(cls, session_key, user):
        """Get your user session object, or create a new one.
        """
        result = None
        if user.is_authenticated():
            # Try to fetch
            try:
                result = cls.objects.get(user=user)
            except cls.DoesNotExist:
                pass
        if result is None:
            # Try to fetch based on session
            try:
                user_session_object = cls.objects.get(session_key=session_key)
                if (user.is_authenticated() and
                    user_session_object.user != user):

                    # Remove session from 'wrong' user/session combi.
                    # Should never happen.
                    user_session_object.session_key = None
                    user_session_object.save()
                    result = cls(session_key=session_key, user=user)
                    result.save()
                else:
                    result = user_session_object
            except cls.DoesNotExist:
                # Create new.
                result = cls(session_key=session_key)
                if user.is_authenticated():
                    result.user = user
                result.save()
        return result

    class Meta:
        abstract = True


class WorkspaceModelMixin(object):
    """Specifics for workspace models.
    """

    def check_workspace_item_adapters(self):
        """Call workspace items' adapters to weed out the faulty ones.

        Calling a workspace item's adapter can result in a
        WorkspaceItemError. This in turn results in an automatic deletion of
        the workspace item. But... We often call the adapter directly, like
        ``workspace_item.adapter.is_animatable``. The result is a "None has no
        attribute is_animatable" error. Tadaah, an error 500 page.

        So we just call the adapters once to make sure the faulty ones are
        deleted without tripping us up.

        """
        for workspace_item in self.workspace_items.all():
            # Just request the adapter.
            workspace_item.adapter

    @property
    def is_animatable(self):
        """Determine if any visible workspace_item is animatable."""
        for workspace_item in self.workspace_items.filter(visible=True):
            try:
                if workspace_item.adapter.is_animatable:
                    return True
            except AttributeError:
                # workspace_item/adapter is invalid.
                pass
        return False


class WorkspaceEdit(
    UserSessionMixin, BackgroundMapMixin, PeriodMixin, ExtentMixin,
    WorkspaceModelMixin):
    """
    Your editable workspace.

    Every user can only have one edit-workspace. If the user is not
    logged in, look at the session and see if any edit-workspaces
    match. If all fail, create a new edit-workspace for the user.
    """

    def __unicode__(self):
        return 'Workspace Edit of user %s' % self.user

    def save_to_storage(self, name, owner):
        """Save this model and workspace_items to Storage.
        """
        workspace_storage, _ = WorkspaceStorage.objects.get_or_create(
            name=name, owner=owner)
        # Delete all existing workspace item storages.
        workspace_storage.workspace_items.all().delete()
        # Create new workspace items.
        for workspace_edit_item in self.workspace_items.all():
            workspace_storage_item = workspace_edit_item.as_storage(
                workspace=workspace_storage)
            workspace_storage_item.save()

    def load_from_storage(self, workspace_storage):
        """Load model and workspace_items from Storage.
        """
        # Delete all existing workspace items.
        self.workspace_items.all().delete()
        # Create new workspace items.
        for workspace_storage_item in workspace_storage.workspace_items.all():
            workspace_edit_item = workspace_storage_item.as_edit(
                workspace=self)
            workspace_edit_item.save()

    def wms_url(self):
        """Used by wms.html"""
        return reverse("lizard_map_workspace_edit_wms")


class WorkspaceEditItem(WorkspaceItemMixin):
    """
    Workspace item for edit workspace.
    """
    workspace = models.ForeignKey(
        WorkspaceEdit,
        related_name='workspace_items')

    def as_storage(self, workspace):
        """Return self as a WorkspaceStorageItem."""
        return self._as_new_object(WorkspaceStorageItem, workspace)


class WorkspaceStorage(BackgroundMapMixin, PeriodMixin, ExtentMixin,
                       WorkspaceModelMixin):
    """
    Stored workspaces.
    """
    name = models.CharField(max_length=40)
    description = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(User)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.owner)

    def wms_url(self):
        """Used by wms.html"""
        return reverse("lizard_map_workspace_storage_wms",
                       kwargs={'workspace_storage_id': self.id})


class WorkspaceStorageItem(WorkspaceItemMixin):
    """
    Workspace item for stored workspace.
    """
    workspace = models.ForeignKey(
        WorkspaceStorage,
        related_name='workspace_items')

    def as_edit(self, workspace):
        """Return self as a WorkspaceEditItem."""
        return self._as_new_object(WorkspaceEditItem, workspace)


class CollageEdit(UserSessionMixin):
    """
    User selection of map locations.
    """
    pass


class StatisticsMixin(models.Model):
    """
    Statistics mixin.
    """
    AGGREGATION_PERIOD_CHOICES = (
        (ALL, _('all')),
        (YEAR, _('year')),
        (QUARTER, _('quarter')),
        (MONTH, _('month')),
        (WEEK, _('week')),
        (DAY, _('day')),
        )

    # Boundary value for statistics.
    boundary_value = models.FloatField(blank=True, null=True)
    # Percentile value for statistics.
    percentile_value = models.FloatField(blank=True, null=True)
    # Restrict_to_month is used to filter the data.
    restrict_to_month = models.IntegerField(blank=True, null=True)
    aggregation_period = models.IntegerField(
        choices=AGGREGATION_PERIOD_CHOICES, default=ALL)

    class Meta:
        abstract = True


class CollageEditItem(WorkspaceItemMixin, StatisticsMixin):
    collage = models.ForeignKey(
        CollageEdit,
        related_name='collage_items')
    identifier = JSONField(default="")

    class Meta:
        ordering = ('name', )

    def html(self, identifiers=None, is_collage=False):
        if identifiers is None:
            identifiers = [self.identifier, ]
        try:
            return self.adapter.html(
                identifiers=identifiers,
                layout_options={'is_collage': is_collage})
        except AttributeError:
            # if self.adapter crashes, it will return None
            return ""

    @property
    def default_grouping_hint(self):
        return '%s::%s' % (self.adapter_class, self.adapter_layer_json)

    @property
    def identifier_str(self):
        """
        Transform keys in identifier into strings before returning.
        """
        result = {}
        for k, v in self.identifier.items():
            result[str(k)] = v
        return result

    @property
    def grouping_hint(self):
        try:
            adapter_location = self.adapter.location(**self.identifier_str)
            return adapter_location['identifier'].get(
                'grouping_hint', self.default_grouping_hint)
        except AttributeError:
            # Adapter is None
            return self.default_grouping_hint

    def form_initial(self):
        """Initial values from object for CollageItemEditorForm."""
        result = {}
        result['boundary_value'] = self.boundary_value
        result['percentile_value'] = self.percentile_value
        result['restrict_to_month'] = self.restrict_to_month
        result['aggregation_period'] = self.aggregation_period
        identifier_layout = self.identifier.get('layout', {})
        result.update(identifier_layout)

        return result

    def img_url(self):
        return self.url("lizard_map_adapter_image", [self.identifier, ])

    def csv_url(self):
        return self.url("lizard_map_adapter_values", [self.identifier, ],
                        extra_kwargs={'output_type': 'csv'})

    def statistics(self, start_date, end_date):
        """From collage snippet group. Brings statistics and collage
        properties together.

        """
        adapter = self.adapter
        if adapter is None:
            return []

        # Calc periods based on aggregation period setting.
        periods = calc_aggregation_periods(start_date, end_date,
                                           self.aggregation_period)
        statistics = []
        for period_start_date, period_end_date in periods:
            if not self.restrict_to_month or (
                self.aggregation_period != MONTH) or (
                self.aggregation_period == MONTH and
                self.restrict_to_month == period_start_date.month):

                # Base statistics for each period.
                statistics_row = adapter.value_aggregate(
                    self.identifier,
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
                    statistics_row['name'] = self.name
                    statistics_row['period'] = fancy_period(
                        period_start_date, period_end_date,
                        self.aggregation_period)
                    statistics_row['boundary_value'] = self.boundary_value
                    statistics_row['percentile_value'] = self.percentile_value
                    statistics.append(statistics_row)
        return statistics


# TODO: Remove legend-shape dependencies of legend stuff, then remove
# the legend stuff.


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

        for k, v in updates.items():
            try:
                if k == 'min_value':
                    self.min_value = float(v)
                elif k == 'max_value':
                    self.max_value = float(v)
                elif k == 'steps':
                    self.steps = int(v)
                elif k == 'min_color':
                    self.min_color = Color(v)
                elif k == 'max_color':
                    self.max_color = Color(v)
                elif k == 'too_low_color':
                    self.too_low_color = Color(v)
                elif k == 'too_high_color':
                    self.too_high_color = Color(v)
            except ValueError, e:
                logger.exception('Could not parse one of the colors')
                raise WorkspaceItemError(e)

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
    is_base_layer = models.BooleanField(default=True)

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

    @classmethod
    def extent(cls, key, fallback):
        """ Setting in "xx0,yy0,xx1,yy1" format.

        TODO: test"""
        extent_names = ['left', 'bottom', 'right', 'top']
        extent_list = cls.get(
            key, fallback).split(',')
        extent = dict(
            [(extent_names[i], s.strip())
             for i, s in enumerate(extent_list)])
        return extent


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
