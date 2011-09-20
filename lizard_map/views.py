import StringIO
import datetime

from django.conf import settings
from django.db.models import Max
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.template.loader import render_to_string
from django.template import RequestContext
from django.utils import simplejson as json
from django.views.decorators.cache import never_cache
import Image
import csv
import logging
import mapnik

from lizard_ui.models import ApplicationScreen

from lizard_map import coordinates
from lizard_map.adapter import parse_identifier_json
from lizard_map.animation import slider_layout_extra
from lizard_map.daterange import current_start_end_dates
from lizard_map.models import Workspace
from lizard_map.models import WorkspaceCollage
from lizard_map.models import WorkspaceCollageSnippet
from lizard_map.models import WorkspaceCollageSnippetGroup
from lizard_map.models import WorkspaceItem
from lizard_map.utility import analyze_http_user_agent
from lizard_map.utility import short_string
from lizard_map.workspace import WorkspaceManager
# Workspace stuff

# L3
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView

from lizard_ui.views import ViewContextMixin
from lizard_map.animation import AnimationSettings
from lizard_map.daterange import current_period
from lizard_map.models import BackgroundMap
from lizard_map.models import CollageEdit
from lizard_map.models import Setting
from lizard_map.models import WorkspaceEdit
from lizard_map.models import WorkspaceEditItem
from lizard_map.models import WorkspaceStorage
from lizard_map.forms import WorkspaceSaveForm
from lizard_map.forms import WorkspaceLoadForm
from lizard_map.forms import DateRangeForm
from lizard_map.forms import CollageForm
from lizard_map.forms import EditForm
from lizard_map.forms import EmptyForm
from lizard_map.forms import SingleObjectForm

from daterange import deltatime_range
from daterange import store_timedelta_range


CUSTOM_LEGENDS = 'custom_legends'
MAP_LOCATION = 'map_location'
MAP_BASE_LAYER = 'map_base_layer'  # The selected base layer
CRUMBS_HOMEPAGE = {'name': 'home', 'title': 'hoofdpagina', 'url': '/'}
POPUP_VIDEO_LAST_SEEN = 'popup_video_last_seen'
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
    """Add workspace and map variables. Not (yet) pretty.
    """
    javascript_click_handler = 'popup_click_handler'

    def workspace_edit(self):
        """Return your workspace"""
        if not hasattr(self, '_workspace_edit'):
            self._workspace_edit = WorkspaceEdit.get_or_create(
                self.request.session.session_key, user=self.request.user)
        return self._workspace_edit

    def animation_slider(self):
        """Add animation slider? Default: none."""
        if not hasattr(self, '_animation_slider'):
            self._animation_slider = None  # default
            if self.workspace_edit().is_animatable:
                self._animation_slider = AnimationSettings(self.request).info()
        return self._animation_slider

    def javascript_hover_handler(self):
        if not hasattr(self, '_javascript_hover_handler'):
            self._javascript_hover_handler = Setting.get(
                'javascript_hover_handler', None)
        return self._javascript_hover_handler


class MapMixin(object):
    """All map stuff
    """
    has_google = False  # Can be set after calling background_maps

    def maps(self):
        # Add map variables.
        self.map_variables = map_variables(self.request)
        return ""

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

    def background_maps(self):
        maps = BackgroundMap.objects.filter(active=True)

        # For the client side to determine is there is a google map.
        if maps.filter(
            layer_type=BackgroundMap.LAYER_TYPE_GOOGLE).count() > 0:

            self.has_google = True

        if not maps:
            logger.warn("No background maps are active. Taking default.")
            maps = BackgroundMap(
                name='Default map',
                default=True,
                active=True,
                layer_type=BackgroundMap.LAYER_TYPE_OSM,
                layer_url=DEFAULT_OSM_LAYER_URL)

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
    WorkspaceMixin, CollageMixin, DateRangeMixin, ViewContextMixin, MapMixin,
    GoogleTrackingMixin, TemplateView):
    """All-in-one"""
    pass


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

        # Determine if we want to show the video. Only show it once
        # every day or so.
        popup_video_url = kwargs.get('popup_video_url', None)

        # Update request for popup, resets popup_video_url if too new.
        if popup_video_url is not None:
            now = datetime.datetime.now()
            if not POPUP_VIDEO_LAST_SEEN in self.request.session:
                # Record the time and show the popup.
                self.request.session[POPUP_VIDEO_LAST_SEEN] = now
            elif ((now - self.request.session[POPUP_VIDEO_LAST_SEEN]) <
                TIME_BETWEEN_VIDEO_POPUP):
                # We've seen it recently enough, don't show it now.
                popup_video_url = None
            else:
                # Record the new time and show the popup.
                self.request.session[POPUP_VIDEO_LAST_SEEN] = now

        # May be None, even when popup_video_url exists.
        context['popup_video_url'] = popup_video_url

        return context


# # Obsolete
# def workspace(request,
#               workspace_id,
#               javascript_click_handler=None,
#               javascript_hover_handler=None,
#               template='lizard_map/workspace.html'):
#     """Render page with one workspace.

#     workspaces in dictionary, because of ... ?
#     """
#     workspace = get_object_or_404(Workspace, pk=workspace_id)

#     context_dict = {'workspaces': {'user': [workspace]},
#                     }
#     if javascript_click_handler:
#         context_dict['javascript_click_handler'] = javascript_click_handler
#     if javascript_hover_handler:
#         context_dict['javascript_hover_handler'] = javascript_hover_handler
#     return render_to_response(
#         template,
#         context_dict,
#         context_instance=RequestContext(request))

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


class DateRangeView(DateRangeMixin, ActionDialogView):
    template_name = 'lizard_map/box_daterange.html'
    template_name_success = template_name
    form_class = DateRangeForm  # Define your form

    def form_valid_action(self, form):
        """
        Update date range
        """
        logger.debug("Updating date range...")
        date_range = form.cleaned_data

        period, timedelta_start, timedelta_end = deltatime_range(
            date_range)
        store_timedelta_range(
            self.request, period, timedelta_start, timedelta_end)


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


# # L3
# @never_cache
# def workspace_item_empty(request):
#     """Clear workspace items for edit workspace."""
#     workspace_edit = WorkspaceEdit.get_or_create(
#         request.session.session_key, request.user)
#     workspace_edit.workspace_items.all().delete()

#     return HttpResponse("")


# L3
@never_cache
def workspace_edit_item(
    request, workspace_edit=None, workspace_item_id=None, visible=None):
    """edits a workspace_item

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


# # L3: based on workspace_item_toggle. UNFINISHED NEED TESTING
# @never_cache
# def collage_item_toggle(
#     request,
#     collage_edit=None):

#     """Toggle collage item in collage.

#     Return if it is added (True), or removed (False)
#     """

#     # For testing, workspace_edit can be given.
#     if collage_edit is None:
#         collage_edit = CollageEdit.get_or_create(
#             request.session.session_key, request.user)

#     name = request.POST['name']
#     adapter_class = request.POST['adapter_class']
#     adapter_layer_json = request.POST['adapter_layer_json']
#     identifier = json.loads(request.POST['identifier'])

#     # Find out if it is already present.
#     existing_collage_items = collage_edit.collage_items.filter(
#         adapter_class=adapter_class,
#         adapter_layer_json=adapter_layer_json,
#         identifier=identifier)
#     if existing_collage_items.count() == 0:
#         # Create new
#         logger.debug("Creating new collage-item.")

#         # TODO: put this in model.
#         if collage_edit.collage_items.count() > 0:
#             max_index = collage_edit.collage_items.aggregate(
#                 Max('index'))['index__max']
#         else:
#             max_index = 10

#         collage_edit.collage_items.create(
#             adapter_class=adapter_class,
#             index=max_index + 10,
#             adapter_layer_json=adapter_layer_json,
#             identifier=identifier,
#             name=name[:80])
#         just_added = True
#     else:
#         # Delete existing items
#         logger.debug("Deleting existing collage-item.")
#         existing_collage_items.delete()
#         just_added = False

#     return HttpResponse(json.dumps(just_added))




#To be updated
@never_cache
def workspace_item_extent(request, workspace_item_id=None):
    """Returns extent for the workspace in json.

    Transform to correct client-side projection, then return coordinates.
    """
    workspace_item_id = request.GET['workspace_item_id']
    workspace_item = get_object_or_404(WorkspaceItem, pk=workspace_item_id)
    extent = workspace_item.adapter.extent()

    srs = Setting.get('projection', DEFAULT_PROJECTION)
    extent_converted['east'], extent_converted['north'] = google_to_srs(
        extent['east'], extent['north'], srs)
    extent_converted['west'], extent_converted['south'] = google_to_srs(
        extent['west'], extent['south'], srs)

    return HttpResponse(json.dumps(extent_converted))


@never_cache
def snippet_group_graph_edit(request, snippet_group_id):
    """Edits snippet_group properties using post.
    """
    post = request.POST
    title = post.get('title', None)
    x_label = post.get('x_label', None)
    y_label = post.get('y_label', None)
    y_min = post.get('y_min', None)
    y_max = post.get('y_max', None)
    boundary_value = post.get('boundary_value', None)
    percentile_value = post.get('percentile_value', None)
    aggregation_period = post.get('aggregation_period', None)
    restrict_to_month = post.get('restrict_to_month', None)
    if restrict_to_month is not None:
        try:
            restrict_to_month = int(restrict_to_month)
            assert restrict_to_month > 0
            assert restrict_to_month < 13
        except ValueError:
            restrict_to_month = None

    snippet_group = WorkspaceCollageSnippetGroup.objects.get(
        pk=snippet_group_id)
    if title is not None:
        # Empty string is also good! it will force default title.
        snippet_group.layout_title = title
    if x_label is not None:
        snippet_group.layout_x_label = x_label
    if y_label is not None:
        snippet_group.layout_y_label = y_label
    snippet_group.restrict_to_month = restrict_to_month
    if aggregation_period is not None:
        snippet_group.aggregation_period = int(aggregation_period)
    try:
        snippet_group.layout_y_min = float(y_min)
    except (ValueError, TypeError):
        snippet_group.layout_y_min = None
    try:
        snippet_group.layout_y_max = float(y_max)
    except (ValueError, TypeError):
        snippet_group.layout_y_max = None
    try:
        snippet_group.boundary_value = float(boundary_value)
    except (ValueError, TypeError):
        snippet_group.boundary_value = None
    try:
        snippet_group.percentile_value = float(percentile_value)
    except (ValueError, TypeError):
        snippet_group.percentile_value = None
    snippet_group.save()
    return HttpResponse('')


@never_cache
def snippet_group_image(request, snippet_group_id, legend=True):
    """Draws a single image for the snippet_group. There MUST be at
    least 1 snippet in the group."""

    snippet_group = WorkspaceCollageSnippetGroup.objects.get(
        pk=snippet_group_id)
    snippets = snippet_group.snippets.filter(visible=True)
    identifiers = [snippet.identifier for snippet in snippets]

    # Add aggregation_period to each identifier
    for identifier in identifiers:
        if not 'layout' in identifier:
            identifier['layout'] = {}
        identifier['layout'][
            'aggregation_period'] = snippet_group.aggregation_period

    # Add legend option ('layout' is always present).
    if legend:
        for identifier in identifiers:
            identifier['layout']['legend'] = True

    # Get width and height.
    width = request.GET.get('width')
    height = request.GET.get('height')
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

    using_workspace_item = snippets[0].workspace_item
    start_date, end_date = current_start_end_dates(request)
    layout_extra = snippet_group.layout()  # Basic extra's, x-min, title, ...

    # Add current position of slider, if available

    layout_extra.update(slider_layout_extra(request))

    return using_workspace_item.adapter.image(identifiers,
                                              start_date, end_date,
                                              width, height,
                                              layout_extra=layout_extra)


# @never_cache
# def session_workspace_edit_item(request,
#                                 workspace_item_id=None,
#                                 workspace_category='user'):
#     """edits workspace item, the function automatically finds best
#     appropriate workspace

#     if workspace_item_id is None, a new workspace_item will be created
#     using workspace_item_add TODO if workspace_item_id is filled in,
#     apply edits and save

#     """
#     workspace_id = request.session['workspaces'][workspace_category][0]

#     is_temp_workspace = workspace_category == 'temp'

#     if workspace_item_id is None:
#         return workspace_item_add(request, workspace_id,
#                                   is_temp_workspace=is_temp_workspace)

#     #todo: maak functie af
#     return


@never_cache
def session_workspace_extent(request, workspace_category='user'):
    """Returns extent for the workspace in json.
    """
    if 'workspaces' in request.session:
        workspace_id = request.session['workspaces'][workspace_category][0]
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        return HttpResponse(json.dumps(workspace.extent()))
    else:
        return HttpResponse(json.dumps(''))


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
    x_found = None
    y_found = None

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

        html_per_workspace_item = workspace_item.adapter.html(
            identifiers=identifiers,
            layout_options={'add_snippet': add_snippet,
                            'legend': True},
            )

        if 'google_coords' in display_object:
            x_found, y_found = display_object['google_coords']
        html[workspace_item.id] = html_per_workspace_item

    result_html = [html[index] for index in display_group_order][:3]

    if popup_id is None:
        popup_id = 'popup-id'
    result = {'id': popup_id,
              'x': x_found,
              'y': y_found,
              'html': result_html,
              'big': big_popup,
              }
    return HttpResponse(json.dumps(result))


# Updated for L3, but needs refactoring.
def popup_collage_json(collage, popup_id, request=None):
    """
    Display collage. Each item in a separate tab.
    """

    html = []
    big_popup = True
    google_x, google_y = None, None

    collage_items = collage.collage_items.filter(visible=True)

    # L3. For now: only one page per collage item. No grouping yet.
    for collage_item in collage_items:
        html.append(collage_item.html())

    result = {'id': popup_id,
              'html': html,
              'big': big_popup,
              }
    return HttpResponse(json.dumps(result))


# Collages stuff


# Needs updating
def collage(request,
            collage_id,
            editable=False,
            template='lizard_map/collage.html'):
    """Render page with one collage"""
    show_table = request.GET.get('show_table', False)

    collage = get_object_or_404(WorkspaceCollage, pk=collage_id)

    return render_to_response(
        template,
        {'collage': collage,
         'editable': editable,
         'request': request,
         'show_table': show_table},
        context_instance=RequestContext(request))


# Obsolete
@never_cache
def session_collage_snippet_add(request,
                                workspace_item_id=None,
                                workspace_item_location_identifier=None,
                                workspace_item_location_shortname=None,
                                workspace_item_location_name=None,
                                workspace_collage_id=None,
                                workspace_category='user'):
    """finds session user workspace and add snippet to (only) corresponding
    collage
    """

    if workspace_item_id is None:
        workspace_item_id = request.POST.get('workspace_item_id')
    if workspace_item_location_identifier is None:
        workspace_item_location_identifier = request.POST.get(
            'workspace_item_location_identifier')
    if workspace_item_location_shortname is None:
        workspace_item_location_shortname = request.POST.get(
            'workspace_item_location_shortname')
    if workspace_item_location_name is None:
        workspace_item_location_name = request.POST.get(
            'workspace_item_location_name')

    workspace_id = request.session['workspaces'][workspace_category][0]
    workspace = Workspace.objects.get(pk=workspace_id)
    workspace_item = WorkspaceItem.objects.get(pk=workspace_item_id)

    if len(workspace.collages.all()) == 0:
        workspace.collages.create()
    collage = workspace.collages.all()[0]

    # Shorten name to 80 characters
    workspace_item_location_shortname = short_string(
        workspace_item_location_shortname, 80)
    workspace_item_location_name = short_string(
        workspace_item_location_name, 80)

    # create snippet using collage function: also finds/makes snippet group
    snippet, _ = collage.get_or_create_snippet(
        workspace_item=workspace_item,
        identifier_json=workspace_item_location_identifier,
        shortname=workspace_item_location_shortname,
        name=workspace_item_location_name)

    return HttpResponse(json.dumps(workspace_id))


# Obsolete
def session_collage_snippet_delete(request,
                                   object_id=None):
    """removes snippet

    TODO: check permission of collage, workspace owners
    """
    if object_id is None:
        object_id = request.POST.get('object_id')
    snippet = get_object_or_404(WorkspaceCollageSnippet, pk=object_id)
    # snippet_group = snippet.snippet_group

    snippet.delete()
    return HttpResponse()


# Obsolete
@never_cache
def snippet_popup(request, snippet_id=None):
    """get snippet/fews location by snippet_id and return data

    """
    if snippet_id is None:
        snippet_id = request.GET.get('snippet_id')
    snippet = get_object_or_404(WorkspaceCollageSnippet, pk=snippet_id)

    popup_id = 'popup-snippet-%s' % snippet_id
    return popup_json([snippet.location, ],
                      popup_id=popup_id,
                      request=request,
                      hide_add_snippet=True)


# L3. TODO: test
@never_cache
def collage_popup(request,
                  collage_id=None,
                  template='lizard_map/collage.html'):
    """Render page with one collage in popup format

    collage_id in GET parameter.
    """
    # if collage_id is None:
    #     collage_id = request.GET.get('collage_id')
    # collage = get_object_or_404(WorkspaceCollage, pk=collage_id)
    collage = CollageEdit.get_or_create(
        request.session.session_key, request.user)
    popup_id = 'popup-collage'

    # Only one collage popup allowed, also check jquery.workspace.js
    return popup_collage_json(
        collage,
        popup_id=popup_id,
        request=request)


# L3
@never_cache
def workspace_item_image(request, workspace_item):
    """Shows image corresponding to workspace item and location identifier(s)

    identifier_list
    """
    identifier_json_list = request.GET.getlist('identifier')
    identifier_list = [json.loads(identifier_json) for identifier_json in
                       identifier_json_list]

    width = request.GET.get('width')
    height = request.GET.get('height')
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

    start_date, end_date = current_start_end_dates(request)

    # add animation slider position
    layout_extra = slider_layout_extra(request)

    return workspace_item.adapter.image(identifier_list, start_date, end_date,
                                        width, height,
                                        layout_extra=layout_extra)


# L3
def workspace_edit_item_image(request, workspace_item_id):
    workspace_item = get_object_or_404(
        WorkspaceEditItem, pk=workspace_item_id)
    return workspace_item_image(request, workspace_item)


@never_cache
def snippet_edit(request, snippet_id=None, visible=None):
    """
    Edits snippet layout properties.
    """
    post = request.POST
    layout = {}
    if snippet_id is None:
        snippet_id = post['snippet_id']
    snippet = get_object_or_404(WorkspaceCollageSnippet, pk=snippet_id)
    if visible is None:
        if 'visible' in post:
            visible = post['visible']
    if visible:
        lookup = {'true': True, 'false': False}
        snippet.visible = lookup[visible]
    if post.get('color', None):
        layout.update({'color': post['color']})
    if post.__contains__('line_min'):
        layout.update({'line_min': None})
    if post.__contains__('line_max'):
        layout.update({'line_max': None})
    if post.__contains__('line_avg'):
        layout.update({'line_avg': None})

    identifier = snippet.identifier
    if 'layout' in identifier:
        del identifier['layout']
    identifier.update({'layout': layout})

    snippet.set_identifier(identifier)
    snippet.save()

    return HttpResponse('')


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
def search_coordinates(request, format='popup'):
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
            # For the x/y we use the original x/y value to position the popup to
            # the lower right of the cursor to prevent click propagation problems.
            result['x'] = x + (radius / 10)
            result['y'] = y - (radius / 10)
            return HttpResponse(json.dumps(result))
        else:
            # default: as popup
            return popup_json(found, request=request)
    else:
        return popup_json([])


def action_collage_add(form_data):
    """
    Add items to collage by coordinates.
    """
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
        collage.collage_items.create(
            adapter_class=found_item['workspace_item'].adapter_class,
            adapter_layer_json=found_item[
                'workspace_item'].adapter_layer_json,
            name=found_item['name'],
            identifier=found_item['identifier'])


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
        action_collage_add(form_data)


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


class WorkspaceEmptyView(WorkspaceMixin, ActionDialogView):
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


def export_snippet_group_csv(request, snippet_group_id):
    """
    Creates a table with each location as column. Each row is a datetime.
    """
    snippet_group = WorkspaceCollageSnippetGroup.objects.get(
        pk=snippet_group_id)
    start_date, end_date = current_start_end_dates(request)
    table = snippet_group.values_table(start_date, end_date)

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=export.csv'
    writer = csv.writer(response)
    for row in table:
        writer.writerow(row)
    return response


def export_identifier_csv(request, workspace_item_id=None,
    identifier_json=None):
    """
    Uses adapter.values to get values. Then return these values in csv format.
    """
    # Collect input.
    if workspace_item_id is None:
        workspace_item_id = request.GET.get('workspace_item_id')
    if identifier_json is None:
        identifier_json = request.GET.get('identifier_json')
    workspace_item = WorkspaceItem.objects.get(pk=workspace_item_id)
    identifier = parse_identifier_json(identifier_json)
    start_date, end_date = current_start_end_dates(request)
    adapter = workspace_item.adapter
    values = adapter.values(identifier, start_date, end_date)
    filename = '%s.csv' % (
        adapter.location(**identifier).get('name', 'export'))

    # Make the csv output.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    writer = csv.writer(response)
    writer.writerow(['Datum + tijdstip', 'Waarde', 'Eenheid'])
    for row in values:
        writer.writerow([row['datetime'], row['value'], row['unit']])
    return response


def export_snippet_group_statistics_csv(request, snippet_group_id=None):
    """
    Exports snippet_group statistics as csv.
    """
    if snippet_group_id is None:
        snippet_group_id = request.GET.get('snippet_group_id')
    snippet_group = WorkspaceCollageSnippetGroup.objects.get(
        pk=snippet_group_id)
    start_date, end_date = current_start_end_dates(request)
    statistics = snippet_group.statistics(start_date, end_date)

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = ('attachment; '
                                       'filename=export_statistics.csv')
    writer = csv.writer(response)
    colnames = ['min', 'max', 'avg']
    colnamesdisplay = ['min', 'max', 'avg']
    if snippet_group.boundary_value is not None:
        colnames.append('count_lt')
        colnames.append('count_gte')
        colnamesdisplay.append(
            '# < %s' % snippet_group.boundary_value)
        colnamesdisplay.append(
            '# >= %s' % snippet_group.boundary_value)
    if snippet_group.percentile_value is not None:
        colnames.append('percentile')
        colnamesdisplay.append(
            'percentile %f' % snippet_group.percentile_value)
    writer.writerow(colnamesdisplay)
    for row in statistics:
        writer.writerow([row[colname] for colname in colnames])
    return response


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
        'workspaces': request.session['workspaces'],
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

    # Map settings
    mapnik_map = mapnik.Map(data['width'], data['height'])
    layers = data['layers']
    # Setup mapnik srs.
    mapnik_map.srs = coordinates.srs_to_mapnik_projection[data['srs']]
    mapnik_map.background = mapnik.Color(data['color'])
    #m.background = mapnik.Color(data['color')]

    for k, v in data['workspaces'].items():
        if len(v) <= 0:
            v[0] = -1

        workspace = get_object_or_404(Workspace, pk=v[0])
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
    """
    http_user_agent = request.META.get('HTTP_USER_AGENT', '')
    logger.debug("Converting image to rgba...")
    rgba_image = Image.fromstring('RGBA',
                                  (data['width'], data['height']),
                                  img.tostring())
    buf = StringIO.StringIO()
    if 'MSIE 6.0' in http_user_agent:
        imgPIL = rgba_image.convert('P')
        imgPIL.save(buf, data['format'], transparency=0)
    else:
        rgba_image.save(buf, data['format'])
    buf.seek(0)
    return buf
