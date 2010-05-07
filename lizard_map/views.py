import StringIO

import mapnik
import PIL.Image
from django.db.models import Max
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
import simplejson as json

from lizard_map.layers import shapefile_layer
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

def workspace_item_reorder(request, workspace_id):
    """reorder workspace items

    reorders workspace_item[] in new order. expects all workspace_items from workspace

    TODO: check permissions
    """
    workspace = get_object_or_404(Workspace, pk=workspace_id)
    workspace_items = [get_object_or_404(WorkspaceItem, pk=workspace_item_id) for 
                       workspace_item_id in request.POST.getlist('workspace_items[]')]
    for i, workspace_item in enumerate(workspace_items):
        if workspace_item.workspace == workspace:
            workspace_item.index = i*10
            workspace_item.save()
    return HttpResponse(json.dumps(''))

def workspace_item_add(request, workspace_id):
    """add new workspace item to workspace"""
    workspace = get_object_or_404(Workspace, pk=workspace_id)

    max_index = workspace.workspace_items.aggregate(Max('index'))['index__max']

    workspace.workspace_items.create(layer_method='shapefile_layer', index=max_index+10)

    return HttpResponse(json.dumps(''))

def workspace_item_delete(request, workspace_item_id):
    """delete workspace item from workspace"""
    workspace_item = get_object_or_404(WorkspaceItem, pk=workspace_item_id)
    workspace_item.delete()

    return HttpResponse(json.dumps(''))


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

    # TODO: iterate
    for workspace_item in workspace.workspace_items.all():
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
