/*jslint browser: true */
/*jslint evil: true */
/*global $, OpenLayers, popup_click_handler, popup_hover_handler, alert,
G_PHYSICAL_MAP, TouchHandler */
var layers, map;
layers = [];

//layers is globally defined
function updateLayer(workspace_id) {
    layers[workspace_id].mergeNewParams({'random': Math.random()});
}


function updateLayers() {
    var i;
    for (i = 0; i < layers.length; i += 1) {
        if (layers[i] !== undefined) {
            updateLayer(i);
        }
    }
}


function showMap() {
    var options, base_layer, MapClickControl, MapHoverControl,
        map_click_control, map_hover_control,
        javascript_click_handler_name, javascript_hover_handler_name,
        $lizard_map_wms, startlocation_x, startlocation_y,
        startlocation_zoom, projection, display_projection,
        base_layer_type, wms_url, wms_layers, osm_url;

    // Find client-side extra data.
    $lizard_map_wms = $("#lizard-map-wms");

    projection = $lizard_map_wms.attr("data-projection");
    display_projection = $lizard_map_wms.attr("data-display-projection");
    base_layer_type = $lizard_map_wms.attr("data-base-layer-type");

    startlocation_x = $lizard_map_wms.attr("data-startlocation-x");
    startlocation_y = $lizard_map_wms.attr("data-startlocation-y");
    startlocation_zoom = $lizard_map_wms.attr("data-startlocation-zoom");

    // Set up projection and bounds.
    if (projection === "EPSG:900913")
    {
        options = {
            projection: new OpenLayers.Projection(projection),
            displayProjection: new OpenLayers.Projection(display_projection),  // "EPSG:4326"
            units: "m",
            numZoomLevels: 18,
            maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34)
        };
    }
    else if (projection === "EPSG:28992")
    {
        options = {
            projection: new OpenLayers.Projection(projection),
            displayProjection: new OpenLayers.Projection(display_projection),
            units: "m",
            resolutions: [364, 242, 161, 107, 71, 47, 31, 21, 14, 9, 6, 4, 2.7, 1.8],
            maxExtent: new OpenLayers.Bounds(0, 300000, 300000, 600000)
        };
    }
    else
    {
        alert("Lizard-map onjuist geconfigureerd. Projection: " + projection);
    }

    // Map is globally defined.
    map = new OpenLayers.Map('map', options);
    // OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;

    // Set up base layer.
    if (base_layer_type === "OSM")
    {
        osm_url = $lizard_map_wms.attr("data-base-layer-osm");
        base_layer = new OpenLayers.Layer.OSM(
        "Openstreetmap",
        osm_url,
        {buffer: 0});
    }
    else if (base_layer_type === "WMS")
    {
        wms_url = $lizard_map_wms.attr("data-base-layer-wms");
        wms_layers = $lizard_map_wms.attr("data-base-layer-wms-layers");
        base_layer = new OpenLayers.Layer.WMS(
            'Topografische kaart',
            wms_url,
	    {'layers': wms_layers, 'format': 'image/png', 'maxResolution': 364},
            {'isBaseLayer': true, 'buffer': 1}
        );
    }
    else if (base_layer_type === "GOOGLE")
    {
        base_layer = new OpenLayers.Layer.Google(
            "Google Physical",
            {type: G_PHYSICAL_MAP, sphericalMercator: true});
    }
    map.addLayer(base_layer);

    // Add our own data layers.
    $(".workspace-layer").each(function () {
        var workspace_id, workspace_name, workspace_wms;
        workspace_id = $(this).attr("data-workspace-id");
        workspace_name = $(this).attr("data-workspace-name");
        workspace_wms = $(this).attr("data-workspace-wms");
        layers[workspace_id] = new OpenLayers.Layer.WMS(
            workspace_name,
            workspace_wms,
            {layers: 'basic'},
            {singleTile: true,
             isBaseLayer: false});
        map.addLayer(layers[workspace_id]);
    });

    // Set up controls, zoom and center.
    map.addControl(new OpenLayers.Control.LayerSwitcher({'ascending': false}));
    // Click handling.
    javascript_click_handler_name = $lizard_map_wms.attr("data-javascript-click-handler");
    if (javascript_click_handler_name !== undefined) {
        MapClickControl = OpenLayers.Class(OpenLayers.Control, {
            defaultHandlerOptions: {
                'single': true,
                'double': false,
                'pixelTolerance': 0,
                'stopSingle': false,
                'stopDouble': false
            },

            initialize: function (options) {
                this.handlerOptions = OpenLayers.Util.extend(
                    {}, this.defaultHandlerOptions
                );
                OpenLayers.Control.prototype.initialize.apply(
                    this, arguments
                );
                this.handler = new OpenLayers.Handler.Click(
                    this, {
                        'click': this.trigger
                    }, this.handlerOptions
                );
            },

            trigger: function (e) {
                var lonlat;
                lonlat = map.getLonLatFromViewPortPx(e.xy);
                eval(javascript_click_handler_name)(lonlat.lon, lonlat.lat, map);
            }
        });
        map_click_control = new MapClickControl();
        map.addControl(map_click_control);
        map_click_control.activate();
    }
    // Hover handling.
    javascript_hover_handler_name = $lizard_map_wms.attr("data-javascript-hover-handler");
    if (javascript_hover_handler_name !== undefined) {
        // Example code from
        // http://trac.openlayers.org/browser/trunk/openlayers/examples/hover-handler.html
        MapHoverControl = OpenLayers.Class(OpenLayers.Control, {
            defaultHandlerOptions: {
                'delay': 500,
                'pixelTolerance': null,
                'stopMove': false
            },

            initialize: function (options) {
                this.handlerOptions = OpenLayers.Util.extend(
                    {}, this.defaultHandlerOptions
                );
                OpenLayers.Control.prototype.initialize.apply(
                    this, arguments
                );
                this.handler = new OpenLayers.Handler.Hover(
                    this,
                    {'pause': this.onPause, 'move': this.onMove},
                    this.handlerOptions
                );
            },

            onPause: function (e) {
                var lonlat;
                lonlat = map.getLonLatFromViewPortPx(e.xy);
                eval(javascript_hover_handler_name)(lonlat.lon, lonlat.lat, map);
            },

            onMove: function (evt) {
                $("#hover-popup").remove();
            }
        });

        map_hover_control = new MapHoverControl();
        map.addControl(map_hover_control);
        map_hover_control.activate();
    }

    // Zoom to startpoint. Important to parse numbers, else a bug in
    // OpenLayers will initially prevent "+" from working.
    map.setCenter(
        new OpenLayers.LonLat(parseFloat(startlocation_x), parseFloat(startlocation_y)),
        parseFloat(startlocation_zoom));


}


$(document).ready(showMap);
