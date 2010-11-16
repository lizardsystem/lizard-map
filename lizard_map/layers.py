from shapely.geometry import Point
from shapely.wkt import loads
import logging
import mapnik
import osgeo.ogr
import pkg_resources

from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils import simplejson as json

from lizard_map import coordinates
from lizard_map.models import Legend
from lizard_map.models import LegendPoint
from lizard_map.utility import float_to_string
from lizard_map.workspace import WorkspaceItemAdapter

logger = logging.getLogger(__name__)


class WorkspaceItemAdapterShapefile(WorkspaceItemAdapter):
    """Render a WorkspaceItem using a shape file.

    Instance variables:
    * layer_name -- name of the WorkspaceItem that is rendered

    * search_property_name (optional) -- name of shapefile feature
      used in search results: mouse over, title of popup

    * search_property_id (optional) -- id of shapefile feature. Used
      to find the feature back.

    * value_field (optional, used by legend) -- value field for legend
      (takes 'value' if not given)

    * value_name (optional) -- name for value field

    * display_fields (optional) -- list of which columns to
      show in a popup.

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
            layer_arguments.get('search_property_name', "")
        self.search_property_id = \
            layer_arguments.get('search_property_id', "")
        self.legend_id = layer_arguments.get('legend_id', None)
        self.legend_point_id = layer_arguments.get('legend_point_id', None)
        self.value_field = layer_arguments.get('value_field', None)
        self.value_name = layer_arguments.get('value_name', None)
        self.display_fields = layer_arguments.get('display_fields', [])
        if not self.display_fields:
            self.display_fields = [
                {'name': self.value_name, 'field': self.value_field}]

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

    @property
    def _legend_object(self):
        if self.legend_id is not None:
            legend_object = Legend.objects.get(id=self.legend_id)
        elif self.legend_point_id is not None:
            legend_object = LegendPoint.objects.get(id=self.legend_point_id)
        return legend_object

    def legend(self, updates=None):
        return super(WorkspaceItemAdapterShapefile, self).legend_default(
            self._legend_object)

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
        Search area, line or point.

        Make sure that value_field, search_property_id,
        search_property_name are valid columns in your shapefile.

        x,y are google coordinates

        !!!assumes the shapefile has RD projection!

        Note: due to mapnik #503 (http://trac.mapnik.org/ticket/503)
        the search does not work for lines and points. So the
        implementation was done with shapely.

        """
        if not self.search_property_name:
            # We don't have anything to return, so don't search.
            return []

        rd_x, rd_y = coordinates.google_to_rd(x, y)
        query_point = Point(rd_x, rd_y)
        ds = osgeo.ogr.Open(self.layer_filename)
        lyr = ds.GetLayer()
        lyr.ResetReading()
        feat = lyr.GetNextFeature()

        results = []

        while feat is not None:
            geom = feat.GetGeometryRef()
            if geom:
                item = loads(geom.ExportToWkt())
                distance = query_point.distance(item)
                feat_items = feat.items()

                if not radius or (radius is not None and distance < radius):
                    # Found an item.
                    if self.search_property_name not in feat_items:
                        # This means that the search_property_name is not a
                        # valid field in the shapefile dbf.
                        logger.error(
                            ('Search: The field "%s" cannot be found in '
                             'shapefile "%s". '
                             'Check your settings in '
                             'lizard_shape.models.Shape.') %
                            (self.search_property_name, self.layer_name))
                        break  # You don't have to search other rows.
                    name = str(feat_items[self.search_property_name])

                    if self.value_field:
                        if self.value_field not in feat_items:
                            # This means that the value_field is not a
                            # valid field in the shapefile dbf.
                            logger.error(
                                ('Search: The field "%s" cannot be found in '
                                 'shapefile "%s". Check value_field in your '
                                 'legend settings.') %
                                (self.value_field, self.layer_name))
                            break  # You don't have to search other rows.
                        name += ' - %s=%s' % (
                            self.value_name,
                            str(float_to_string(feat_items[self.value_field])))
                    result = {'distance': distance,
                              'name': name,
                              'google_coords':
                              coordinates.rd_to_google(*item.coords[0]),
                              'workspace_item': self.workspace_item}
                    if (self.search_property_id and
                        self.search_property_id in feat_items):
                        result.update(
                            {'identifier':
                                 {'id': feat_items[self.search_property_id]}})
                    results.append(result)
            feat = lyr.GetNextFeature()
        results = sorted(results, key=lambda a: a['distance'])

        return results

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

    def location(self, id):
        """Find id in shape. Used by html function."""

        ds = osgeo.ogr.Open(self.layer_filename)
        lyr = ds.GetLayer()
        lyr.ResetReading()
        feat = lyr.GetNextFeature()

        item, google_x, google_y, feat_items = None, None, None, None
        while feat is not None:
            geom = feat.GetGeometryRef()
            feat_items = feat.items()
            if geom and feat_items[self.search_property_id] == id:
                item = loads(geom.ExportToWkt())
                google_x, google_y = coordinates.rd_to_google(*item.coords[0])
                break
            feat = lyr.GetNextFeature()

        values = []  # contains {'name': <name>, 'value': <value>}
        for field in self.display_fields:
            values.append({'name': field['name'],
                           'value': feat_items[str(field['field'])]})
        name = feat_items[self.search_property_name]
        return {
            'name': name,
            'shortname': name,
            'value_name': self.value_name,
            'value': feat_items[self.value_field],
            'values': values,
            'object': feat_items,
            'workspace_item': self.workspace_item,
            'identifier': {'id': id},
            }

    def html(self, snippet_group=None, identifiers=None, layout_options=None):
        """
        Renders table with shape attributes.
        """
        if snippet_group:
            snippets = snippet_group.snippets.all()
            identifiers = [snippet.identifier for snippet in snippets]
        display_group = [
            self.location(**identifier) for identifier in identifiers]
        add_snippet = False
        if layout_options and 'add_snippet' in layout_options:
            add_snippet = layout_options['add_snippet']

        # Testing: images for timeseries
        img_url = reverse(
                "lizard_map.workspace_item_image",
                kwargs={'workspace_item_id': self.workspace_item.id},
                )
        identifiers_escaped = [json.dumps(identifier).replace('"', '%22')
                               for identifier in identifiers]
        img_url = img_url + '?' + '&'.join(['identifier=%s' % i for i in
                                            identifiers_escaped])

        return render_to_string(
            'lizard_map/popup_shape.html',
            {'display_group': display_group,
             'add_snippet': add_snippet,
             'symbol_url': self.symbol_url(),
             'img_url': img_url})

    def image(self, identifiers, start_date, end_date,
              width=380.0, height=250.0, layout_extra=None):
        """
        Displays timeseries graph.

        This function can only be used in combination with
        lizard-shape. Maybe it's better to move the whole file to
        lizard-shape.
        """
        import datetime

        from lizard_shape.models import His
        from lizard_map.adapter import Graph

        line_styles = self.line_styles(identifiers)

        today = datetime.datetime.now()
        graph = Graph(start_date, end_date,
                      width=width, height=height, today=today)
        graph.axes.grid(True)

        his = His.objects.all()[0]  # Test: take first object.
        hf = his.hisfile()
        parameter = hf.parameters()[2]  # Test: take first parameter.
        location = hf.locations()[0]  # Test: take first location.

        start_datetime = datetime.datetime.combine(start_date, datetime.time())
        end_datetime = datetime.datetime.combine(end_date, datetime.time())
        for identifier in identifiers:
            timeseries = hf.get_timeseries(
                location, parameter, start_datetime, end_datetime, list)

            # Plot data.
            dates = [row[0] for row in timeseries]
            values = [row[1] for row in timeseries]
            graph.axes.plot(dates, values,
                            lw=1,
                            color=line_styles[str(identifier)]['color'],
                            label=parameter)

        # if legend:
        #     graph.legend()

        graph.add_today()
        return graph.http_png()
