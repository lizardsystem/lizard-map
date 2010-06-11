# TODO: this file is currently unused.  Perhaps we *do* want generic shapefile
# rendering, though, so it is retained as example code.  2010-05-14.
import mapnik
import pkg_resources

from lizard_map import coordinates
from lizard_map.workspace import WorkspaceItemAdapter


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
        area_looks = mapnik.PolygonSymbolizer(mapnik.Color('#ffb975'))
        # ^^^ light brownish
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
