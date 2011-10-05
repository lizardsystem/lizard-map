import StringIO
import datetime

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.template import RequestContext
from django.utils import simplejson as json
from django.views.decorators.cache import never_cache
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.views.generic.base import View
import Image
import csv
import logging
import mapnik
import urllib2

#from lizard_map.daterange import deltatime_range
#from lizard_map.daterange import store_timedelta_range
from lizard_map import coordinates
from lizard_map.adapter import adapter_entrypoint
from lizard_map.adapter import adapter_layer_arguments
from lizard_map.adapter import parse_identifier_json
from lizard_map.animation import AnimationSettings
from lizard_map.animation import slider_layout_extra
from lizard_map.coordinates import DEFAULT_OSM_LAYER_URL
from lizard_map.dateperiods import ALL
from lizard_map.dateperiods import MONTH
from lizard_map.daterange import compute_and_store_start_end
from lizard_map.daterange import current_period
from lizard_map.daterange import current_start_end_dates
from lizard_map.forms import CollageForm
from lizard_map.forms import CollageAddForm
from lizard_map.forms import CollageItemEditorForm
from lizard_map.forms import DateRangeForm
from lizard_map.forms import EditForm
from lizard_map.forms import EmptyForm
from lizard_map.forms import WorkspaceLoadForm
from lizard_map.forms import WorkspaceSaveForm
from lizard_map.models import BackgroundMap
from lizard_map.models import CollageEdit
from lizard_map.models import CollageEditItem
from lizard_map.models import Setting
from lizard_map.models import WorkspaceEdit
from lizard_map.models import WorkspaceStorage
from lizard_map.utility import analyze_http_user_agent
from lizard_ui.models import ApplicationScreen
from lizard_ui.views import ViewContextMixin


CUSTOM_LEGENDS = 'custom_legends'
MAP_LOCATION = 'map_location'
MAP_BASE_LAYER = 'map_base_layer'  # The selected base layer
CRUMBS_HOMEPAGE = {'name': 'home', 'title': 'hoofdpagina', 'url': '/'}
TIME_BETWEEN_VIDEO_POPUP = datetime.timedelta(days=1)


DEFAULT_START_EXTENT = '-14675, 6668977, 1254790, 6964942'
DEFAULT_PROJECTION = 'EPSG:900913'


logger = logging.getLogger(__name__)


class GoogleTrackingMixin(object):
    """
    Google tracking code.
    """
    def google_tracking_code():
        try:
            return settings.GOOGLE_TRACKING_CODE
        except AttributeError:
            return None


class WorkspaceMixin(object):
    """Add workspace and map variables.
    """
    javascript_click_handler = 'popup_click_handler'

    def workspace(self):
        """Implement a function that returns a workspace-storage,
        workspace-edit or other workspace."""
        pass

    def animation_slider(self):
        """Add animation slider? Default: none. Calculate each time,
        because the datetime settings could be changed in the
        meanwhile."""
        animation_slider = None
        if self.workspace().is_animatable:
            animation_slider = AnimationSettings(self.request).info()
        return animation_slider

    def javascript_hover_handler(self):
        if not hasattr(self, '_javascript_hover_handler'):
            self._javascript_hover_handler = Setting.get(
                'javascript_hover_handler', None)
        return self._javascript_hover_handler


class WorkspaceEditMixin(WorkspaceMixin):
    def workspace_edit(self):
        """Return your workspace"""
        if not hasattr(self, '_workspace_edit'):
            self._workspace_edit = WorkspaceEdit.get_or_create(
                self.request.session.session_key, user=self.request.user)
        return self._workspace_edit

    def workspace(self):
        return self.workspace_edit()


class MapMixin(object):
    """All map stuff
    """
    # def maps(self):
    #     # Add map variables.
    #     self.map_variables = map_variables(self.request)
    #     return ""

    def max_extent(self):
        s = Setting.extent(
            'max_extent',
            '-20037508.34, -20037508.34, 20037508.34, 20037508.34')
        return s

    def start_extent(self):
        map_location = Setting.extent(
            'start_extent',
            DEFAULT_START_EXTENT)
        if MAP_LOCATION in self.request.session:
            map_location = self.request.session[MAP_LOCATION]
            logger.debug('Fetched map coordinates from session: '
                         '%s' % (map_location))
        return map_location

    def projection(self):
        return Setting.get('projection', DEFAULT_PROJECTION)

    def display_projection(self):
        return Setting.get('projection', 'EPSG:4326')

    def googlemaps_api_key(self):
        return Setting.get('projection', '')  # Must be defined

    def base_layer_name(self):
        if MAP_BASE_LAYER in self.request.session:
            return self.request.session[MAP_BASE_LAYER]
        else:
            return ""

    @property
    def maps(self):
        if not hasattr(self, '_maps'):
            self._maps = BackgroundMap.objects.filter(active=True)
        return self._maps

    def has_google(self):
        # For the client side to determine is there is a google map.
        if self.maps.filter(
            layer_type=BackgroundMap.LAYER_TYPE_GOOGLE).count() > 0:

            return True
        else:
            return False

    def background_maps(self):
        if self.maps:
            return self.maps
        else:
            logger.warn("No background maps are active. Taking default.")
            maps = [BackgroundMap(
                name='Default map',
                default=True,
                active=True,
                layer_type=BackgroundMap.LAYER_TYPE_OSM,
                layer_url=DEFAULT_OSM_LAYER_URL), ]

            return maps


class CollageMixin(object):

    def collage_edit(self):
        if not hasattr(self, '_collage_edit'):
            self._collage_edit = CollageEdit.get_or_create(
                self.request.session.session_key, user=self.request.user)
        return self._collage_edit


class DateRangeMixin(object):
    """Date range stuff
    """
    def current_date_range(self):
        date_range = current_start_end_dates(
            self.request, for_form=True)
        date_range.update(
            {'period': current_period(self.request)})
        return date_range

    def date_start_period(self):
        return self.current_date_range()["dt_start"]

    def date_end_period(self):
        return self.current_date_range()["dt_end"]

    def date_range_form(self):
        return DateRangeForm(self.current_date_range())


class AppView(
    WorkspaceEditMixin, CollageMixin, DateRangeMixin,
    ViewContextMixin, MapMixin,
    GoogleTrackingMixin, TemplateView):
    """All-in-one"""
    pass


class WorkspaceStorageListView(
    ViewContextMixin, GoogleTrackingMixin, TemplateView):
    """Show list of storage workspaces."""

    template_name = 'lizard_map/workspace_storage_list.html'

    def workspaces(self):
        return WorkspaceStorage.objects.all()


class WorkspaceStorageView(
    WorkspaceMixin, CollageMixin, DateRangeMixin,
    ViewContextMixin, MapMixin,
    GoogleTrackingMixin, TemplateView):
    """Workspace storage view.

    TODO: "load workspace in my workspace and go there" """
    template_name = 'lizard_map/workspace_storage_detail.html'

    def workspace(self):
        """Return a workspace"""
        if not hasattr(self, '_workspace'):
            self._workspace = WorkspaceStorage.objects.get(
                pk=self.workspace_id)
        return self._workspace

    def get(self, request, *args, **kwargs):
        self.workspace_id = kwargs['workspace_id']
        return super(WorkspaceStorageView, self).get(
            request, *args, **kwargs)


class HomepageView(AppView):
    """
    Homepage view with apps on the left side

    Try to fetch GET parameter 'screen' from url. It points to the
    application_screen_slug.
    """
    template_name = 'lizard_map/app_screen.html'

    def get_context_data(self, **kwargs):
        context = super(HomepageView, self).get_context_data(**kwargs)

        # Application screen slug
        application_screen_slug = kwargs.get('application_screen_slug', None)
        if application_screen_slug is None:
            application_screen_slug = self.request.GET.get('screen', None)
        context['application_screen_slug'] = application_screen_slug

        # Breadcrumbs
        crumbs_prepend = kwargs.get('crumbs_prepend', None)
        if crumbs_prepend is None:
            if application_screen_slug:
                application_screen = get_object_or_404(
                    ApplicationScreen,
                    slug=application_screen_slug)
                crumbs = [application_screen.crumb(), ]
                if application_screen_slug != 'home':
                    # prepend with "home"
                    application_screen_home = get_object_or_404(
                        ApplicationScreen,
                        slug='home')
                    crumbs = [application_screen_home.crumb(), ] + crumbs
            else:
                crumbs = [CRUMBS_HOMEPAGE]
        else:
            crumbs = list(kwargs['crumbs_prepend'])
        context['crumbs'] = crumbs

        return context


##### Edits on workspace ############


# L3
class ActionDialogView(ViewContextMixin, FormView):
    """
    Generic Action Dialog View.

    Input from user is expected as form. Then an action is performed.
    """

    # Used with "GET" or "POST" with invalid form.
    template_name = 'lizard_map/form_workspace_save.html'
    # Used with "POST" with valid form.
    template_name_success = 'lizard_map/form_workspace_save_success.html'
    # Form which is added to the context for your templates.
    form_class = WorkspaceSaveForm  # Define your form

    success_url = './'

    def form_valid_action(self, form):
        """
        Implement your action here.

        Normally return None. If a not-None is returned, that will be
        returned as result.
        """
        pass

    def form_valid(self, form):
        """
        Return rendered template_name_success.
        """
        logger.debug("form is valid")
        result = self.form_valid_action(form)
        if result:
            return result
        return render(
            self.request,
            self.template_name_success,
            self.get_context_data())

    def form_invalid(self, form):
        """
        Return rendered template_name with current form with errors.
        """
        logger.debug("form is invalid")
        html = render_to_string(
            self.template_name, self.get_context_data(form=form),
            context_instance=RequestContext(self.request))
        return HttpResponseBadRequest(html)

    def get(self, request, *args, **kwargs):
        """Added request to initial, so in your form constructor you
        can use request."""
        self.initial.update({'request': request})
        return super(ActionDialogView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Added request to initial, so in your form constructor you
        can use request."""
        self.initial.update({'request': request})
        return super(ActionDialogView, self).post(request, *args, **kwargs)


class WorkspaceSaveView(ActionDialogView):
    template_name = 'lizard_map/form_workspace_save.html'
    template_name_success = 'lizard_map/form_workspace_save_success.html'
    template_name_forbidden = '403.html'
    form_class = WorkspaceSaveForm  # Define your form

    def form_valid_action(self, form):
        """
        Save edit workspace to storage workspace
        """
        logger.debug("Saving stuff...")
        form_data = form.cleaned_data
        # Should be get, else there is nothing to save...
        workspace_edit = WorkspaceEdit.get_or_create(
           self.request.session.session_key, self.request.user)
        # TODO: quota, warning on duplicate names.
        user = self.request.user
        if not user.is_authenticated():
            html = render_to_string(
                self.template_name_forbidden,
                {'message': ('U kunt geen workspace opslaan als U '
                             'niet bent ingelogd.')},
                context_instance=RequestContext(self.request))
            return HttpResponseForbidden(html)
        workspace_edit.save_to_storage(name=form_data['name'], owner=user)


class WorkspaceLoadView(ActionDialogView):
    template_name = 'lizard_map/form_workspace_load.html'
    template_name_success = 'lizard_map/form_workspace_load_success.html'
    form_class = WorkspaceLoadForm  # Define your form

    def form_valid_action(self, form):
        """
        Load storage workspace to edit workspace
        """
        logger.debug("Loading stuff...")
        form_data = form.cleaned_data

        workspace_edit = WorkspaceEdit.get_or_create(
           self.request.session.session_key, self.request.user)
        # TODO: check permissions.
        workspace_storage = WorkspaceStorage.objects.get(pk=form_data['id'])
        workspace_edit.load_from_storage(workspace_storage)


class DateRangeView(DateRangeMixin, WorkspaceEditMixin, ActionDialogView):
    template_name = 'lizard_map/box_daterange.html'
    template_name_success = template_name
    form_class = DateRangeForm  # Define your form

    reload_screen_after = False  # Default.

    def form_valid_action(self, form):
        """
        Update date range
        """
        logger.debug("Updating date range...")
        date_range = form.cleaned_data
        compute_and_store_start_end(self.request.session, date_range)

    def get(self, request, *args, **kwargs):
        self.reload_screen_after = request.GET.__contains__(
            'reload_screen_after')
        return super(DateRangeView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.reload_screen_after = request.GET.__contains__(
            'reload_screen_after')
        return super(DateRangeView, self).post(request, *args, **kwargs)


class CollageItemEditorView(ActionDialogView):
    """
    Popup per collage item for adjustments in the graph.

    TODO: make prettier. Split global settings and per collage-item settings.
    """
    template_name = 'lizard_map/box_collage_item_editor.html'
    template_name_success = 'lizard_map/box_collage_item_editor_success.html'
    form_class = CollageItemEditorForm

    def get(self, request, *args, **kwargs):
        self.collage_item_id = kwargs['collage_item_id']

        self.collage_item = CollageEditItem.objects.get(
            pk=self.collage_item_id)
        self.initial.update(self.collage_item.form_initial())
        return super(CollageItemEditorView, self).get(
            request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.collage_item_id = kwargs['collage_item_id']
        return super(CollageItemEditorView, self).post(
            request, *args, **kwargs)

    @transaction.commit_on_success
    def form_valid_action(self, form):
        """
        Change collage-item(s) accordingly

        This is a little tricky: some fields are for the graph itself,
        like title or y_min. Since the graph is used for multiple
        collage-items, all those items are updated.

        TODO: unit test.
        TODO: unit test.
        TODO: unit test.
        """

        # Fields that must be applied to all group items
        group_fields = {'title': None,
                        'y_min': None,
                        'y_max': None,
                        'x_label': None,
                        'y_label': None,
                        'aggregation_period': None,
                        'restrict_to_month': None}

        data = form.cleaned_data
        # The collage item being edited.
        collage_item = CollageEditItem.objects.get(pk=self.collage_item_id)

        # Select group to update the parameters.
        # Note: we also update invisible items
        grouped_collage_items, collage_item_group = group_collage_items(
            CollageEditItem.objects.all())

        grouping_hint = collage_item_group[collage_item.id]
        collage_items = grouped_collage_items[grouping_hint]

        # Loop all collage_items in group
        for single_collage_item in collage_items:
            # Model field for every collage item.
            single_collage_item.aggregation_period = data.get(
                'aggregation_period', ALL)

            identifier = single_collage_item.identifier
            new_layout = identifier.get('layout', {})

            # We have two instances of collage_item, only editing (and
            # saving) the one in the group list.
            if single_collage_item.id == collage_item.id:
                single_collage_item.boundary_value = data['boundary_value']
                single_collage_item.percentile_value = data['percentile_value']

            # Layout properties
            for k, v in data.items():
                # Check per field if it is a group field.
                if (single_collage_item.id == collage_item.id or
                    k in group_fields):

                    # Everything resulting in True must be saved
                    # 0.0 must be saved
                    # u'' must be deleted
                    # False must be deleted
                    if v or isinstance(v, float):
                        new_layout[k] = v
                    else:
                        if k in new_layout:
                            del new_layout[k]

            # Restrict to month option which is currently used in NHI only.
            if 'aggregation_period' in new_layout:
                if int(new_layout['aggregation_period']) != MONTH:
                    # Should not be there, but you never know.
                    if 'restrict_to_month' in new_layout:
                        del new_layout['restrict_to_month']
            if ('restrict_to_month' in new_layout and
                (new_layout['restrict_to_month'] == '0' or
                new_layout['restrict_to_month'] is None)):

                del new_layout['restrict_to_month']

            identifier['layout'] = new_layout
            single_collage_item.identifier = identifier
            single_collage_item.save()


# L3
@never_cache
def workspace_item_reorder(
    request, workspace_edit=None, workspace_items_order=None):
    """reorder workspace items.

    reorders workspace_item[] in new order.
    """
    if workspace_edit is None:
        workspace_edit = WorkspaceEdit.get_or_create(
            request.session.session_key, request.user)
    if workspace_items_order is None:
        workspace_items_order = dict([
                (workspace_item_id, index * 10) for
                index, workspace_item_id in enumerate(
                    request.POST.getlist('workspace-items[]'))])

    for workspace_item in workspace_edit.workspace_items.all():
        workspace_item.index = workspace_items_order.get(
            str(workspace_item.pk), 1000)
        print workspace_item.id, workspace_item.index
        workspace_item.save()
    return HttpResponse("")


# L3
@never_cache
def workspace_item_toggle(
    request,
    workspace_edit=None):

    """Toggle workspace item in workspace.

    This means: if the workspace-item is already in the workspace,
    remove it. If it is not in the workspace, add it.

    Return if it is added (True), or removed (False)
    """

    # For testing, workspace_edit can be given.
    if workspace_edit is None:
        workspace_edit = WorkspaceEdit.get_or_create(
            request.session.session_key, request.user)

    name = request.POST['name']
    adapter_class = request.POST['adapter_class']
    adapter_layer_json = request.POST['adapter_layer_json']

    # Find out if it is already present.
    existing_workspace_items = workspace_edit.workspace_items.filter(
        adapter_class=adapter_class,
        adapter_layer_json=adapter_layer_json)
    if existing_workspace_items.count() == 0:
        # Create new
        logger.debug("Creating new workspace-item.")
        if workspace_edit.workspace_items.count() > 0:
            max_index = workspace_edit.workspace_items.aggregate(
                Max('index'))['index__max']
        else:
            max_index = 10

        workspace_edit.workspace_items.create(
            adapter_class=adapter_class,
            index=max_index + 10,
            adapter_layer_json=adapter_layer_json,
            name=name[:80])
        just_added = True
    else:
        # Delete existing items
        logger.debug("Deleting existing workspace-item.")
        existing_workspace_items.delete()
        just_added = False

    return HttpResponse(json.dumps(just_added))


# L3
@never_cache
def workspace_edit_item(
    request, workspace_edit=None, workspace_item_id=None, visible=None):
    """Sets (in)visibility of a workspace_item

    workspace_edit is added for testing
    """
    if workspace_edit is None:
        workspace_edit = WorkspaceEdit.get_or_create(
            request.session.session_key, request.user)
    if workspace_item_id is None:
        workspace_item_id = request.POST['workspace_item_id']
    workspace_item = workspace_edit.workspace_items.get(
        pk=workspace_item_id)
    if visible is None:
        visible = request.POST.get('visible', None)
    if visible:
        lookup = {'true': True, 'false': False}
        workspace_item.visible = lookup[visible]
    workspace_item.save()

    return HttpResponse("")


# L3
@never_cache
def workspace_item_delete(request, workspace_edit=None, object_id=None):
    """delete workspace item from workspace

    returns true if >= 1 items were deleted

    if workspace_item_id is not provided, it tries to get the variable
    workspace_item_id from the request.POST
    """
    if object_id is None:
        object_id = request.POST['object_id']
    if workspace_edit is None:
        workspace_edit = WorkspaceEdit.get_or_create(
            request.session.session_key, request.user)
    workspace_items = workspace_edit.workspace_items.filter(pk=object_id)
    deleted = True if workspace_items.count() > 0 else False
    workspace_items.delete()

    return HttpResponse(json.dumps(deleted))


# #To be updated/tested
# @never_cache
# def workspace_item_extent(request, workspace_item_id=None):
#     """Returns extent for the workspace in json.

#     Transform to correct client-side projection, then return coordinates.
#     """
#     workspace_item_id = request.GET['workspace_item_id']
#     workspace_item = get_object_or_404(WorkspaceItem, pk=workspace_item_id)
#     extent = workspace_item.adapter.extent()

#     srs = Setting.get('projection', DEFAULT_PROJECTION)
#     extent_converted['east'], extent_converted['north'] = google_to_srs(
#         extent['east'], extent['north'], srs)
#     extent_converted['west'], extent_converted['south'] = google_to_srs(
#         extent['west'], extent['south'], srs)

#     return HttpResponse(json.dumps(extent_converted))


def popup_json(found, popup_id=None, hide_add_snippet=False, request=None):
    """Return html with info on list of 'found' objects.

    Optionally give pagenumber (starts at 0). If omitted, just join
    everything.

    found: list of dictionaries {'distance': ..., 'timeserie': ...,
    'workspace_item': ..., 'identifier': ...}.

    Note: identifier must be a dict. {'id': the_real_id}.

    Result format (used by the javascript popup function):

    result = {'id': popup_id,
              'x': x_found,
              'y': y_found,
              'html': result_html,
              'big': big_popup,
              }
    """

    html = {}
    # x_found = None
    # y_found = None

    # Regroup found list of objects into workspace_items.
    display_groups = {}
    display_group_order = []
    for display_object in found:
        workspace_item = display_object['workspace_item']
        if workspace_item.id not in display_groups:
            display_groups[workspace_item.id] = []
        display_groups[workspace_item.id].append(display_object)
        if workspace_item.id not in display_group_order:
            display_group_order.append(workspace_item.id)

    if len(display_groups) > 1:
        big_popup = True
    else:
        big_popup = False

    # Now display them.
    for workspace_item_id, display_group in display_groups.items():
        # There MUST be at least one item in the group
        workspace_item = display_group[0]['workspace_item']

        add_snippet = True

        try:
            identifiers = [display_object['identifier']
                           for display_object in display_group]
        except:
            logger.critical(
                "No 'identifier' found in a display_object. Perhaps an "
                "incorrect shapefile?")
            identifiers = None
        if identifiers is None:
            continue

        # Passing the request object as a layout_option is a bit of a hack,
        # but for some use cases we really need access to it in the html()
        # method of a WorkspaceItemAdapter, which unfortunately is
        # lacking a **kwargs at this moment.

        html_per_workspace_item = workspace_item.adapter.html(
            identifiers=identifiers,
            layout_options={'add_snippet': add_snippet,
                            'legend': True,
                            'request': request},
            )

        # if 'google_coords' in display_object:
        #     x_found, y_found = display_object['google_coords']
        html[workspace_item.id] = html_per_workspace_item

    result_html = [html[index] for index in display_group_order][:3]

    if popup_id is None:
        popup_id = 'popup-id'
    result = {'id': popup_id,
              # 'x': x_found,
              # 'y': y_found,
              'html': result_html,
              'big': big_popup,
              }
    return HttpResponse(json.dumps(result))


def group_collage_items(collage_items):
    """
    Group collage items.

    The grouping is done automagically by adapter property "grouping
    hint", or adapter/adapter_layer_arguments by creating collage
    items with extra property "identifiers".

    TODO: test
    """
    # for collage_item in collage_items:
    #     collage_item.identifiers = [collage_item.identifier, ]

    # Identifiers by grouping hint. Content is a list with collage
    # items.
    grouped_collage_items = {}
    collage_item_group = {}  # For each collage_item_id: which grouping_hint?

    for collage_item in collage_items:
        grouping_hint = collage_item.grouping_hint
        if grouping_hint not in grouped_collage_items:
            grouped_collage_items[grouping_hint] = []
        grouped_collage_items[grouping_hint].append(
            collage_item)
        collage_item_group[collage_item.id] = grouping_hint

    return grouped_collage_items, collage_item_group


# Updated for L3.
def popup_collage_json(collage_items, popup_id, request=None):
    """
    Display collage. Each item in a separate tab.
    """

    html = []
    big_popup = True

    grouped_collage_items, _ = group_collage_items(collage_items)
    for collage_items in grouped_collage_items.values():
        collage_item = collage_items[0]  # Each group always has items.
        identifiers = [collage_item.identifier for
                       collage_item in collage_items]
        html.append(
            collage_item.html(identifiers=identifiers, is_collage=True))

    result = {'id': popup_id,
              'html': html,
              'big': big_popup,
              }
    return HttpResponse(json.dumps(result))


# Collages stuff


# L3.
@never_cache
def collage_popup(request,
                  collage_id=None,
                  collage_item_id=None,
                  template='lizard_map/collage.html'):
    """Render page with collage item(s) in popup format
    """
    collage = CollageEdit.get_or_create(
        request.session.session_key, request.user)
    popup_id = 'popup-collage'

    collage_items = collage.collage_items.filter(visible=True)

    # This item is filled when clicking on a single collage item.
    if collage_item_id is not None:
        collage_items = collage_items.filter(pk=collage_item_id)

    # Only one collage popup allowed, also check jquery.workspace.js
    return popup_collage_json(
        collage_items,
        popup_id=popup_id,
        request=request)


# TODO: Update to L3
def legend_edit(request):
    """Updates a session legend.

    POST parameters:
    name
    min_value (optional)
    max_value (optional)
    steps (optional)
    min_color (optional): format ...
    max_color (optional)
    too_low_color (optional)
    too_high_color (optional)

    request['session']['custom_legends'][<name>] = {..}
    """

    # Get new legend from post parameters.
    options = ['min_value', 'max_value', 'steps',
               'min_color', 'max_color', 'too_low_color',
               'too_high_color']

    name = request.POST['name']
    new_legend = {}
    for option in options:
        value = request.POST.get(option, None)
        if value:
            new_legend[option] = value

    # Update session data with new obtained legend.
    custom_legends = request.session.get(CUSTOM_LEGENDS, {})
    custom_legends[name] = new_legend

    request.session[CUSTOM_LEGENDS] = custom_legends

    return HttpResponse('')


"""
Map stuff
"""


def wms(request, workspace_storage_id=None):
    """Return PNG as WMS service for given workspace_edit or
    workspace_storage.

    if workspace_storage_id is not provided, it will take your own
    WorkspaceEdit.
    """

    if workspace_storage_id is None:
        workspace = WorkspaceEdit.get_or_create(
            request.session.session_key, request.user)
    else:
        workspace = get_object_or_404(
            WorkspaceStorage, pk=workspace_storage_id)

    # WMS standard parameters
    width = int(request.GET.get('WIDTH'))
    height = int(request.GET.get('HEIGHT'))
    layers = request.GET.get('LAYERS')
    layers = [layer.strip() for layer in layers.split(',')]
    bbox = request.GET.get('BBOX')
    bbox = tuple([float(i.strip()) for i in bbox.split(',')])
    srs = request.GET.get('SRS')
    # TODO: check that they're not none

    # Map settings
    mapnik_map = mapnik.Map(width, height)
    # Setup mapnik srs.
    mapnik_map.srs = coordinates.srs_to_mapnik_projection[srs]
    mapnik_map.background = mapnik.Color('transparent')
    #m.background = mapnik.Color('blue')

    workspace_items = workspace.workspace_items.filter(visible=True).reverse()
    for workspace_item in workspace_items:
        logger.debug("Drawing layer for %s..." % workspace_item)
        try:
            layers, styles = workspace_item.adapter.layer(
                layer_ids=layers,
                request=request)
            layers.reverse()  # first item should be drawn on top (=last)
            for layer in layers:
                mapnik_map.layers.append(layer)
            for name in styles:
                mapnik_map.append_style(name, styles[name])
        except:
            # This part may NEVER crash. Layers from workspace items
            # should prevent crashing themselves, but you never know.
            logger.exception("Error in drawing layer for %s" % workspace_item)

    #Zoom and create image
    logger.debug("Zooming to box...")
    mapnik_map.zoom_to_box(mapnik.Envelope(*bbox))
    # mapnik_map.zoom_to_box(layer.envelope())
    img = mapnik.Image(width, height)
    logger.debug("Rendering map...")
    mapnik.render(mapnik_map, img)
    http_user_agent = request.META.get('HTTP_USER_AGENT', '')

    logger.debug("Converting image to rgba...")
    rgba_image = Image.fromstring('RGBA', (width, height), img.tostring())
    buf = StringIO.StringIO()
    if 'MSIE 6.0' in http_user_agent:
        imgPIL = rgba_image.convert('P')
        imgPIL.save(buf, 'png', transparency=0)
    else:
        rgba_image.save(buf, 'png')
    buf.seek(0)
    response = HttpResponse(buf.read())
    response['Content-type'] = 'image/png'
    return response


def search(workspace, google_x, google_y, radius):
    """Search workspace for given coordinates.

    Return a list of found results in "adapter.search" dictionary
    format.
    """
    found = []

    for workspace_item in workspace.workspace_items.filter(
        visible=True):

        try:
            search_results = workspace_item.adapter.search(
                google_x, google_y, radius=radius)
            found += search_results
        except:
            logger.exception(
                "Crashed while calling search on %s" %
                workspace_item)
    return found


# L3
def search_coordinates(request, workspace_storage_id=None, format='popup'):
    """searches for objects near GET x,y,radius returns json_popup of
    results.

    GET parameter user_workspace_id: a workspace-edit that is
    currently shown.

    Optional GET parameter srs, if omitted, assume google.

    Format: 'popup', 'name'
    """

    # workspace_manager = WorkspaceManager(request)
    # workspace_collections = workspace_manager.load_or_create()

    # xy params from the GET request.
    x = float(request.GET.get('x'))
    y = float(request.GET.get('y'))
    # TODO: convert radius to correct scale (works now for google + rd)
    radius = float(request.GET.get('radius'))
    radius_search = radius
    if 'HTTP_USER_AGENT' in request.META:
        analyzed_user_agent = analyze_http_user_agent(
            request.META['HTTP_USER_AGENT'])
        # It's more difficult to point with your finger than with the mouse.
        if analyzed_user_agent['device'] == 'iPad':
            radius_search = radius_search * 3
    srs = request.GET.get('srs')
    google_x, google_y = coordinates.srs_to_google(srs, x, y)

    if workspace_storage_id:
        workspace = WorkspaceStorage.objects.get(pk=workspace_storage_id)
    else:
        user_workspace_id = request.GET.get('user_workspace_id', None)
        workspace = WorkspaceEdit.objects.get(pk=user_workspace_id)

    found = search(workspace, google_x, google_y, radius)

    if found:
        # ``found`` is a list of dicts {'distance': ..., 'timeserie': ...}.
        found.sort(key=lambda item: item['distance'])
        if format == 'name':
            result = {}
            result['name'] = found[0]['name']
            # x, y = coordinates.google_to_srs(google_x, google_y, srs)
            # result['x'] = x
            # result['y'] = y

            # For the x/y we use the original x/y value to position
            # the popup to the lower right of the cursor to prevent
            # click propagation problems.
            result['x'] = x + (radius / 10)
            result['y'] = y - (radius / 10)
            return HttpResponse(json.dumps(result))
        else:
            # default: as popup
            return popup_json(found, request=request)
    else:
        return popup_json([], request=request)


class CollageDetailView(
    CollageMixin, DateRangeMixin, ViewContextMixin, TemplateView):
    """
    Shows "my collage" as big page.
    """
    template_name = 'lizard_map/collage_edit_detail.html'
    hide_statistics = False

    def grouped_collage_items(self):
        """A grouped collage item is a collage item with property
        "identifiers": a list of identifiers """
        collage_items, _ = group_collage_items(
            self.collage_edit().collage_items.filter(visible=True))

        return collage_items

    def get(self, request, *args, **kwargs):
        self.hide_statistics = request.GET.get('hide_statistics', False)

        return super(CollageDetailView, self).get(request, *args, **kwargs)


class CollageStatisticsView(
    ViewContextMixin, TemplateView):
    """
    Shows statistics for collage items.
    """
    template_name = 'lizard_map/box_statistics.html'
    collage_items = None

    def get(self, request, *args, **kwargs):
        collage_item_ids = request.GET.getlist('collage_item_id')
        self.collage_items = CollageEditItem.objects.filter(
            id__in=collage_item_ids)

        return super(CollageStatisticsView, self).get(request, *args, **kwargs)


class CollageView(CollageMixin, ActionDialogView):
    """
    Add collage item by coordinates
    """
    template_name = 'lizard_map/box_collage.html'
    template_name_success = template_name
    form_class = CollageForm

    def form_valid_action(self, form):
        """Find collage items and save them.
        """
        form_data = form.cleaned_data

        # Add items to collage by coordinates.
        x = float(form_data['x'])
        y = float(form_data['y'])
        # TODO: convert radius to correct scale (works now for google + rd)
        radius = float(form_data['radius'])
        workspace_id = form_data['workspace_id']
        srs = form_data['srs']
        google_x, google_y = coordinates.srs_to_google(srs, x, y)

        # Workspace.
        workspace = WorkspaceEdit.objects.get(pk=workspace_id)
        collage = CollageEdit.get_or_create(
            self.request.session.session_key, self.request.user)

        found = search(workspace, google_x, google_y, radius)

        for found_item in found:
            # Add all found items to collage.
            logger.debug("Adding collage item %s" % found_item['name'])
            #print '%r' % found_item['identifier']
            collage.collage_items.create(
                adapter_class=found_item['workspace_item'].adapter_class,
                adapter_layer_json=found_item[
                    'workspace_item'].adapter_layer_json,
                name=found_item['name'][:80],
                identifier=found_item['identifier'])


class CollageAddView(CollageMixin, ActionDialogView):
    """
    Add collage item by name + adapter_class + adapter_layer_json + identifier.
    """
    template_name = 'lizard_map/box_collage.html'
    template_name_success = template_name
    form_class = CollageAddForm

    def form_valid_action(self, form):
        data = form.cleaned_data
        collage = CollageEdit.get_or_create(
            self.request.session.session_key, self.request.user)
        # Parse_identifier_json is unnecessary, but it provides an
        # extra check.
        collage.collage_items.create(
            adapter_class=data['adapter_class'],
            adapter_layer_json=data['adapter_layer_json'],
            name=data['name'][:80],
            identifier=parse_identifier_json(data['identifier']))


class CollageEmptyView(CollageView):
    """
    Empty collage.
    """
    form_class = EmptyForm

    def form_valid_action(self, form):
        """Delete all collage items from collage_edit.
        """
        logger.debug('Deleting all collage items from collage_edit')
        collage_edit = CollageEdit.get_or_create(
            self.request.session.session_key, self.request.user)
        collage_edit.collage_items.all().delete()


class CollageItemEditView(CollageView):
    """Edit collage item: create, (read, )update or delete"""
    form_class = EditForm

    def form_valid_action(self, form):
        form_data = form.cleaned_data
        collage_edit = CollageEdit.get_or_create(
            self.request.session.session_key, self.request.user)
        collage_item = collage_edit.collage_items.get(
            pk=form_data['object_id'])
        if form_data['action'] == 'update':
            logger.debug("Updating collage item...")
            collage_item.visible = form_data['visible']
            collage_item.save()
        elif form_data['action'] == 'delete':
            logger.debug("Deleting collage item...")
            collage_item.delete()


class CollagePopupView(CollageMixin, TemplateView):
    template_name = 'lizard_map/box_collage_popup.html'


class WorkspaceEmptyView(WorkspaceEditMixin, ActionDialogView):
    template_name = 'lizard_map/box_workspace.html'
    template_name_success = template_name
    form_class = EmptyForm

    def form_valid_action(self, form):
        """
        """
        workspace_edit = WorkspaceEdit.get_or_create(
            self.request.session.session_key, self.request.user)
        workspace_edit.workspace_items.all().delete()


"""
Export
"""


# # TODO: update to L3
# def export_snippet_group_csv(request, snippet_group_id):
#     """
#     Creates a table with each location as column. Each row is a datetime.
#     """
#     snippet_group = WorkspaceCollageSnippetGroup.objects.get(
#         pk=snippet_group_id)
#     start_date, end_date = current_start_end_dates(request)
#     table = snippet_group.values_table(start_date, end_date)

#     response = HttpResponse(mimetype='text/csv')
#     response['Content-Disposition'] = 'attachment; filename=export.csv'
#     writer = csv.writer(response)
#     for row in table:
#         writer.writerow(row)
#     return response


# # TODO: update to L3
# def export_identifier_csv(request, workspace_item_id=None,
#     identifier_json=None):
#     """
#     Uses adapter.values to get values. Then return these
# #values in csv format.
#     """
#     # Collect input.
#     if workspace_item_id is None:
#         workspace_item_id = request.GET.get('workspace_item_id')
#     if identifier_json is None:
#         identifier_json = request.GET.get('identifier_json')
#     workspace_item = WorkspaceItem.objects.get(pk=workspace_item_id)
#     identifier = parse_identifier_json(identifier_json)
#     start_date, end_date = current_start_end_dates(request)
#     adapter = workspace_item.adapter
#     values = adapter.values(identifier, start_date, end_date)
#     filename = '%s.csv' % (
#         adapter.location(**identifier).get('name', 'export'))

#     # Make the csv output.
#     response = HttpResponse(mimetype='text/csv')
#     response['Content-Disposition'] = 'attachment; filename="%s"' % filename
#     writer = csv.writer(response)
#     writer.writerow(['Datum + tijdstip', 'Waarde', 'Eenheid'])
#     for row in values:
#         writer.writerow([row['datetime'], row['value'], row['unit']])
#     return response


# # TODO: update to L3
# def export_snippet_group_statistics_csv(request, snippet_group_id=None):
#     """
#     Exports snippet_group statistics as csv.
#     """
#     if snippet_group_id is None:
#         snippet_group_id = request.GET.get('snippet_group_id')
#     snippet_group = WorkspaceCollageSnippetGroup.objects.get(
#         pk=snippet_group_id)
#     start_date, end_date = current_start_end_dates(request)
#     statistics = snippet_group.statistics(start_date, end_date)

#     response = HttpResponse(mimetype='text/csv')
#     response['Content-Disposition'] = ('attachment; '
#                                        'filename=export_statistics.csv')
#     writer = csv.writer(response)
#     colnames = ['min', 'max', 'avg']
#     colnamesdisplay = ['min', 'max', 'avg']
#     if snippet_group.boundary_value is not None:
#         colnames.append('count_lt')
#         colnames.append('count_gte')
#         colnamesdisplay.append(
#             '# < %s' % snippet_group.boundary_value)
#         colnamesdisplay.append(
#             '# >= %s' % snippet_group.boundary_value)
#     if snippet_group.percentile_value is not None:
#         colnames.append('percentile')
#         colnamesdisplay.append(
#             'percentile %f' % snippet_group.percentile_value)
#     writer.writerow(colnamesdisplay)
#     for row in statistics:
#         writer.writerow([row[colname] for colname in colnames])
#     return response


"""
Map locations are stored in the session with key MAP_SESSION. It
contains a dictionary with fields x, y and zoom.
"""


def map_location_save(request):
    """
    Save map layout in session.

    - extent as strings (POST top, left, right, bottom).
    - selected base layer name.


    """
    top = request.POST['top']
    left = request.POST['left']
    right = request.POST['right']
    bottom = request.POST['bottom']
    base_layer_name = request.POST['base_layer_name']
    request.session[MAP_LOCATION] = {
        'top': top,
        'left': left,
        'right': right,
        'bottom': bottom}
    request.session[MAP_BASE_LAYER] = base_layer_name
    return HttpResponse("")


def map_location_load_default(request):
    """
    Return start_extent
    """
    extent = Setting.extent(
        'start_extent',
        DEFAULT_START_EXTENT)

    map_location = {'extent': extent}

    request.session[MAP_BASE_LAYER] = ''  # Reset selected base layer.

    return HttpResponse(json.dumps(map_location))


# Save map
def save_map_as_image(request):
    """
    Return map as png image to download.
    """
    data = {
        'width': int(request.GET.get('WIDTH')),
        'height': int(request.GET.get('HEIGHT')),
        'layers': [layer.strip()
                   for layer in request.GET.get('LAYERS').split(',')],
        'bbox': tuple([float(i.strip())
                       for i in request.GET.get('BBOX').split(',')]),
        'srs': request.GET.get('SRS'),
        'workspaces': request.session.get('workspaces'),
        'color': "transparent",
        'format': "png",
        'content_type': "application/x-png",
        }

    img = create_mapnik_image(request, data)
    buf = mapnik_image_to_stream(request, data, img)

    response = HttpResponse(buf.read())
    response['Content-Type'] = 'application/x-png'
    response['Content-disposition'] = 'Attachment; filename=%s' % 'kaart.png'

    return response


def create_mapnik_image(request, data):
    """TODO: remove copy-pasting.
    """
    # Map settings
    mapnik_map = mapnik.Map(data['width'], data['height'])
    layers = data['layers']
    # Setup mapnik srs.
    mapnik_map.srs = coordinates.srs_to_mapnik_projection[data['srs']]
    mapnik_map.background = mapnik.Color(data['color'])
    #m.background = mapnik.Color(data['color')]

    workspace = WorkspaceEdit.get_or_create(
        request.session.session_key, user=request.user)

    workspace_items = workspace.workspace_items.filter(
        visible=True).reverse()

    for workspace_item in workspace_items:
        logger.debug("Drawing layer for %s..." % workspace_item)
        layers, styles = workspace_item.adapter.layer(layer_ids=layers,
                                                      request=request)
        layers.reverse()  # first item should be drawn on top (=last)
        for layer in layers:
            mapnik_map.layers.append(layer)
        for name in styles:
            mapnik_map.append_style(name, styles[name])


    #Zoom and create image
    logger.debug("Zooming to box...")
    mapnik_map.zoom_to_box(mapnik.Envelope(*data['bbox']))
    img = mapnik.Image(data['width'], data['height'])
    logger.debug("Rendering map...")
    mapnik.render(mapnik_map, img)

    return img


def mapnik_image_to_stream(request, data, img):
    """
    Convert mapnik image object to bytes stream

    TODO: remove hardcoding url
    """
    http_user_agent = request.META.get('HTTP_USER_AGENT', '')
    logger.debug("Converting image to rgba...")

    bbox = ",".join([str(x) for x in data['bbox']])
    geoserver_img = urllib2.urlopen("http://10.100.130.132:8080/geoserver/"+
        "wms?LAYERS=nhi%3Awaterkaart&FORMAT=image%2Fpng&MAXRESOLUTION=364&SERVICE"+
        "=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&EXCEPTIONS=application%2Fvnd."+
        "ogc.se_inimage&SRS=EPSG%3A28992&BBOX="+ str(bbox) +
        "&WIDTH="+ str(data['width']) +"&HEIGHT=" + str(data['height'])).read()

    # ^^^ TODO: This should be configurable! (Added by gnijholt on Sep 28 2011)
    base_image = Image.open(StringIO.StringIO(geoserver_img))
    rgba_image = Image.fromstring('RGBA',
                                  (data['width'], data['height']),
                                  img.tostring()).convert("RGBA")

    base_w, base_h = base_image.size
    rgba_w, rgba_h = rgba_image.size

    offset = ((base_w-rgba_w), (base_h-rgba_h))
    base_image.paste(rgba_image, offset, rgba_image)
    # ^^^ Passing rgba_image twice to get transparency working in paste()

    buf = StringIO.StringIO()
    if 'MSIE 6.0' in http_user_agent:
        imgPIL = base_image.convert('P')
        imgPIL.save(buf, data['format'], transparency=0)
    else:
        base_image.save(buf, data['format'])
    buf.seek(0)
    return buf


# Statistics

def statistics_csv(request):
    """
    Return csv for statistics of given collage_items.

    Collage items are from your collage edit.

    TODO: when statistics must be downloaded from other collage-items,
    we must pass the object in a different way.

    TODO: make prettier
    """
    start_date, end_date = current_start_end_dates(request)
    collage = CollageEdit.get_or_create(
        request.session.session_key, request.user)
    collage_items = collage.collage_items.filter(visible=True)
    statistics = []
    for collage_item in collage_items:
        statistics.extend(collage_item.statistics(start_date, end_date))

    # Statistics as csv.
    filename = 'statistieken.csv'

    # Make the csv output.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = ('attachment; filename="%s"' % filename)
    writer = csv.writer(response)
    writer.writerow(['Naam', 'Periode', 'Minimum', 'Maximum', 'Gemiddeld',
                     'Percentiel grens', 'Percentiel waarde',
                     'Grenswaarde', 'Aantal boven grenswaarde',
                     'Aantal onder grenswaarde'])
    for row in statistics:
        writer.writerow([
                row['name'], row['period'], row['min'], row['max'], row['avg'],
                row['percentile_value'], row['percentile'],
                row['boundary_value'], row['count_lt'], row['count_gte']])
    return response


# Adapter related views

class AdapterMixin(object):
    """
    Provide functions to get adapter stuff from get request
    """
    def adapter(self, adapter_class):
        """
        named url arguments become kwargs
        """
        adapter_layer_json = self.request.GET.get("adapter_layer_json")
        layer_arguments = adapter_layer_arguments(adapter_layer_json)
        return adapter_entrypoint(adapter_class, layer_arguments)

    def identifiers(self):
        identifier_json_list = self.request.GET.getlist('identifier')
        identifier_list = [json.loads(identifier_json) for identifier_json in
                           identifier_json_list]
        return identifier_list

    def identifier(self):
        identifier_json = self.request.GET.get('identifier')
        identifier = parse_identifier_json(identifier_json)
        return identifier


class ImageMixin(object):
    def width_height(self):
        width = self.request.GET.get('width')
        height = self.request.GET.get('height')

        if width:
            width = int(width)
        else:
            # We want None, not u''.
            width = None

        if height:
            height = int(height)
        else:
            # We want None, not u''.
            height = None
        return width, height


class AdapterImageView(AdapterMixin, ImageMixin, View):
    def get(self, request, *args, **kwargs):
        """
        named url arguments become kwargs
        """
        current_adapter = self.adapter(kwargs['adapter_class'])
        identifier_list = self.identifiers()
        width, height = self.width_height()

        start_date, end_date = current_start_end_dates(self.request)

        # add animation slider position
        layout_extra = slider_layout_extra(self.request)

        return current_adapter.image(
            identifier_list, start_date, end_date,
            width, height,
            layout_extra=layout_extra)


class AdapterValuesView(AdapterMixin, ViewContextMixin, TemplateView):
    """
    Values for a single identifier

    Format in csv, html
    """
    template_name = 'lizard_map/box_table.html'

    def get(self, request, *args, **kwargs):
        adapter = self.adapter(kwargs['adapter_class'])
        output_type = self.kwargs['output_type']
        identifier = self.identifier()
        self.start_date, self.end_date = current_start_end_dates(self.request)

        self.values = adapter.values(
            identifier, self.start_date, self.end_date)

        self.name = adapter.location(**identifier).get('name', 'export')

        if output_type == 'csv':
            filename = '%s.csv' % (
                self.name)
            # Make the csv output.
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = (
                'attachment; filename="%s"' %
                filename)
            writer = csv.writer(response)
            writer.writerow(['Datum + tijdstip', 'Waarde', 'Eenheid'])
            for row in self.values:
                writer.writerow([row['datetime'], row['value'], row['unit']])
            return response
        else:
            # Make html table using self.values
            return super(AdapterValuesView, self).get(request, *args, **kwargs)
