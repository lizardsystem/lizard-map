/*jslint browser: true */
/*jslint evil: true */
/*global $, OpenLayers, popup_click_handler, popup_hover_handler */
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
    var options, openstreetmapLayer, MapClickControl, MapHoverControl,
        map_click_control, map_hover_control,
        javascript_click_handler_name, javascript_hover_handler_name,
        $lizard_map_wms;

    // Find client-side extra data.
    $lizard_map_wms = $("#lizard-map-wms");

    // Set up projection and bounds.
    options = {
        projection: new OpenLayers.Projection("EPSG:900913"),
        displayProjection: new OpenLayers.Projection("EPSG:4326"),
        units: "m",
        numZoomLevels: 18,
        maxExtent: new OpenLayers.Bounds(129394, 6659216, 1335570, 7306790)
    };
    map = new OpenLayers.Map('map', options);

    // Set up base layer.
    openstreetmapLayer = new OpenLayers.Layer.OSM(
        "Openstreetmap",
        "http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png",
        {buffer: 0});
    map.addLayer(openstreetmapLayer);

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
    javascript_hover_handler_name = $lizard_map_wms.attr("data-javascript-click-handler");
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
    // Extend zooming.
    map.setCenter(new OpenLayers.LonLat(550000, 6850000), 10);
}


$(document).ready(showMap);
