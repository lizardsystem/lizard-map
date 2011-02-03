import StringIO

from django.conf import settings
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson as json
from django.views.decorators.cache import never_cache
import Image
import csv
import logging
import mapnik

from lizard_map import coordinates
from lizard_map.adapter import parse_identifier_json
from lizard_map.animation import AnimationSettings
from lizard_map.animation import slider_layout_extra
from lizard_map.daterange import current_start_end_dates
from lizard_map.daterange import DateRangeForm
from lizard_map.models import Workspace
from lizard_map.models import WorkspaceItem
from lizard_map.models import WorkspaceCollage
from lizard_map.models import WorkspaceCollageSnippet
from lizard_map.models import WorkspaceCollageSnippetGroup
from lizard_map.utility import analyze_http_user_agent
from lizard_map.utility import short_string
from lizard_map.workspace import WorkspaceManager

# Workspace stuff

CUSTOM_LEGENDS = 'custom_legends'
MAP_LOCATION = 'map_location'
CRUMBS_HOMEPAGE = {'name': 'home', 'title': 'hoofdpagina', 'url': '/'}

logger = logging.getLogger(__name__)


def homepage(request,
             template='lizard_map/example_homepage.html',
             crumbs_prepend=None):
    """Default apps screen, make your own template.
    """
    date_range_form = DateRangeForm(
        current_start_end_dates(request, for_form=True))

    workspace_manager = WorkspaceManager(request)
    workspaces = workspace_manager.load_or_create()
    date_range_form = DateRangeForm(
        current_start_end_dates(request, for_form=True))

    if crumbs_prepend is not None:
        crumbs = list(crumbs_prepend)
    else:
        crumbs = [CRUMBS_HOMEPAGE]

    return render_to_response(
        template,
        {'date_range_form': date_range_form,
         'workspaces': workspaces,
         'javascript_hover_handler': 'popup_hover_handler',
         'javascript_click_handler': 'popup_click_handler',
         'crumbs': crumbs},
        context_instance=RequestContext(request))


def workspace(request,
              workspace_id,
              javascript_click_handler='popup_click_handler',
              javascript_hover_handler='popup_hover_handler',
              template='lizard_map/workspace.html'):
    """Render page with one workspace.

    workspaces in dictionary, because of ... ?
    """
    workspace = get_object_or_404(Workspace, pk=workspace_id)

    # Calculate whether we want animation.
    # TODO: make custom RequestContext where this code is included
    animation_slider = False
    for workspace_item in workspace.workspace_items.filter(
        visible=True):
        if workspace_item.adapter.is_animatable:
            animation_slider = AnimationSettings(request).info()
            break

    date_range_form = DateRangeForm(
        current_start_end_dates(request, for_form=True))
    return render_to_response(
        template,
        {'workspaces': {'user': [workspace]},
         'javascript_click_handler': javascript_click_handler,
         'javascript_hover_handler': javascript_hover_handler,
         'animation_slider': animation_slider,
         'date_range_form': date_range_form},
        context_instance=RequestContext(request))


@never_cache
def workspace_item_reorder(request,
                           workspace_id=None,
                           template='lizard_map/tag_workspace.html'):
    """reorder workspace items. returns workspace_id

    reorders workspace_item[] in new order. expects all workspace_items from
    workspace

    TODO: check permissions
    """
    if workspace_id is None:
        workspace_id = request.GET['workspace_id']

    workspace = get_object_or_404(Workspace, pk=workspace_id)
    workspace_items = [
        get_object_or_404(WorkspaceItem, pk=workspace_item_id) for
        workspace_item_id in request.POST.getlist('workspace-items[]')]
    for i, workspace_item in enumerate(workspace_items):
        workspace_item.workspace = workspace
        workspace_item.index = i * 10
        workspace_item.save()
    return HttpResponse(json.dumps(workspace.id))


# TODO: put item_add and item_edit in 1 function
@never_cache
def workspace_item_add(request,
                       workspace_id=None,
                       is_temp_workspace=False,
                       template='lizard_map/tag_workspace.html'):
    """add new workspace item to workspace. returns rendered workspace"""
    if workspace_id is None:
        workspace_id = request.POST['workspace_id']
    workspace = get_object_or_404(Workspace, pk=workspace_id)
    name = request.POST['name']
    adapter_class = request.POST['adapter_class']
    adapter_layer_json = request.POST['adapter_layer_json']

    if is_temp_workspace:
        # only one workspace item is used in the temp workspace
        workspace.workspace_items.all().delete()
    if workspace.workspace_items.count() > 0:
        max_index = workspace.workspace_items.aggregate(
            Max('index'))['index__max']
    else:
        max_index = 10

    workspace.workspace_items.create(adapter_class=adapter_class,
                                     index=max_index + 10,
                                     adapter_layer_json=adapter_layer_json,
                                     name=name)
    return HttpResponse(json.dumps(workspace.id))


@never_cache
def workspace_item_empty(request,
                       workspace_id,
                       is_temp_workspace=False,
                       template='lizard_map/tag_workspace.html'):
    """Clear workspace items for given workspace."""
    workspace = get_object_or_404(Workspace, pk=workspace_id)
    workspace.workspace_items.all().delete()

    return HttpResponse("")


@never_cache
def workspace_item_edit(request, workspace_item_id=None, visible=None):
    """edits a workspace_item

    returns workspace_id

    TODO: permission
    """
    if workspace_item_id is None:
        workspace_item_id = request.POST['workspace_item_id']
    workspace_item = get_object_or_404(WorkspaceItem, pk=workspace_item_id)
    if visible is None:
        if request.POST['visible']:
            visible = request.POST['visible']
    if visible:
        lookup = {'true': True, 'false': False}
        workspace_item.visible = lookup[visible]
    workspace_item.save()

    return HttpResponse(json.dumps(workspace_item.workspace.id))


@never_cache
def workspace_item_extent(request, workspace_item_id=None):
    """Returns extent for the workspace in json.
    """
    workspace_item_id = request.GET['workspace_item_id']
    workspace_item = get_object_or_404(WorkspaceItem, pk=workspace_item_id)
    return HttpResponse(json.dumps(workspace_item.adapter.extent()))


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
    snippets = snippet_group.snippets.all()
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


@never_cache
def workspace_item_delete(request, object_id=None):
    """delete workspace item from workspace

    returns workspace_id

    if workspace_item_id is not provided, it tries to get the variable
    workspace_item_id from the request.POST
    """
    if object_id is None:
        object_id = request.POST['object_id']
    workspace_item = get_object_or_404(WorkspaceItem, pk=object_id)
    workspace_id = workspace_item.workspace.id
    workspace_item.delete()

    return HttpResponse(json.dumps(workspace_id))


@never_cache
def session_workspace_edit_item(request,
                                workspace_item_id=None,
                                workspace_category='user'):
    """edits workspace item, the function automatically finds best
    appropriate workspace

    if workspace_item_id is None, a new workspace_item will be created
    using workspace_item_add TODO if workspace_item_id is filled in,
    apply edits and save

    """
    workspace_id = request.session['workspaces'][workspace_category][0]

    is_temp_workspace = workspace_category == 'temp'

    if workspace_item_id is None:
        return workspace_item_add(request, workspace_id,
                                  is_temp_workspace=is_temp_workspace)

    #todo: maak functie af
    return


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

    result_html = ''
    x_found = None
    y_found = None

    # Regroup found list of objects into workspace_items.
    display_groups = {}
    for display_object in found:
        workspace_item = display_object['workspace_item']
        if workspace_item.id not in display_groups:
            display_groups[workspace_item.id] = []
        display_groups[workspace_item.id].append(display_object)

    if len(display_groups) > 1:
        big_popup = True
    else:
        big_popup = False

    # Figure out temp workspace items (we don't want add-to-collage there).
    temp_workspace_item_ids = []
    if request is not None:
        workspace_manager = WorkspaceManager(request)
        workspace_manager.load_workspaces()
        temp_workspaces = workspace_manager.workspaces['temp']
        temp_workspace_items = WorkspaceItem.objects.filter(
            workspace__in=temp_workspaces, visible=True)
        temp_workspace_item_ids = [
            workspace_item.id for workspace_item in temp_workspace_items]

    # Now display them.
    for workspace_item_id, display_group in display_groups.items():
        # There MUST be at least one item in the group
        workspace_item = display_group[0]['workspace_item']

        # Check if this display object must have the option add_snippet
        if hide_add_snippet or (workspace_item_id in temp_workspace_item_ids):
            add_snippet = False
        else:
            add_snippet = True

        # Add workspace_item name on top
        # title = workspace_item.name

        identifiers = [display_object['identifier'] for display_object
                       in display_group]
        # img_url = workspace_item_image_url(workspace_item.id, identifiers)

        html_per_workspace_item = workspace_item.adapter.html(
            identifiers=identifiers,
            layout_options={'add_snippet': add_snippet,
                            'legend': True},
            )

        if 'google_coords' in display_object:
            x_found, y_found = display_object['google_coords']
        result_html += html_per_workspace_item

    if popup_id is None:
        popup_id = 'popup-id'
    result = {'id': popup_id,
              'x': x_found,
              'y': y_found,
              'html': result_html,
              'big': big_popup,
              }
    return HttpResponse(json.dumps(result))


def popup_collage_json(collage, popup_id, request=None):
    """
    display collage by adding display_groups together
    """

    result_html = ''
    snippet_groups = collage.snippet_groups.all()
    if len(snippet_groups) > 1:
        big_popup = True
    else:
        big_popup = False
    google_x, google_y = None, None

    for snippet_group in snippet_groups:
        snippets = snippet_group.snippets.all()
        if snippets:
            # Pick workspace_item of first snippet to build html
            workspace_item = snippets[0].workspace_item
            html_per_workspace_item = workspace_item.adapter.html(
                snippet_group=snippet_group,
                layout_options={'legend': True})
            result_html += html_per_workspace_item

            # Pick the location of the first snippet.
            if 'google_coords' in snippets[0].location:
                google_x, google_y = snippets[0].location['google_coords']

    result = {'id': popup_id,
              'x': google_x,
              'y': google_y,
              'html': result_html,
              'big': big_popup,
              }
    return HttpResponse(json.dumps(result))


# Collages stuff


def collage(request,
            collage_id,
            editable=False,
            template='lizard_map/collage.html'):
    """Render page with one collage"""
    date_range_form = DateRangeForm(
        current_start_end_dates(request, for_form=True))
    show_table = request.GET.get('show_table', False)

    collage = get_object_or_404(WorkspaceCollage, pk=collage_id)

    return render_to_response(
        template,
        {'collage': collage,
         'editable': editable,
         'date_range_form': date_range_form,
         'request': request,
         'show_table': show_table},
        context_instance=RequestContext(request))


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


@never_cache
def collage_popup(request,
                  collage_id=None,
                  template='lizard_map/collage.html'):
    """Render page with one collage in popup format"""
    if collage_id is None:
        collage_id = request.GET.get('collage_id')
    collage = get_object_or_404(WorkspaceCollage, pk=collage_id)
    popup_id = 'popup-collage'

    # Only one collage popup allowed, also check jquery.workspace.js
    return popup_collage_json(
        collage,
        popup_id=popup_id,
        request=request)


@never_cache
def workspace_item_image(request, workspace_item_id):
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

    workspace_item = get_object_or_404(WorkspaceItem, pk=workspace_item_id)
    start_date, end_date = current_start_end_dates(request)

    # add animation slider position
    layout_extra = slider_layout_extra(request)

    return workspace_item.adapter.image(identifier_list, start_date, end_date,
                                        width, height,
                                        layout_extra=layout_extra)


def snippet_edit(request, snippet_id):
    """
    Edits snippet layout properties.
    """
    snippet = WorkspaceCollageSnippet.objects.get(pk=snippet_id)

    post = request.POST
    layout = {}
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


def wms(request, workspace_id):
    """Return PNG as WMS service."""

    workspace = get_object_or_404(Workspace, pk=workspace_id)

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
        layers, styles = workspace_item.adapter.layer(layer_ids=layers,
                                                      request=request)
        layers.reverse()  # first item should be drawn on top (=last)
        for layer in layers:
            mapnik_map.layers.append(layer)
        for name in styles:
            mapnik_map.append_style(name, styles[name])
        # mapnik_map.zoom_to_box(layer.envelope())

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


def search_name(request):
    """Search for objects near GET x,y,radius then return
    name. Optional GET parameter srs, if omitted, assume google.
    """
    workspace_manager = WorkspaceManager(request)
    workspace_collections = workspace_manager.load_or_create()

    # xy params from the GET request.
    x = float(request.GET.get('x'))
    y = float(request.GET.get('y'))
    # TODO: convert radius to correct scale (works now for google + rd)
    radius = float(request.GET.get('radius'))
    srs = request.GET.get('srs')
    google_x, google_y = coordinates.srs_to_google(srs, x, y)

    found = []
    for workspace_collection in workspace_collections.values():
        for workspace in workspace_collection:
            for workspace_item in workspace.workspace_items.filter(
                visible=True):
                search_results = workspace_item.adapter.search(
                    google_x, google_y, radius=radius)
                found += search_results
    if found:
        # ``found`` is a list of dicts {'distance': ..., 'timeserie': ...}.
        found.sort(key=lambda item: item['distance'])
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
        return popup_json([])


def search_coordinates(request):
    """searches for objects near GET x,y,radius returns json_popup of
    results. Optional GET parameter srs, if omitted, assume google."""
    workspace_manager = WorkspaceManager(request)
    workspace_collections = workspace_manager.load_or_create()

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

    found = []
    for workspace_collection in workspace_collections.values():
        for workspace in workspace_collection:
            for workspace_item in workspace.workspace_items.filter(
                visible=True):
                search_results = workspace_item.adapter.search(
                    google_x, google_y, radius=radius_search)
                found += search_results
    if found:
        # ``found`` is a list of dicts {'distance': ..., 'timeserie': ...}.
        found.sort(key=lambda item: item['distance'])
        return popup_json(found, request=request)
    else:
        return popup_json([])


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
    Saves given coordinates as strings (POST x, y, zoom) to session.
    """
    x = request.POST['x']
    y = request.POST['y']
    zoom = request.POST['zoom']
    request.session[MAP_LOCATION] = {'x': x, 'y': y, 'zoom': zoom}
    return HttpResponse("")


def map_location_load_default(request):
    """
    Returns stored coordinates in a json dict, or empty dict if
    nothing was saved.
    """
    try:
        map_settings = settings.MAP_SETTINGS
        x = map_settings['startlocation_x']
        y = map_settings['startlocation_y']
        zoom = map_settings['startlocation_zoom']
    except AttributeError:
        logger.warn(
            'Could not find MAP_SETTINGS in '
            'django settings or MAP_SETTINGS '
            'not properly configured, using default coordinates.')
        x, y, zoom = '550000', '6850000', '10'

    map_location = {'x': x, 'y': y, 'zoom': zoom}

    return HttpResponse(json.dumps(map_location))
