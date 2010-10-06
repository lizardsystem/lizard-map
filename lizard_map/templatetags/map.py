from django import template

register = template.Library()


class MapVariablesNode(template.Node):
    """
    This node adds lizard-map variables to the context; in the
    template those variables are finally inserted into javascript
    code.
    """

    def render(self, context):
        context['base_layer_type'] = 'OSM'  # OSM or WMS
        context['projection'] = 'EPSG:900913'  # EPSG:900913, EPSG:28992
        context['display_projection'] = 'EPSG:4326'  # EPSG:900913, EPSG:28992, EPSG:4326
        context['startlocation_x'] = '550000'
        context['startlocation_y'] = '6850000'
        context['startlocation_zoom'] = '10'
        context['base_layer_wms'] = (
            'http://nederlandwms.risicokaart.nl/wmsconnector/'
            'com.esri.wms.Esrimap?'
            'SERVICENAME=risicokaart_pub_nl_met_ondergrond&')
        context['base_layer_wms_layers'] = (
            'Outline_nederland,Dissolve_provincies,0,2,12,3,38,5,4,9,10')
        context['base_layer_osm'] = (
            'http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png')
        return ''

     # <!-- data-base-layer-type="WMS" {# OSM or WMS #} -->
     # <!-- data-projection="EPSG:28992"  {# for WMS: EPSG:28992, EPSG:900913 #} -->
     # <!-- data-display-projection="EPSG:28992"  {# for WMS: EPSG:28992, EPSG:900913, EPSG:4326 #} -->
     # <!-- data-startlocation-x="127000" {# RD #} -->
     # <!-- data-startlocation-y="473000" -->
     # <!-- data-startlocation-zoom="4" -->

     # <!-- data-base-layer-type="OSM" {# OSM or WMS #} -->
     # <!-- data-projection="EPSG:900913"  {# for WMS: EPSG:28992, EPSG:900913 #} -->
     # <!-- data-display-projection="EPSG:4326"  {# for WMS: EPSG:28992, EPSG:900913, EPSG:4326 #} -->
     # <!-- data-startlocation-x="550000" {# OSM, google projection #} -->
     # <!-- data-startlocation-y="6850000" -->
     # <!-- data-startlocation-zoom="10" -->

@register.tag
def map_variables(parser, token):
    """Display debug info on workspaces."""
    return MapVariablesNode()
