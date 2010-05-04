import StringIO

import mapnik
import pkg_resources
import PIL.Image
from django.http import HttpResponse


def wms(request):  # workspace=xyz, layers=abc?
    """Return PNG as WMS service."""

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

    layer = mapnik.Layer(
        "Waterlichamen",
        ("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 "
         "+k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel "
         "+towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 "
         "+units=m +no_defs"))
    # TODO: ^^^ translation!
    layer.datasource = mapnik.Shapefile(
        file=pkg_resources.resource_filename(
            'lizard_map',
            'test_shapefiles/KRWwaterlichamen_vlakken.shp'))
    area_style = mapnik.Style()
    layout_rule = mapnik.Rule()
    area_looks = mapnik.PolygonSymbolizer(mapnik.Color('lightblue'))
    line_looks = mapnik.LineSymbolizer(mapnik.Color('blue'), 1)
    area_looks.fill_opacity = 1
    layout_rule.symbols.append(area_looks)
    layout_rule.symbols.append(line_looks)
    area_style.rules.append(layout_rule)
    m.append_style('Area style', area_style)
    layer.styles.append('Area style')
    m.layers.append(layer)

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
