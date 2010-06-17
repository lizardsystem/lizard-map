# TODO: this file is currently unused.  Perhaps we *do* want generic shapefile
# rendering, though, so it is retained as example code.  2010-05-14.
import mapnik
import pkg_resources

from lizard_map import coordinates
from workspace import WorkspaceItemAdapter

class WorkspaceItemAdapterShapefile(WorkspaceItemAdapter):
    def layer(self):
        """Return layer and styles for a shapefile.

        Registered as ``shapefile_layer``
        """
        layers = []
        styles = {}
        layer = mapnik.Layer("Waterlichamen", coordinates.RD)
        # TODO: ^^^ translation!
        layer.datasource = mapnik.Shapefile(
            file=pkg_resources.resource_filename(
                'lizard_map',
                'test_shapefiles/KRWwaterlichamen_vlakken.shp'))
        area_looks = mapnik.PolygonSymbolizer(mapnik.Color('#ffb975')) #light brownish
        line_looks = mapnik.LineSymbolizer(mapnik.Color('#dd0000'), 1)
        area_looks.fill_opacity = 0.5
        layout_rule = mapnik.Rule()
        layout_rule.symbols.append(area_looks)
        layout_rule.symbols.append(line_looks)
        area_style = mapnik.Style()
        area_style.rules.append(layout_rule)
        styles['Area style'] = area_style
        layer.styles.append('Area style')
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
            name_in_shapefile = feature.properties['WGBNAAM']
            result.append({'name': name_in_shapefile})

        return result
