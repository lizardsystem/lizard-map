import logging
import mapnik
import pkg_resources

from lizard_map import coordinates
from lizard_map.models import Legend
from lizard_map.models import LegendPoint
from lizard_map.workspace import WorkspaceItemAdapter

logger = logging.getLogger(__name__)


class WorkspaceItemAdapterShapefile(WorkspaceItemAdapter):
    """Render a WorkspaceItem using a shape file.

    Instance variables:
    * layer_name -- name of the WorkspaceItem that is rendered

    * search_property_name -- name of shapefile feature used in search
      results - must be come kind of id

    * value_field (optional, with legend) -- value field for legend
      (takes 'value' if not given)

    Legend:
    * legend_id (optional, preferenced) -- id of legend (linestyle)
    OR
    * legend_point_id (optional) -- id of legend_point_id (points)
    ELSE it takes default legend

    Shapefile:
    * layer_filename -- absolute path to shapefile
    OR
    * resource_module -- module that contains the shapefile resource
    * resource name -- name of the shapefile resource

    """
    def __init__(self, *args, **kwargs):
        """Store the name and location of the shapefile to render.

        kwargs can specify the shapefile to render, see the implementation of
        this method for details. If kwargs does not specify the shapefile, the
        object renders the shapefile that is specified by default_layer_name,
        default_resource_module and default_resource_name.

        """
        super(WorkspaceItemAdapterShapefile, self).__init__(*args, **kwargs)

        layer_arguments = kwargs['layer_arguments']
        self.layer_name = str(layer_arguments['layer_name'])
        layer_filename = layer_arguments.get('layer_filename', None)
        if layer_filename is not None:
            self.layer_filename = str(layer_filename)
            self.resource_module = None
            self.resource_name = None
        else:
            # If layer_filename is not defined, resource_module and
            # resource_name must be defined.
            self.resource_module = str(layer_arguments['resource_module'])
            self.resource_name = str(layer_arguments['resource_name'])
            self.layer_filename = pkg_resources.resource_filename(
                self.resource_module,
                self.resource_name)
        self.search_property_name = \
            str(layer_arguments.get('search_property_name', ""))
        self.legend_id = layer_arguments.get('legend_id', None)
        self.legend_point_id = layer_arguments.get('legend_point_id', None)
        self.value_field = layer_arguments.get('value_field', None)

    def _default_mapnik_style(self):
        """
        Makes default mapnik style
        """
        area_looks = mapnik.PolygonSymbolizer(mapnik.Color('#ffb975'))
        # ^^^ light brownish
        line_looks = mapnik.LineSymbolizer(mapnik.Color('#dd0000'), 1)
        area_looks.fill_opacity = 0.5
        layout_rule = mapnik.Rule()
        layout_rule.symbols.append(area_looks)
        layout_rule.symbols.append(line_looks)
        area_style = mapnik.Style()
        area_style.rules.append(layout_rule)
        return area_style

    def legend(self, updates=None):
        if self.legend_id is not None:
            legend_object = Legend.objects.get(id=self.legend_id)
        elif self.legend_point_id is not None:
            legend_object = LegendPoint.objects.get(id=self.legend_point_id)
        return super(WorkspaceItemAdapterShapefile, self).legend_default(
            legend_object)

    def layer(self, layer_ids=None, request=None):
        """Return layer and styles for a shapefile.

        Registered as ``shapefile_layer``

        http://127.0.0.1:8000/map/workspace/1/wms/?LAYERS=basic&SERVICE=
        WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&EXCEPTIONS=application%
        2Fvnd.ogc.se_inimage&FORMAT=image%2Fjpeg&SRS=EPSG%3A900913&BBOX=
        523838.00391791,6818214.5267836,575010.91942212,6869720.7532931&
        WIDTH=140&HEIGHT=140
        """
        layers = []
        styles = {}
        layer = mapnik.Layer(self.layer_name, coordinates.RD)
        # TODO: ^^^ translation!

        layer.datasource = mapnik.Shapefile(
            file=self.layer_filename)
        if self.legend_id is not None:
            legend = Legend.objects.get(id=self.legend_id)
            style = legend.mapnik_linestyle(value_field=str(self.value_field))
            # style = self._default_mapnik_style()
        elif self.legend_point_id is not None:
            legend_point = LegendPoint.objects.get(id=self.legend_point_id)
            style = legend_point.mapnik_style(
                value_field=str(self.value_field))
        else:
            # Show layer with default legend.
            style = self._default_mapnik_style()
        style_name = str('Area style %s::%s::%s' % (
                self.layer_filename,
                self.legend_id,
                self.value_field))
        styles[style_name] = style
        layer.styles.append(style_name)
        layers = [layer]
        return layers, styles

    def search(self, x, y, radius=None):
        """
        Hacky at the moment as searching shapefiles is harder than expected.

        x,y are google coordinates

        """
        # Set up a basic map as only map can search...
        mapnik_map = mapnik.Map(400, 400)
        mapnik_map.srs = coordinates.GOOGLE

        layers, styles = self.layer()
        for layer in layers:
            mapnik_map.layers.append(layer)
        for name in styles:
            mapnik_map.append_style(name, styles[name])
        # 0 is the first layer.
        feature_set = mapnik_map.query_point(0, x, y)
        result = []
        for feature in feature_set.features:
            try:
                if self.search_property_name:
                    name_in_shapefile = \
                        feature.properties[str(self.search_property_name)]
            except KeyError:
                # This means that the search_property_name is not a
                # valid field in the shapefile dbf.
                logger.error(
                    ('Search: The field "%s" cannot be found in '
                     'shapefile "%s". '
                     'Check your settings in lizard_shape.models.Shape.') %
                    (self.search_property_name, self.layer_name))
                name_in_shapefile = ''
                continue
            try:
                if self.value_field:
                    value_in_shapefile = \
                        feature.properties[str(self.value_field)]
            except KeyError:
                # This means that the value_field is not a
                # valid field in the shapefile dbf.
                logger.error(
                    ('Search: The field "%s" cannot be found in '
                     'shapefile "%s". Check value_field in your '
                     'legend settings.') %
                    (self.value_field, self.layer_name))
                value_in_shapefile = ''
                continue
            name = name_in_shapefile
            if value_in_shapefile:
                name += ' (%r)' % value_in_shapefile

            result.append(
                {'distance': 0.0,
                 'name': name,
                 'identifier': {id: name_in_shapefile}})

        return result

    def symbol_url(self, identifier=None, start_date=None,
                   end_date=None, icon_style=None):
        """
        Returns symbol.
        """
        if icon_style is None and self.legend_point_id is not None:
            legend_object = LegendPoint.objects.get(pk=self.legend_point_id)
            icon_style = legend_object.icon_style()
        return super(WorkspaceItemAdapterShapefile, self).symbol_url(
            identifier=identifier,
            start_date=start_date,
            end_date=end_date,
            icon_style=icon_style)
