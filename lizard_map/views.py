import StringIO

import mapnik
import PIL.Image
from django.db.models import Max
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
import simplejson as json

from lizard_map.models import Workspace
from lizard_map.models import WorkspaceItem


def workspace(request,
              workspace_id,
              template='lizard_map/workspace.html'):
    """Render page with one workspace"""
    workspace = get_object_or_404(Workspace, pk=workspace_id)
    return render_to_response(
        template,
        {'workspaces': [workspace]},
        context_instance=RequestContext(request))


def workspace_item_reorder(request,
                           workspace_id,
                           template='lizard_map/tag_workspace.html'):
    """reorder workspace items. returns rendered workspace

    reorders workspace_item[] in new order. expects all workspace_items from
    workspace

    TODO: check permissions
    """
    workspace = get_object_or_404(Workspace, pk=workspace_id)
    workspace_items = [
        get_object_or_404(WorkspaceItem, pk=workspace_item_id) for
        workspace_item_id in request.POST.getlist('workspace_items[]')]
    print workspace_items
    for i, workspace_item in enumerate(workspace_items):
        workspace_item.workspace = workspace
        workspace_item.index = i * 10
        workspace_item.save()
    return render_to_response(
        template,
        {'workspace': workspace},
        context_instance=RequestContext(request))

# TODO: put item_add and item_edit in 1 function


def workspace_item_add(request,
                       workspace_id,
                       template='lizard_map/tag_workspace.html'):
    """add new workspace item to workspace. returns rendered workspace"""
    workspace = get_object_or_404(Workspace, pk=workspace_id)
    name = request.POST['name']
    layer_method = request.POST['layer_method']
    layer_method_json = request.POST['layer_method_json']

    if workspace.workspace_items.count() > 0:
        max_index = workspace.workspace_items.aggregate(
            Max('index'))['index__max']
    else:
        max_index = 10

    workspace.workspace_items.create(layer_method=layer_method,
                                     index=max_index + 10,
                                     layer_method_json=layer_method_json,
                                     name=name)
    return render_to_response(
        template,
        {'workspace': workspace},
        context_instance=RequestContext(request))


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


def workspace_item_delete(request, workspace_item_id=None):
    """delete workspace item from workspace

    returns workspace_id

    if workspace_item_id is not provided, it tries to get the variable
    workspace_item_id from the request.POST
    """
    if workspace_item_id is None:
        workspace_item_id = request.POST['workspace_item_id']
    workspace_item = get_object_or_404(WorkspaceItem, pk=workspace_item_id)
    workspace_id = workspace_item.workspace.id
    workspace_item.delete()

    return HttpResponse(json.dumps(workspace_id))


def session_workspace_edit_item(request,
                                workspace_item_id=None,
                                workspace_category='user'):
    """edits workspace item, the function automatically finds best appropriate
    workspace

    if workspace_item_id is None, a new workspace_item will be created using
    workspace_item_add TODO if workspace_item_id is filled in, apply edits and
    save

    """
    workspace_id = request.session['workspaces'][workspace_category][0]

    if workspace_item_id is None:
        return workspace_item_add(request, workspace_id)

    #todo: maak functie af
    return


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
    # TODO: check that they're not none

    # Map settings
    google_mercator = (
        '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 '
        '+lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m '
        '+nadgrids=@null +no_defs +over')  # No commas between strings!
    # TODO ^^^ Is this the correct one for google?
    mapnik_map = mapnik.Map(width, height)
    mapnik_map.srs = google_mercator
    mapnik_map.background = mapnik.Color('transparent')
    #m.background = mapnik.Color('blue')

    for workspace_item in workspace.workspace_items.filter(visible=True):
        layers, styles = workspace_item.layers()
        for layer in layers:
            mapnik_map.layers.append(layer)
        for name in styles:
            mapnik_map.append_style(name, styles[name])

    #Zoom and create image
    mapnik_map.zoom_to_box(mapnik.Envelope(*bbox))
    # m.zoom_to_box(layer.envelope())
    img = mapnik.Image(width, height)
    mapnik.render(mapnik_map, img)
    http_user_agent = request.META.get('HTTP_USER_AGENT', '')
    rgba_image = PIL.Image.fromstring('RGBA', (width, height), img.tostring())
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


def clickinfo(request, workspace_id):
    # TODO: this one is mostly for testing, so it can be removed later on.
    # [reinout]
    workspace = get_object_or_404(Workspace, pk=workspace_id)
    # xy params from the GET request.
    x = float(request.GET.get('x'))
    y = float(request.GET.get('y'))

    found = None
    for workspace_item in workspace.workspace_items.filter(visible=True):
        found_items = workspace_item.search(x, y)
        if found_items:
            # Grab first one for now.
            found = found_items[0]
            break

    if found:
        msg = "You found %s at  %s, %s" % (found.name, found.x, found.y)
    else:
        msg = 'Nothing found'
    # TODO: return json: {msg, x_found, y_found}
    return HttpResponse(msg)
