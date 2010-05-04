import mapnik
import pkg_resources


def shapefile_layer():
    """Return layer and styles for a shapefile.

    Registered as ``shapefile_layer``
    """
    layers = []
    styles = {}
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
    area_looks = mapnik.PolygonSymbolizer(mapnik.Color('lightblue'))
    line_looks = mapnik.LineSymbolizer(mapnik.Color('blue'), 1)
    area_looks.fill_opacity = 1
    layout_rule = mapnik.Rule()
    layout_rule.symbols.append(area_looks)
    layout_rule.symbols.append(line_looks)
    area_style = mapnik.Style()
    area_style.rules.append(layout_rule)
    styles['Area style'] = area_style
    layer.styles.append('Area style')
    layers = [layer]
    return layers, styles
