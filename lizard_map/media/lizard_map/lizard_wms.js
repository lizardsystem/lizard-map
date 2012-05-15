/*jslint browser: true */
/*jslint evil: true */
/*jslint nomen: false */
/*global $, OpenLayers, popup_click_handler, popup_hover_handler, alert,
G_PHYSICAL_MAP, G_SATELLITE_MAP, G_NORMAL_MAP, G_HYBRID_MAP, TouchHandler,
stretchOneSidebarBox */

// OpenLayers.ImgPath = "http://js.mapbox.com/theme/dark/";
//OpenLayers.ImgPath = "/static_media/themes/dark/";

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
                     'maxResolution': 364,
                     'transparent': !is_base_layer},
                    {'isBaseLayer': is_base_layer,
                     'visibility': is_base_layer,
                     'transitionEffect': 'resize',
                     'buffer': 1}
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
    lizard_leaflet.showMap();
    setDownloadImageLink();
    setUpMultipleSelection();
});
