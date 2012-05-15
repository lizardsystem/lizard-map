/*jslint browser: true */
/*jslint evil: true */
/*jslint nomen: false */
/*global $, OpenLayers, popup_click_handler, popup_hover_handler, alert,
G_PHYSICAL_MAP, G_SATELLITE_MAP, G_NORMAL_MAP, G_HYBRID_MAP, TouchHandler,
stretchOneSidebarBox */

// OpenLayers.ImgPath = "http://js.mapbox.com/theme/dark/";
OpenLayers.ImgPath = "/static_media/themes/dark/";

var layers, wms_layers, background_layers, map;
layers = [];  // Used in an associative way.
background_layers = [];  // Just the identifiers.
wms_layers = {};

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


/* L3 is multiple selection turned on? */
function multipleSelection() {
    return $("li#map-multiple-selection").hasClass("active");
}

/* L3 click on (lon, lat) in multiple select mode

Borrowed from popup_click_handler
*/
function addSelection(x, y, map) {
    var extent, radius, url, workspace_id, workspace_type;
    extent = map.getExtent();
    radius = Math.abs(extent.top - extent.bottom) / 30;  // Experimental, seems to work good
    $("#map_").css("cursor", "progress");
    url = $(".workspace").attr("data-url-lizard-map-add-selection");
    workspace_id = $(".workspace").attr("data-workspace-id");
    workspace_type = $(".workspace").attr("data-workspace-type");
    if (workspace_type === undefined) {
	workspace_type = "workspace_edit"; // Default
    }

    if (url !== undefined) {
        $.post(
            url,
            { x: x, y: y, radius: radius, srs: map.getProjection(),
              workspace_id: workspace_id, workspace_type: workspace_type},
            function (data, status, context) {
                var div;
                div = $(data).find("#edit-collage");
                $("#edit-collage").html(div.html());

                stretchOneSidebarBox();
                //show_popup(data);
                //$("#map").css("cursor", "default");
            }
        );
    }
}


// Refresh/setup background layers only when they're not available yet.
function refreshBackgroundLayers() {
    var $lizard_map_wms, selected_base_layer_name, base_layer,
    base_layer_type;
    $lizard_map_wms = $("#lizard-map-wms");
    if (!$lizard_map_wms) {
        // No element found, nothing to do.
        return;
    }
    selected_base_layer_name = $lizard_map_wms.attr("data-selected-base-layer");
    $lizard_map_wms.find(".background-layer").each(function () {
        var google_type, data_google_type, layer_name, layer_type, url,
        is_default, layer_names, identifier, is_base_layer;
        layer_type = $(this).attr("data-layer-type");
        layer_name = $(this).attr("data-layer-name");
        is_default = $(this).attr("data-default");
        is_base_layer = ($(this).attr("data-is-base-layer") === 'True');

        // Three possible identificators.
        url = $(this).attr("data-layer-url");
        layer_names = $(this).attr("data-layer-layer-names");
        data_google_type = $(this).attr("data-google-layer-type");
        identifier = url + layer_names + data_google_type;
        if ($.inArray(identifier, background_layers) === -1) {
            // Not already present, adding it.
            if (layer_type === "GOOGLE")
            {
                // default=1, physical=2, hybrid=3, satellite=4
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
                    {type: google_type,
                     transitionEffect: 'resize',
                     sphericalMercator: true});
            }
            else if (layer_type === "OSM")
            {
                base_layer = new OpenLayers.Layer.OSM(
                    layer_name, url,
                    {buffer: 0,
                     transitionEffect: 'resize'});
            }
            else if (layer_type === "WMS")
            {
                base_layer = new OpenLayers.Layer.WMS(
                    layer_name, url,
                    {'layers': layer_names,
                     'format': 'image/png',
                     'reproject': true,
                     'transparent': !is_base_layer},
                    {'isBaseLayer': is_base_layer,
                     'visibility': is_base_layer,
                     'numZoomLevels': 19,
                     'units': "m",
                     'maxExtent': new OpenLayers.Bounds(
                         -128 * 156543.03390625,
                         -128 * 156543.03390625,
                       128 * 156543.03390625,
                       128 * 156543.03390625
                     ),
                     'transitionEffect': 'resize',
                     'buffer': 1}
                );
            }
            else if (layer_type === "TMS")
            {
                base_layer = new OpenLayers.Layer.TMS(
                    layer_name,
                    url,
                    {layername: layer_names,
                     type: 'png',
                     tileSize: new OpenLayers.Size(256, 256)
                    }
                );
            }
            // layers.base_layer
            map.addLayer(base_layer);
            background_layers.push(identifier);
            // Set base layer if is_default.
            if ((selected_base_layer_name === "") &&
                (is_default === "True")) {

                map.setBaseLayer(base_layer);
            } else if (selected_base_layer_name === layer_name) {
                map.setBaseLayer(base_layer);
            }
        }
    });
}



function refreshWorkspaceLayers() {
    var $lizard_map_wms, wms_layers, osm_url;
    $lizard_map_wms = $("#lizard-map-wms");
    $(".workspace-layer").each(function () {
        var workspace_id, workspace_name, workspace_wms;
        workspace_id = $(this).attr("data-workspace-id");
        workspace_name = $(this).attr("data-workspace-name");
        workspace_wms = $(this).attr("data-workspace-wms");
        if (layers[workspace_id] === undefined) {
            // It doesn't exist yet.
            layers[workspace_id] = new OpenLayers.Layer.WMS(
                workspace_name,
                workspace_wms,
                {layers: 'basic'},
                {singleTile: true,
                 transitionEffect: 'resize',
                 displayInLayerSwitcher: false,
                 isBaseLayer: false});
            layers[workspace_id].mergeNewParams({'random': Math.random()});
            map.addLayer(layers[workspace_id]);
        } else {
            // It exists: refresh it.
            layers[workspace_id].mergeNewParams({'random': Math.random()});
        }
    });
}



function refreshWmsLayers() {
    // Add wms layers from workspace items.
    var $lizard_map_wms, osm_url, i, ids_found;
    ids_found = [];
    $lizard_map_wms = $("#lizard-map-wms");
    $(".workspace-wms-layer").each(function () {
        var name, url, params, options, id;
        // WMS id, different than workspace ids.
        id = $(this).attr("data-workspace-wms-id");
        ids_found.push(id);
        name = $(this).attr("data-workspace-wms-name");
        url = $(this).attr("data-workspace-wms-url");
        params = $(this).attr("data-workspace-wms-params");
        options = $(this).attr("data-workspace-wms-options");
        if (wms_layers[id] === undefined) {
            // Create it.
            wms_layers[id] = new OpenLayers.Layer.WMS(
                name, url, $.parseJSON(params), $.parseJSON(options));
            map.addLayer(wms_layers[id]);
        }
    });
    // Remove unused ones.
    $.each(wms_layers, function (key, value) {
        if ($.inArray(key, ids_found) === -1) {
            // Remove now-unused layer.
            map.removeLayer(value);
            delete wms_layers[key];
        }
    });
}


/* Adds all layers (base + workspaces) to map. Refreshes all
workspaces. Layers from other sources are assumed to be 'static' */
function refreshLayers() {
    // Set up all layers.
    refreshBackgroundLayers();
    refreshWorkspaceLayers();
    refreshWmsLayers();
}


function ZoomSlider(options) {
    this.control = new OpenLayers.Control.PanZoomBar(options);

    OpenLayers.Util.extend(this.control, {
        draw: function (px) {
            // initialize our internal div
            OpenLayers.Control.prototype.draw.apply(this, arguments);
            px = this.position.clone();

            // place the controls
            this.buttons = [];

            var sz, centered;
            sz = new OpenLayers.Size(18, 18);
            centered = new OpenLayers.Pixel(px.x + sz.w / 2, px.y);

            this._addButton("zoomin", "zoom-plus-mini.png", centered.add(0, 5), sz);
            centered = this._addZoomBar(centered.add(0, sz.h + 5));
            this._addButton("zoomout", "zoom-minus-mini.png", centered, sz);
            return this.div;
        }
    });
    return this.control;
}


function showMap() {
    var options, base_layer, MapClickControl, MapHoverControl,
        map_click_control, zoom_panel, map_hover_control,
        javascript_click_handler_name, javascript_hover_handler_name,
        $lizard_map_wms, projection, display_projection, start_extent,
        start_extent_left, start_extent_top, start_extent_right,
        start_extent_bottom, max_extent, max_extent_left, max_extent_top,
        max_extent_right, max_extent_bottom;

    window.setUpMapDimensions();

    // Make custom OpenLayers._getScriptLocation
    // OpenLayers (OL) cannot get its script location if the filename
    // OpenLayers.js has been changed.
    // This function is needed when loading images etc for OL.
    OpenLayers._getScriptLocation = function () {
        //return $("#openlayers-script").attr("data-openlayers-url");
        return "/static_media/openlayers/";
    };

    // Find client-side extra data.
    $lizard_map_wms = $("#lizard-map-wms");

    projection = $lizard_map_wms.attr("data-projection");
    display_projection = $lizard_map_wms.attr("data-display-projection");

    start_extent_left = $lizard_map_wms.attr("data-start-extent-left");
    start_extent_top = $lizard_map_wms.attr("data-start-extent-top");
    start_extent_right = $lizard_map_wms.attr("data-start-extent-right");
    start_extent_bottom = $lizard_map_wms.attr("data-start-extent-bottom");
    start_extent = new OpenLayers.Bounds(
        parseFloat(start_extent_left), parseFloat(start_extent_bottom),
        parseFloat(start_extent_right), parseFloat(start_extent_top));

    max_extent_left = $lizard_map_wms.attr("data-max-extent-left");
    max_extent_top = $lizard_map_wms.attr("data-max-extent-top");
    max_extent_right = $lizard_map_wms.attr("data-max-extent-right");
    max_extent_bottom = $lizard_map_wms.attr("data-max-extent-bottom");
    max_extent = new OpenLayers.Bounds(
        parseFloat(max_extent_left), parseFloat(max_extent_bottom),
        parseFloat(max_extent_right), parseFloat(max_extent_top));

    // Set up projection and bounds.
    if (projection === "EPSG:900913")
    {
        options = {
            projection: new OpenLayers.Projection(projection),
            displayProjection: new OpenLayers.Projection(display_projection),  // "EPSG:4326"
            units: "m",
            maxResolution: 78271.516964,
            numZoomLevels: 18,
            maxExtent: max_extent,
            controls: []
        };
    }
    else if (projection === "EPSG:28992")
    {
        options = {
            projection: new OpenLayers.Projection(projection),
            displayProjection: new OpenLayers.Projection(display_projection),
            units: "m",
            resolutions: [364, 242, 161, 107, 71, 47, 31, 21, 14, 9, 6, 4, 2.7, 1.8, 0.9, 0.45, 0.2],
            maxExtent: max_extent,
            controls: []
        };
    }
    else
    {
        alert("Lizard-map onjuist geconfigureerd. Wilt U een kaart op deze pagina? Gebruik anders een andere template.");
    }

    // Map is globally defined.
    map = new OpenLayers.Map('map', options);
    // OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;

    refreshLayers();

    // Set up controls, zoom and center.
    map.addControl(new OpenLayers.Control.LayerSwitcher({'ascending': true}));
    // Click handling.
    javascript_click_handler_name = $lizard_map_wms.attr("data-javascript-click-handler");
    if (javascript_click_handler_name) {
        MapClickControl = OpenLayers.Class(OpenLayers.Control, {
            defaultHandlerOptions: {
                'single': true,
                'double': false,
                'pixelTolerance': null,
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
                        'click': this.trigger,
                        'touchstart': this.trigger
                    }, this.handlerOptions
                );
            },

            trigger: function (e) {
                var lonlat;
                lonlat = map.getLonLatFromViewPortPx(e.xy);
                if (multipleSelection()) {
                    addSelection(lonlat.lon, lonlat.lat, map);
                } else {
                    eval(javascript_click_handler_name)(
                        lonlat.lon, lonlat.lat, map);
                }
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
                eval(javascript_hover_handler_name)(
                    lonlat.lon, lonlat.lat, map);

            },

            onMove: function (evt) {
                $("#hover-popup").remove();
            }
        });

        map_hover_control = new MapHoverControl();
        map.addControl(map_hover_control);
        map_hover_control.activate();
    }

    zoom_panel = new OpenLayers.Control.Panel();
    zoom_panel.addControls([ new ZoomSlider({ zoomStopHeight: 3 }) ]);
    map.addControl(zoom_panel);
    map.addControl(new OpenLayers.Control.Navigation());

    // Zoom to startpoint. Important to parse numbers, else a bug in
    // OpenLayers will initially prevent "+" from working.
    //
    // Saving and subsequently restoring a start_extent often results in a
    // zoom level that is decreased by -1. This might be due to rounding
    // errors. By passing true to zoomToExtent, we will get the zoom
    // level that most closely fits the specified bounds.
    // See #2762 and #2794.
    map.zoomToExtent(start_extent, true);
}


/*
Creates parameters part of url
*/
function getMapUrl() {
    var extent, srs, activelayers, url, width, height, i;
    extent  = map.getExtent();
    extent  = [extent.left, extent.bottom,
               extent.right, extent.top].join(',');
    srs = map.getProjectionObject();
    activelayers = [];
    url = "?";
    width   = map.getSize().w;
    height  = map.getSize().h;

    for (i = map.layers.length - 1; i >= 0; i -= 1) {
        if (!map.layers[i].getVisibility()) {
            continue;
        }
        if (!map.layers[i].calculateInRange()) {
            continue;
        }
	if (!map.layers[i].params) {
	    /* Why does this happen? I don't know, but this appears necessary. */
	    continue;
	}

        activelayers[activelayers.length] = map.layers[i].params.LAYERS;
    }

    activelayers = activelayers.join(',');

    url += "LAYERS=" + activelayers;
    url += "&SRS=" + srs;
    url += "&BBOX=" + extent;
    url += "&WIDTH=" + width;
    url += "&HEIGHT=" + height;

    return url;
}

/*
Replaces a href attr. of 'Download' subelement
*/
function setDownloadImageLink() {
    $('a#download-map').click(function (e) {
        var url;
        url = $(this).attr("href");

	url += getMapUrl();
        // Because the result is an image, a popup will occur.
        window.location = url;
        return false;
    });
}


/* map-multiple-selection button */
function setUpMultipleSelection() {
    $("#map-multiple-selection").live("click", function () {
        $(this).toggleClass("active");
    });
}


$(document).ready(function () {
    showMap();
    setDownloadImageLink();
    setUpMultipleSelection();
});
