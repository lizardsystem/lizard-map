import datetime
import json
import logging
import random
import string

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Max
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from lizard_security.manager import FilteredManager
from lizard_security.models import DataSet
import jsonfield
import lizard_map.configchecker
import mapnik
import pkg_resources

from lizard_map import dateperiods
from lizard_map import fields
from lizard_map.adapter import AdapterClassNotFoundError
from lizard_map.adapter import adapter_class_names
from lizard_map.adapter import adapter_entrypoint
from lizard_map.adapter import adapter_layer_arguments
from lizard_map.adapter import adapter_serialize
from lizard_map.conf import settings
from lizard_map.exceptions import WorkspaceItemError
from lizard_map.mapnik_helper import point_rule
# Temporary, because fewsjdbc api handler imports this.
from lizard_map.adapter import ADAPTER_ENTRY_POINT
from lizard_map.utility import get_host


ADAPTER_ENTRY_POINT  # Pyflakes...
lizard_map.configchecker  # Pyflakes...

# workspace storage's secret slugs
SECRET_SLUG_CHARS = string.ascii_lowercase
SECRET_SLUG_LENGTH = 8

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

    is_animatable = False

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
                # Only delete if it is saved in the first place.
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

    def _as_new_collage_object(self, obj, collage):
        """Return self as a new object with the same properties except
        collage .

        Used when duplicating CollageStorageItems to
        CollageEditItems and vice versa."""
        delete_fields = ['_state', '_collage_cache', 'collage_id', 'id']

        # Get current data in dict.
        kwargs = self.__dict__
        for delete_me in delete_fields:
            if delete_me in kwargs:
                del kwargs[delete_me]

        # Put data in new object.
        collage_item = obj(**kwargs)
        collage_item.collage = collage
        return collage_item

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

    def has_extent(self):
        """Return true if this workspace item's adapter can
        successfully compute an extent and doesn't have "None" in the
        extent's values."""
        if not hasattr(self, 'adapter') or not hasattr(self.adapter, 'extent'):
            return False

        try:
            extent = self.adapter.extent()
        except:
            # Even if the hard disk is in fact on fire, we don't want to raise
            # an exception here because that may break the whole page.
            logger.exception("Error when calling .extent()")
            return False

        if extent is None:
            return False

        if not isinstance(extent, dict):
            return False

        return None not in extent.values()


class UserSessionMixin(models.Model):
    """For objects that are bound to a user and/or session.
    """
    user = models.ForeignKey(User, null=True, blank=True, unique=True)
    session_key = models.CharField(
        max_length=40, unique=True, blank=True, null=True)

    @classmethod
    def get_using_session(cls, session_key, user):
        """Get your user session object, or return None."""
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

                    return None
                else:
                    result = user_session_object
            except cls.DoesNotExist:
                return None
        return result

    @classmethod
    def create_using_session(cls, session_key, user):
        """Create a new user session object.

        Although this will usually be called only if it doesn't exist
        yet, concurrency means that that's never certain. If it
        happens to already exist, we just return the existing
        object.

        XXX: There is a race condition here still; if two threads /
        requests both call this, it is possible that two objects are
        created for the same user / session_key. The fix is to make
        session_key and user unique_together and catch the resulting
        exception. However, for now the current implementation is
        better than it was already, and as sessions are always created
        when the page is first seen, it is likely that there will only
        be one request at that time."""

        if user.is_authenticated():
            result, created = cls.objects.get_or_create(user=user)
        else:
            result, created = cls.objects.get_or_create(
                session_key=session_key)

        return result

    @classmethod
    def get_or_create(cls, session_key, user):
        """Get your user session object, or create a new one.
        """
        result = cls.get_using_session(session_key, user)
        if result is None:
            result = cls.create_using_session(session_key, user)
        return result

    class Meta:
        abstract = True


class WorkspaceModelMixin(object):
    """Specifics for workspace models.
    """

    is_animatable = False

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

    def wms_layers(self):
        """Getting lizard-wms to work by returning the appropriate values
        used in lizard_map/wms.html. This is a hack in the sense that I
        (Remco Gerlich) don't know what the best place for this function is,
        or whether decoding the json already happens somewhere else."""

        def to_template_data(workspace_item):
            # EJVOS: why this is stored as a JSON string is beyond me...
            adapter_layer = json.loads(workspace_item.adapter_layer_json)
            timepositions = adapter_layer.get('timepositions', '')
            info = json.dumps({
                'timepositions': timepositions
            })

            if workspace_item.adapter_class == ADAPTER_CLASS_WMS:
                # item is located on an external WMS server
                cql_filters_unicode = adapter_layer.get('cql_filters', [])
                cql_filters = json.dumps(
                    [i.encode('utf-8') for i in cql_filters_unicode])

                return {
                    'wms_id': workspace_item.id,
                    'name': workspace_item.name,
                    'url': adapter_layer.get('url', ''),
                    'params': adapter_layer.get('params', '{}'),
                    'options': adapter_layer.get('options', '{}'),
                    'index': workspace_item.index,
                    'is_animatable': 'false',
                    'cql_filters': cql_filters,
                    'info': info,
                }
            else:
                # item is served by our local simulated WMS server
                # using mapnik etc.
                params = json.dumps({
                        'layers': 'lizard:generated_layer_%s'.format(
                            workspace_item.id),
                        })
                options = json.dumps({
                    'transitionEffect': 'resize',
                    'displayInLayerSwitcher': False,
                    'singleTile': True,
                    'isBaseLayer': False,
                    'opacity': 1.0
                })
                if isinstance(workspace_item, WorkspaceStorageItem):
                    url = reverse('lizard_map_workspace_storage_wms', kwargs={
                        'workspace_storage_id': workspace_item.workspace.id,
                        'workspace_item_id': workspace_item.id
                    })
                else:
                    url = reverse(
                        'lizard_map_workspace_edit_wms',
                        kwargs={'workspace_item_id': workspace_item.id})
                return {
                    'wms_id': workspace_item.id,
                    'name': workspace_item.name,
                    'url': url,
                    'params': params,
                    'options': options,
                    'index': workspace_item.index,
                    'info': info,
                }
        return [to_template_data(workspace_item)
                for workspace_item in self.workspace_items.all()
                if workspace_item.visible]


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

    @classmethod
    def get_or_create(cls, session_key, user):
        """Get or create a workspace edit, optionally using a default.

        If user already has a workspace edit, return it. If he hasn't,
        use settings 'default_workspace_anonymous_user' or
        'default_workspace_user', depending on the user's
        is_authorized, to retrieve a stored workspace, copying its
        items to a newly created WorkspaceEdit. If a stored workspace
        isn't found this way, return a new empty workspace edit."""

        workspace_edit = cls.get_using_session(session_key, user)
        if workspace_edit is not None:
            # Already exists
            return workspace_edit

        # Doesn't exist yet -- create it, then optionally copy
        # defaults
        workspace_edit = cls.create_using_session(
            session_key=session_key, user=user)

        if user.is_authenticated():
            stored_workspace_slug = Setting.get(
                'default_workspace_user')
        else:
            stored_workspace_slug = Setting.get(
                'default_workspace_anonymous_user')

        if stored_workspace_slug:
            try:
                workspace_storage = WorkspaceStorage.objects.get(
                    secret_slug=stored_workspace_slug)

                # Found a workspace storage, copy its items
                workspace_edit.load_from_storage(workspace_storage)
            except (WorkspaceStorage.DoesNotExist,
                    WorkspaceStorage.MultipleObjectsReturned) as e:
                logger.warn("Failed to load WorkspaceStorage {0} for user: {1}"
                            .format(stored_workspace_slug, e))

        return workspace_edit

    def save_to_storage(self, name, owner, extent=None):
        """Save this model and workspace_items to Storage.
        """
        workspace_storage, _ = WorkspaceStorage.objects.get_or_create(
            name=name, owner=owner)

        # Delete all existing workspace item storages.
        workspace_storage.workspace_items.all().delete()

        # Add extent to storage, only when specified
        if extent:
            try:
                workspace_storage.x_min = extent['left']
                workspace_storage.x_max = extent['right']
                workspace_storage.y_min = extent['bottom']
                workspace_storage.y_max = extent['top']
                workspace_storage.extent_is_set = True
            except:
                logger.exception(
                    'Failed to store extent in workspace. Skipping...')

        # Init secret slug
        workspace_storage.init_secret_slug()
        workspace_storage.save()

        # Create new workspace items.
        for workspace_edit_item in self.workspace_items.filter(visible=True):
            workspace_storage_item = workspace_edit_item.as_storage(
                workspace=workspace_storage)
            workspace_storage_item.save()

        # Return slug so it can be shown
        return workspace_storage.secret_slug

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

    def in_workspace(self, workspace_item_name):
        """Check if the workspace contains an item with the given
        workspace_item_name."""

        return (self.workspace_items.filter(name=workspace_item_name)
                .count()) > 0

    def toggle_workspace_item(self, name, adapter_class, adapter_layer_json):
        """If the given workspace item is present in this workspace
        edit, remove it. If it's not, add it. Used by the
        workspace_item_toggle view, moved here because it is also
        useful for non-view code.

        Returns a boolean indicating whether the item was added."""

        # Find out if it is already present.
        existing_workspace_items = self.workspace_items.filter(
            adapter_class=adapter_class,
            adapter_layer_json=adapter_layer_json)
        if existing_workspace_items.count() == 0:
            self.add_workspace_item(
                name, adapter_class, adapter_layer_json, skip_test=True)
            return True
        else:
            # Delete existing items
            logger.debug("Deleting existing workspace-item.")
            existing_workspace_items.delete()
            return False

    def add_workspace_item(
        self, name, adapter_class, adapter_layer_json, skip_test=False):
        """Add a workspace item if it doesn't exist yet in this
        workspace_edit. If it does, do nothing.

        If skip_test is True, it is assumed that the test was already
        done and the item isn't present."""
        if not skip_test:
            # Find out if it is already present.
            if self.workspace_items.filter(
                adapter_class=adapter_class,
                adapter_layer_json=adapter_layer_json).exists():
                return

        # Create new
        logger.debug("Creating new workspace-item.")
        if self.workspace_items.count() > 0:
            max_index = self.workspace_items.aggregate(
                Max('index'))['index__max']
        else:
            max_index = 10

        self.workspace_items.create(
            adapter_class=adapter_class,
            index=max_index + 10,
            adapter_layer_json=adapter_layer_json,
            name=name[:80])


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
    owner = models.ForeignKey(User, null=True, blank=True)
    secret_slug = models.CharField(max_length=16, null=True)
    extent_is_set = models.BooleanField(default=False)
    sidebar_is_collapsed = models.BooleanField(default=False)
    rightbar_is_collapsed = models.BooleanField(default=True)
    index = models.IntegerField(default=100)
    private = models.BooleanField(
        default=True, help_text=_("When checked, this workspace is only "
                                   "available for logged-in users."))
    data_set = models.ForeignKey(DataSet,
                                 null=True,
                                 blank=True)

    supports_object_permissions = True
    objects = FilteredManager()

    class Meta:
        ordering = ('index', )


    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.owner)

    def init_secret_slug(self):
        if self.secret_slug is None:
            self.secret_slug = ''.join(random.choice(SECRET_SLUG_CHARS)
                                       for i in range(SECRET_SLUG_LENGTH))


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


class CollageStorage(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(User, null=True, blank=True)
    secret_slug = models.CharField(max_length=16, null=True)
    data_set = models.ForeignKey(DataSet,
                                 null=True,
                                 blank=True)

    supports_object_permissions = True
    objects = FilteredManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.owner)

    def init_secret_slug(self):
        if self.secret_slug is None:
            self.secret_slug = ''.join(random.choice(SECRET_SLUG_CHARS)
                                       for i in range(SECRET_SLUG_LENGTH))


class CollageEdit(UserSessionMixin):
    """
    User selection of map locations.
    """

    def data_in_collage(self, adapter_class, adapter_layer_json,
                        name, identifier):
        """Check if an item with the same data already exists in the
        collage."""
        adapter_layer_json = json.loads(adapter_layer_json)
        for item in (self.collage_items
            .filter(adapter_class=adapter_class)
            .filter(name=name)):
            # Easiest way to compare identifiers?
            if item.identifier == identifier and \
               json.loads(item.adapter_layer_json) == adapter_layer_json:
                return True
        return False

    def save_to_storage(self, name, owner):
        """Save this model and collage_items to Storage.
        """
        collage_storage, _ = CollageStorage.objects.get_or_create(
            name=name, owner=owner)

        # Delete all existing collage item storages.
        collage_storage.collage_items.all().delete()

        # Init secret slug
        collage_storage.init_secret_slug()
        collage_storage.save()

        # Create new collage items.
        for collage_edit_item in self.collage_items.filter(visible=True):
            collage_storage_item = collage_edit_item.as_storage(
                collage=collage_storage)
            collage_storage_item.save()

        # Return slug so it can be shown
        return collage_storage.secret_slug

    def load_from_storage(self, collage_storage):
        """Load model and collage_items from Storage.
        """
        # Delete all existing collage items.
        self.collage_items.all().delete()
        # Create new collage items.
        for collage_storage_item in collage_storage.collage_items.all():
            collage_edit_item = collage_storage_item.as_edit(
                collage=self)
            collage_edit_item.save()


class StatisticsMixin(models.Model):
    """
    Statistics mixin.
    """
    AGGREGATION_PERIOD_CHOICES = (
        (dateperiods.ALL, _('all')),
        (dateperiods.YEAR, _('year')),
        (dateperiods.QUARTER, _('quarter')),
        (dateperiods.MONTH, _('month')),
        (dateperiods.WEEK, _('week')),
        (dateperiods.DAY, _('day')),
        )

    # Boundary value for statistics.
    boundary_value = models.FloatField(blank=True, null=True)
    # Percentile value for statistics.
    percentile_value = models.FloatField(blank=True, null=True)
    # Restrict_to_month is used to filter the data.
    restrict_to_month = models.IntegerField(blank=True, null=True)
    aggregation_period = models.IntegerField(
        choices=AGGREGATION_PERIOD_CHOICES, default=dateperiods.ALL)

    class Meta:
        abstract = True


class CollageStorageItem(WorkspaceItemMixin, StatisticsMixin):
    collage = models.ForeignKey(
        CollageStorage,
        related_name='collage_items')
    identifier = jsonfield.JSONField()

    class Meta:
        ordering = ('name', )

    def as_edit(self, collage):
        """Return self as a CollageEditItem."""
        return self._as_new_collage_object(CollageEditItem, collage)


class CollageEditItem(WorkspaceItemMixin, StatisticsMixin):
    collage = models.ForeignKey(
        CollageEdit,
        related_name='collage_items')
    identifier = jsonfield.JSONField()

    class Meta:
        ordering = ('name', )

    def html(self, identifiers=None, is_collage=False, request=None):
        if identifiers is None:
            identifiers = [self.identifier, ]
        try:
            return self.adapter.html(
                identifiers=identifiers,
                layout_options={'is_collage': is_collage, 'request': request})
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

    # The following methods are used from the collage_edit_detail
    # page and control which things are shown on that page.
    @property
    def data_description(self):
        """Title to show above this bit of data on the collage page."""
        return self.adapter.collage_detail_data_description(self.identifier)

    @property
    def collage_detail_edit_action(self):
        """Which edit action to show on the collage detail page. Currently
        the only working option in collage_edit_detail is 'graph'. If this
        data can't be edited on the collage detail page, return None.
        Calls 'collage_detail_edit_action' in the adapter."""
        return self.adapter.collage_detail_edit_action(self.identifier)

    @property
    def collage_detail_show_edit_block(self):
        return self.adapter.collage_detail_show_edit_block(self.identifier)

    @property
    def collage_detail_show_statistics_block(self):
        return self.adapter.collage_detail_show_statistics_block(
            self.identifier)

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
        periods = dateperiods.calc_aggregation_periods(start_date, end_date,
                                           self.aggregation_period)
        statistics = []
        for period_start_date, period_end_date in periods:
            if not self.restrict_to_month or (
                self.aggregation_period != dateperiods.MONTH) or (
                self.aggregation_period == dateperiods.MONTH and
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
                    statistics_row['period'] = dateperiods.fancy_period(
                        period_start_date, period_end_date,
                        self.aggregation_period)
                    statistics_row['boundary_value'] = self.boundary_value
                    statistics_row['percentile_value'] = self.percentile_value
                    statistics.append(statistics_row)
        return statistics

    def as_storage(self, collage):
        """Return self as a CollageStorageItem."""
        return self._as_new_collage_object(CollageStorageItem, collage)


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

    default_color = fields.ColorField()
    min_color = fields.ColorField()
    max_color = fields.ColorField()
    too_low_color = fields.ColorField()
    too_high_color = fields.ColorField()

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
        return fields.legend_values(
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
                    self.min_color = fields.Color(v)
                elif k == 'max_color':
                    self.max_color = fields.Color(v)
                elif k == 'too_low_color':
                    self.too_low_color = fields.Color(v)
                elif k == 'too_high_color':
                    self.too_high_color = fields.Color(v)
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
    LAYER_TYPE_TMS = 4

    LAYER_TYPE_CHOICES = (
        (LAYER_TYPE_GOOGLE, 'GOOGLE'),
        (LAYER_TYPE_OSM, 'OSM'),
        (LAYER_TYPE_WMS, 'WMS'),
        (LAYER_TYPE_TMS, 'TMS'),
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

    # The default map URL used as background map, must be
    # BackgroundMap.LAYER_TYPE_OSM.
    DEFAULT_OSM_LAYER_URL = (
        'http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png')

    name = models.CharField(max_length=20)
    index = models.IntegerField(default=100)
    default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    is_base_layer = models.BooleanField(default=True)
    is_single_tile = models.BooleanField(default=False)

    layer_type = models.IntegerField(choices=LAYER_TYPE_CHOICES)
    google_type = models.IntegerField(
        choices=GOOGLE_TYPE_CHOICES,
        null=True, blank=True,
        help_text='Choose map type in case of GOOGLE maps.')
    layer_url = models.CharField(
        max_length=200,
        null=True, blank=True,
        help_text='Tile url for use with OSM or WMS or TMS',
        default='http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png')
    layer_names = models.TextField(
        null=True, blank=True,
        help_text='Fill in layer names in case of WMS or TMS')

    class Meta:
        ordering = ('index', )

    def __unicode__(self):
        return '%s' % self.name

    @classmethod
    def default_maps(cls):
        """Return the default background maps, currently only OSM."""
        return [
            cls(
                name='Default map',
                default=True,
                active=True,
                layer_type=cls.LAYER_TYPE_OSM,
                layer_url=cls.DEFAULT_OSM_LAYER_URL)]


class Setting(models.Model):
    """
    Global settings.

    Available keys with default values:
    projection 'EPSG:900913'
    display_projection 'EPSG:4326'
    googlemaps_api_key
    """

    @classmethod
    def CACHE_KEY(cls):
        return 'lizard-map.Setting::%s' % (get_host(), )

    key = models.CharField(max_length=40, unique=True)
    value = models.CharField(max_length=200)

    def __unicode__(self):
        return '%s = %s' % (self.key, self.value)

    @classmethod
    def get(cls, key, default=None):
        """
        Return value from given key.

        If the key does not exist, return the default. Caches the whole
        Setting table.

        Using the `default` argument is *deprecated* and it isn't
        used. Defaults for several Settings are defined in conf.py,
        and could be overridden in settings.py.

        If there is no default for a setting, this returns None.
        """

        # Caching.
        allsettings = cache.get(cls.CACHE_KEY())  # Dict
        if allsettings is None:
            allsettings = {}
            for setting in cls.objects.all():
                allsettings[setting.key] = setting.value
            cache.set(cls.CACHE_KEY(), allsettings)

        # Handle default, should be the usual case in Lizard5
        if key not in allsettings:
            if default is not None:
                # Only warn if None is not a fine value: otherwise we'd warn
                # about a setting that doesn't *need* to be set.
                logger.warn(
                    'Setting "%s" got a default "%s", this is deprecated.'
                    % (key, default))

            return getattr(
                settings, 'LIZARD_MAP_DEFAULT_{}_SETTING'.format(
                    key.upper()), None)

        # Return desired result.
        return allsettings[key]

    @classmethod
    def get_dict(cls, key, default=None):
        """
        Return {key: value} for given key
        """
        return {key: cls.get(key, default)}

    @classmethod
    def extent(cls, key, fallback=None):
        """ Setting in "xx0,yy0,xx1,yy1" format.

        Fallback is *deprecrated* and ignored.
        """
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
                 sender.CACHE_KEY())
    cache.delete(sender.CACHE_KEY())


post_save.connect(setting_post_save_delete, sender=Setting)
post_delete.connect(setting_post_save_delete, sender=Setting)
