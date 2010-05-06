import StringIO

import mapnik
import PIL.Image
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response

from lizard_map.layers import shapefile_layer
from lizard_map.models import Workspace


def workspace(request,
              workspace_id,
              template='lizard_map/workspace.html'):
    """Render page with one workspace"""
    workspace = get_object_or_404(Workspace, pk=workspace_id)
    return render_to_response(
        template,
        {'workspaces': [workspace]},
        context_instance=RequestContext(request))

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
    m = mapnik.Map(width, height)
    # TODO: rename 'm'
    m.srs = google_mercator
    m.background = mapnik.Color('transparent')
    #m.background = mapnik.Color('blue')

    # TODO: iterate
    for workspace_item in workspace.workspace_items.all():
        layers, styles = workspace_item.layers()
        for layer in layers:
            m.layers.append(layer)
        for name in styles:
            m.append_style(name, styles[name])

    #Zoom and create image
    m.zoom_to_box(mapnik.Envelope(*bbox))
    # m.zoom_to_box(layer.envelope())
    img = mapnik.Image(width, height)
    mapnik.render(m, img)
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
