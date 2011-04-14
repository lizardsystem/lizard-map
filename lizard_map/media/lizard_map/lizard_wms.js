/*jslint browser: true */
/*jslint evil: true */
/*global $, OpenLayers, popup_click_handler, popup_hover_handler, alert,
G_PHYSICAL_MAP, G_SATELLITE_MAP, G_NORMAL_MAP, G_HYBRID_MAP, TouchHandler */


var layers, map;
layers = []; // used in an associative way
//layer_names = []; // stores all names, so we can loop through the layers

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


/* Adds all layers (base + workspaces) to map. Refreshes all
workspaces. Layers from other sources are assumed to be 'static' */
function refreshLayers() {
    var $lizard_map_wms, base_layer,
        base_layer_type, wms_url, wms_layers, osm_url;

    // Remove all old layers.
    layers = [];
    while (map.layers.length > 0) {
        map.removeLayer(map.layers[0]);
    }

    // Set up all layers.
    $lizard_map_wms = $("#lizard-map-wms");

    $lizard_map_wms.find(".background-layer").each(function () {
        var google_type, data_google_type, layer_name, layer_type, url,
            is_default, layer_names;
        layer_type = $(this).attr("data-layer-type");
        layer_name = $(this).attr("data-layer-name");
        is_default = $(this).attr("data-default");

        if (layer_type === "GOOGLE")
        {
            // default=1, physical=2, hybrid=3, satellite=4
            data_google_type = $(this).attr("data-google-layer-type");
            if (data_google_type === "2") {
                google_type = G_PHYSICAL_MAP;
            }
            else if (data_google_type === "3") {
                google_type = G_HYBRID_MAP;
            }
            else if (data_google_type === "4") {
                google_type = G_SATELLITE_MAP;
            } else {
                google_type = G_NORMAL_MAP;
            }
            base_layer = new OpenLayers.Layer.Google(
                layer_name,
                {type: google_type, sphericalMercator: true});
        }
        else if (layer_type === "OSM")
        {
            url = $(this).attr("data-layer-url");
            base_layer = new OpenLayers.Layer.OSM(
                layer_name, url, {buffer: 0});
        }
        else if (layer_type === "WMS")
        {
            url = $(this).attr("data-layer-url");
            layer_names = $(this).attr("data-layer-layer-names");
            base_layer = new OpenLayers.Layer.WMS(
                layer_name, wms_url,
                {'layers': layer_names, 'format': 'image/png',
                 'maxResolution': 364},
                {'isBaseLayer': true, 'buffer': 1}
            );
        }
        // layers.base_layer
        map.addLayer(base_layer);
        // Set base layer if is_default.
        if (is_default === "True") {
            map.setBaseLayer(base_layer);
        }
    });
    // base_layer_type = $lizard_map_wms.attr("data-base-layer-type");

    // // Set up base layer.
    // if (base_layer_type === "OSM")
    // {
    //     osm_url = $lizard_map_wms.attr("data-base-layer-osm");
    //     base_layer = new OpenLayers.Layer.OSM(
    //     "Openstreetmap",
    //     osm_url,
    //     {buffer: 0});
    // }
    // else if (base_layer_type === "WMS")
    // {
    //     wms_url = $lizard_map_wms.attr("data-base-layer-wms");
    //     wms_layers = $lizard_map_wms.attr("data-base-layer-wms-layers");
    //     base_layer = new OpenLayers.Layer.WMS(
    //         'Topografische kaart',
    //         wms_url,
    //         {'layers': wms_layers, 'format': 'image/png', 'maxResolution': 364},
    //         {'isBaseLayer': true, 'buffer': 1}
    //     );
    // }
    // else if (base_layer_type === "GOOGLE")
    // {
    //     base_layer = new OpenLayers.Layer.Google(
    //         "Google Physical",
    //         {type: G_PHYSICAL_MAP, sphericalMercator: true});
    // }
    // layers.base_layer = base_layer;
    // map.addLayer(base_layer);

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
        layers[workspace_id].mergeNewParams({'random': Math.random()});
        map.addLayer(layers[workspace_id]);
    });

    // Add wms layers from workspace items.
    $(".workspace-wms-layer").each(function () {
        var name, url, params, options, id;
        // WMS id, different than workspace ids.
        id = $(this).attr("data-workspace-wms-id");
        name = $(this).attr("data-workspace-wms-name");
        url = $(this).attr("data-workspace-wms-url");
        params = $(this).attr("data-workspace-wms-params");
        options = $(this).attr("data-workspace-wms-options");
        layers[id] = new OpenLayers.Layer.WMS(
            name, url, $.parseJSON(params), $.parseJSON(options));
        map.addLayer(layers[id]);
    });
}


function showMap() {
    var options, base_layer, MapClickControl, MapHoverControl,
        map_click_control, map_hover_control,
        javascript_click_handler_name, javascript_hover_handler_name,
        $lizard_map_wms, projection, display_projection, start_extent,
        start_extent_left, start_extent_top, start_extent_right,
        start_extent_bottom, max_extent, max_extent_left, max_extent_top,
        max_extent_right, max_extent_bottom;

    // Find client-side extra data.
    $lizard_map_wms = $("#lizard-map-wms");

    projection = $lizard_map_wms.attr("data-projection");
    display_projection = $lizard_map_wms.attr("data-display-projection");

    start_extent_left = $lizard_map_wms.attr("data-start-extent-left");
    start_extent_top = $lizard_map_wms.attr("data-start-extent-top");
    start_extent_right = $lizard_map_wms.attr("data-start-extent-right");
    start_extent_bottom = $lizard_map_wms.attr("data-start-extent-bottom");
    start_extent = new OpenLayers.Bounds(
        parseFloat(start_extent_left), parseFloat(start_extent_top),
        parseFloat(start_extent_right), parseFloat(start_extent_bottom));

    max_extent_left = $lizard_map_wms.attr("data-max-extent-left");
    max_extent_top = $lizard_map_wms.attr("data-max-extent-top");
    max_extent_right = $lizard_map_wms.attr("data-max-extent-right");
    max_extent_bottom = $lizard_map_wms.attr("data-max-extent-bottom");
    max_extent = new OpenLayers.Bounds(
        parseFloat(max_extent_left), parseFloat(max_extent_top),
        parseFloat(max_extent_right), parseFloat(max_extent_bottom));

    // Set up projection and bounds.
    if (projection === "EPSG:900913")
    {
        options = {
            projection: new OpenLayers.Projection(projection),
            displayProjection: new OpenLayers.Projection(display_projection),  // "EPSG:4326"
            units: "m",
            numZoomLevels: 18,
            maxExtent: max_extent
        };
    }
    else if (projection === "EPSG:28992")
    {
        options = {
            projection: new OpenLayers.Projection(projection),
            displayProjection: new OpenLayers.Projection(display_projection),
            units: "m",
            resolutions: [364, 242, 161, 107, 71, 47, 31, 21, 14, 9, 6, 4, 2.7, 1.8, 0.9, 0.45, 0.2],
            maxExtent: max_extent
        };
    }
    else
    {
        alert("Lizard-map onjuist geconfigureerd. Staat 'lizard_map.context_processors.processor.processor' in je context processors? Is de lizard_map fixture geladen?");
    }

    // Map is globally defined.
    map = new OpenLayers.Map('map', options);
    // OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;

    refreshLayers();

    // Set up controls, zoom and center.
    map.addControl(new OpenLayers.Control.LayerSwitcher({'ascending': true}));
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
    map.setCenter(start_extent.getCenterLonLat(),
                  map.getZoomForExtent(start_extent));

}


$(document).ready(showMap);
