// jslint configuration; btw: don't put a space before 'jslint' below.
/*jslint browser: true */
/*global $, OpenLayers, window, updateLayer, updateLayers,
stretchOneSidebarBox, reloadGraphs, fillSidebar, show_popup,
hover_popup, layers, map */

var animationTimer, transparencyTimer;

// if (typeof(console) === 'undefined') {
//     // Prevents the firebug console from throwing errors in browsers other
//     // than Firefox/Chrome/Chromium
//     // From http://gist.github.com/384113
//     var console = {};
//     console.log = function () {};
// }


function setSliderDate(slider_value) {
    $.ajax({
        type: "POST",
        url: $("#animation-slider").attr("data-ajax-path"),
        data: "slider_value=" + slider_value,
        success: function (data) {
            // Update the date label span with the returned data
            $('span#selected-date').html($.parseJSON(data));
        }
    });
}


function setUpAnimationSlider() {
    var workspace_item_id;
    $("#animation-slider").slider({
        min: parseInt($("#animation-slider").attr("data-min"), 10),
        max: parseInt($("#animation-slider").attr("data-max"), 10),
        step: parseInt($("#animation-slider").attr("data-step"), 10),
        value: parseInt($("#animation-slider").attr("data-value"), 10),
        slide: function (event, ui) {
            if (animationTimer) {
                clearTimeout(animationTimer);
            }
            animationTimer = setTimeout(
                function () {
                    // Only run after nothing happened for 300ms.
                    setSliderDate(ui.value);
                },
                300);
        },
        change: function (event, ui) {
            setSliderDate(ui.value);
            updateLayers();
            reloadGraphs();
        }
    });
}


function setUpTransparencySlider() {
    var transparency_slider_value;
    transparency_slider_value = 100;
    if ($('#map').data("transparency_slider_value")) {
        transparency_slider_value = $("#map").data(
            "transparency_slider_value");
    }
    $("#transparency-slider").slider({
        min: 0,
        max: 100,
        step: 1,
        value: transparency_slider_value,
        slide: function (event, ui) {
            $('#map').data("transparency_slider_value", ui.value);
            $(layers).each(function (i, layer) {
                if (layer !== undefined) {
                    layer.setOpacity(ui.value / 100);
                }
            });
        }
    });
}


function setUpMapLoadDefaultLocation() {
    $("#map-load-default-location").click(function () {
        var url, coordinates, zoom;
        url = $(this).attr("data-url");
        $.getJSON(
            url, function (data) {
                if ((data.x !== undefined) &&
                    (data.y !== undefined) &&
                    (data.zoom !== undefined))
                {
                    map.setCenter(
                        new OpenLayers.LonLat(parseFloat(data.x),
                                              parseFloat(data.y)),
                        parseFloat(data.zoom));
                }
            });
    });
}


/* Reload map-actions: put all initialization functions here for map actions
(above map, load/save location/ empty temp workspace) */
function reloadMapActions() {
    $(".map-actions").load(
        "./ .map-action",
        function () {
            fillSidebar();
            setUpAnimationSlider();
            setUpTransparencySlider();
            setUpMapLoadDefaultLocation();
        });
}


function setUpWorkspaceAcceptable() {
    // Set up draggability for current and future items.
    // See http://tinyurl.com/29lg4y3 .
    $(".workspace-acceptable").live("mouseover", function () {
        if (!$(this).data("draggable-initialized")) {
            $(this).data("draggable-initialized", true);
            $(this).draggable({
                scroll: 'false',
                cursor: 'move',
                helper: 'clone',
                appendTo: 'body',
                revert: 'true',
                placeholder: 'ui-sortable-placeholder'
            });
        }
    });
    // Clicking a workspace-acceptable shows it in the 'temp' workspace.
    $(".workspace-acceptable").live("click", function (event) {
        var name, adapter_class, adapter_layer_json, url_add_item_temp;
        $(".workspace-acceptable").removeClass("selected");
        $(this).addClass("selected");
        name = $(this).attr("data-name");
        adapter_class = $(this).attr("data-adapter-class");
        adapter_layer_json = $(this).attr("data-adapter-layer-json");
        url_add_item_temp = $(".workspace").attr(
            "data-url-lizard-map-session-workspace-add-item-temp");
        $.post(
            url_add_item_temp,
            {name: name,
             adapter_class: adapter_class,
             adapter_layer_json: adapter_layer_json
            },
            function (workspace_id) {
                var url, center_x, center_y;
                updateLayer(workspace_id);
                reloadMapActions();
                // Load extent from workspace and zoom to it.
                url = $(".workspace").attr(
                    "data-url-lizard-map-session-workspace-extent-temp");
                $.getJSON(url, {}, function (extent) {
                    // If we do not get extent, just forget it.
                    if ((extent.north !== null) &&
                        (extent.south !== null) &&
                        (extent.east !== null) &&
                        (extent.west !== null))
                    {
                        // Convert bbox to center coordinates
                        center_x = (extent.east + extent.west) / 2;
                        center_y = (extent.north + extent.south) / 2;
                        // Now pan
                        map.panTo(
                            new OpenLayers.LonLat(parseFloat(center_x),
                                                  parseFloat(center_y)));
                    }
                });
            });
        stretchOneSidebarBox();
    });

    // Add action to button 'add-workspace-item' in workspace
    // acceptables. This class is added by
    // setUpWorkspaceAcceptableButtons in lizard-ui: lizard.js.
    $(".add-workspace-item").live("click", function (event) {
        // Fetch workspace acceptable properties and add workspace item.
        var wa_name, adapter_class, adapter_layer_json, url,
            $workspace_acceptable, $workspace, workspace_id;
        // Get adapter class and parameters.
        $workspace_acceptable = $(this).parents(".workspace-acceptable");
        $workspace = $(".workspace");  // Assumes there is only 1.
        workspace_id = $workspace.attr("data-workspace-id");

        wa_name = $workspace_acceptable.attr("data-name");
        adapter_class = $workspace_acceptable.attr("data-adapter-class");
        adapter_layer_json = $workspace_acceptable.attr("data-adapter-layer-json");
        url = $workspace.attr("data-url-lizard-map-workspace-item-add");

        // Request to make workspace item and update workspace.
        $.post(
            url,
            {workspace_id: workspace_id,
             name: wa_name,
             adapter_class: adapter_class,
             adapter_layer_json: adapter_layer_json
            },
            function (workspace_id) {
                // Update all workspaces.
                $(".workspace").updateWorkspace();
                // "click" the empty temp workspace
                $(".workspace-empty-temp").click();
            }
        );
        return false; // Same as .preventDefault and .stopPropagation
    });
}


function setUpWorkspaceEmpty() {
    var $workspace, workspace_id, url;
    $(".workspace-empty-trigger").live('click', function () {
        $workspace = $(this).parents("div.workspace");
        workspace_id = $workspace.attr("data-workspace-id");
        url = $workspace.attr("data-url-lizard-map-workspace-item-empty");
        $.post(
            url, {workspace_id: workspace_id},
            function (data) {
                $workspace.updateWorkspace();
            });
    });
}


// Date selector: only support for ONE date selector at the moment.

function setUpDateChoice() {
    $.datepicker.setDefaults($.datepicker.regional.nl);
    $("#id_date_start").datepicker();
    $("#id_date_end").datepicker();
}

function setUpDateAjaxForm(overlay) {
    var form = $("form", overlay);
    form.submit(function () {
        $.post(
            form.attr('action'),
            form.serialize(),
            function (data) {
                // This is the success handler.  Form can contain errors,
                // though.
                var newForm, freshForm;
                newForm = $(data).find('form');
                form.html(newForm);
                setUpDateChoice();
                freshForm = $("form", overlay);
                setUpDateAjaxForm(freshForm);
                if (newForm.html().indexOf("rror") === -1) {
                    // No error/Error, so refresh graphs and close the popup.
                    reloadGraphs();
                    $("div.close", overlay).click();
                }
            });
        return false;
    });
}


function setUpDatePopup() {
    $(".popup-trigger").live('mouseover', function () {
        if (!$(this).data("popup-initialized")) {
            $(this).data("popup-initialized", true);
            $(this).overlay({
                onLoad: function () {
                    var overlay = this.getOverlay();
                    setUpDateAjaxForm(overlay);
                }
            });
        }
    });
}

function setUpNotFoundPopup() {
    $("#not_found_popup_trigger").overlay();
}

function nothingFoundPopup() {
    $("#not_found_popup_trigger").click();
    setTimeout(function () {
        $("#not_found_popup div.close").click();
    },
              2000);
}

function setUpGraphEditPopup() {
    $(".graph_edit_trigger").overlay();
}






/*
Empty the temp workspace
*/
function setUpEmptyTempInteraction() {
    $(".workspace-empty-temp").live("click", function () {
        var $workspace, url, workspace_item_id;
        $(this).css("cursor", "progress");
        $workspace = $(".workspace");
        url = $workspace.attr("data-url-lizard-map-workspace-item-delete");
        workspace_item_id = $(this).attr("data-workspace-item-id");
        $.post(
            url,
            {object_id: workspace_item_id},
            function (workspace_id) {
                updateLayer(workspace_id);
                // load new map actions
                reloadMapActions();
                // remove highlighting
                $(".workspace-acceptable").removeClass("selected");
            }
        );
    });
}


function popup_click_handler(x, y, map) {
    var extent, radius, url;
    extent = map.getExtent();
    radius = Math.abs(extent.top - extent.bottom) / 30;  // Experimental, seems to work good
    $("#map_OpenLayers_ViewPort").css("cursor", "progress");
    url = $(".workspace").attr("data-url-lizard-map-search-coordinates");
    if (url !== undefined) {
        $.getJSON(
            url,
            { x: x, y: y, radius: radius, srs: map.getProjection() },
            function (data) {
                $("#map_OpenLayers_ViewPort").css("cursor", "default");
                show_popup(data, map);
            }
        );
    }
}


function popup_hover_handler(x, y, map) {
    /* Show name of one item when hovering above a map */
    var extent, radius, url;
    extent = map.getExtent();
    radius = Math.abs(extent.top - extent.bottom) / 30;  // experimental, seems to work good
    url = $(".workspace").attr("data-url-lizard-map-search-name");
    if (url !== undefined) {
        $.getJSON(
            url,
            { x: x, y: y, radius: radius, srs: map.getProjection() },
            function (data) {
                hover_popup(data, map);
            }
        );
    }
}


/* Legend edit functions. */
function setUpLegendColorPickers() {
    var submit, beforeshow;
    submit = function (hsb, hex, rgb, el) {
	    $(el).val(hex);
	    $(el).ColorPickerHide();
    };
    beforeshow = function () {
        $(this).ColorPickerSetColor(this.value);
    };

    $("input[name=min_color]").ColorPicker({onSubmit: submit, onBeforeShow: beforeshow});
    $("input[name=max_color]").ColorPicker({onSubmit: submit, onBeforeShow: beforeshow});
    $("input[name=too_low_color]").ColorPicker({onSubmit: submit, onBeforeShow: beforeshow});
    $("input[name=too_high_color]").ColorPicker({onSubmit: submit, onBeforeShow: beforeshow});

    // Setup widget colors.
    $("#colorSelector").each(function () {
        var div, rel, color;
        rel = $(this).attr("rel");
        color = $(rel).attr("value");
        div = $(this).find("div");
        div.css('backgroundColor', '#' + color);
    });

    // Make the widget clickable.
    $("#colorSelector").ColorPicker({
        onBeforeShow: function () {
            var rel, color;
            rel = $(this).attr("rel");
            color = $(rel).attr("value");
            $(this).ColorPickerSetColor(color);
        },
        onChange: function (hsb, hex, rgb) {
            $("#colorSelector div").css('backgroundColor', '#' + hex);
        },
        onSubmit: function (hsb, hex, rgb, el) {
            var rel;
            rel = $(el).attr("rel");
            $(rel).val(hex);
            $(el).ColorPickerHide();
        }
    });

}


/* Pans to workspace item. Only works if extent function is
implemented for that particilar workspace item. */
function setUpWorkspaceItemPanToLayer() {
    $(".workspace-item-pan-to").live("click", function () {
        var url, workspace_item_id;
        workspace_item_id = $(this).parent().attr(
            "data-object-id");
        url = $(this).parents(".workspace").attr(
            "data-url-lizard-map-workspace-item-extent");
        $.getJSON(
            url,
            {workspace_item_id: workspace_item_id},
            function (extent) {
                var center_x, center_y;
                // If we do not get extent, just forget it.
                if ((extent.north !== null) &&
                    (extent.south !== null) &&
                    (extent.east !== null) &&
                    (extent.west !== null))
                {
                    // Convert bbox to center coordinates
                    center_x = (extent.east + extent.west) / 2;
                    center_y = (extent.north + extent.south) / 2;
                    // Now pan
                    map.panTo(
                        new OpenLayers.LonLat(parseFloat(center_x),
                                              parseFloat(center_y)));
                }
            });
    });
}


function legend_action_reload(event) {
    // send all legend properties to server and reload page
    var $form, url, name;
    event.preventDefault();
    $form = $(this).parents("form.legend-options");
    url = $form.attr("data-url");
    $.post(
        url,
        $form.serialize(),
        function () {
            // Reload page after posting.
            location.reload();
        });
}


function setUpLegendEdit() {
    $(".legend-edit").live("mouseover", function () {
        if (!$(this).data("popup-initialized")) {
            $(this).data("popup-initialized", true);
            $(this).overlay();
            setUpLegendColorPickers();
        }
    });
    $(".legend-action-reload").live("click", legend_action_reload);
}


function mapSaveLocation() {
    var url, coordinates;
    url = $("#lizard-map-wms").attr("data-save-location-url");
    coordinates = map.center;
    $.ajax({
        type: 'POST',
        url: url,
        data: {x: coordinates.lon, y: coordinates.lat, zoom: map.zoom},
        async: false,
        success: function () {}
    });
}


// Initialize all workspace actions.
$(document).ready(function () {
    setUpWorkspaceAcceptable();
    setUpWorkspaceEmpty();
    setUpDatePopup();
    setUpDateChoice();
    setUpNotFoundPopup();
    setUpEmptyTempInteraction();
    setUpAnimationSlider();
    setUpTransparencySlider();
    setUpGraphEditPopup();
    setUpWorkspaceItemPanToLayer();

    // Set up legend edit.
    setUpLegendEdit();

    setUpMapLoadDefaultLocation();

    /* Workspace functions, requires jquery.workspace.js */
    $(".workspace").workspaceInteraction();
    $(".add-snippet").snippetInteraction(); // voor collage view, nu nog nutteloos voor popup
    $("a.lizard-map-link").lizardMapLink();
});

// Beforeunload: this function is called just before leaving the page
// and loading the new page. Unload however is called after loading
// the new page.
$(window).bind('beforeunload', function () {
    mapSaveLocation(); // Save map location when 'before' leaving page.
});
