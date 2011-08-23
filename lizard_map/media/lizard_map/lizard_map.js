// jslint configuration; btw: don't put a space before 'jslint' below.
/*jslint browser: true */
/*global $, OpenLayers, window, updateLayers, addProgressAnimationIntoWorkspace,
stretchOneSidebarBox, reloadGraphs, fillSidebar, show_popup,
alert, setUpTooltips,
hover_popup, layers, wms_layers, map, refreshLayers, isCollagePopupVisible */

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
            var index;
            $('#map').data("transparency_slider_value", ui.value);
            $(layers).each(function (i, layer) {
                if (layer !== undefined) {
                    layer.setOpacity(ui.value / 100);
                }
            });
            // WMS layers
            for (index in wms_layers) {
                // Lint wants an if statement.. why?
                if (true) {
                    wms_layers[index].setOpacity(ui.value / 100);
                }
            }
        }
    });
}


/* L3 */
function setUpMapLoadDefaultLocation() {
    $("#map-load-default-location").click(function () {
        var url;
        url = $(this).attr("data-url");
        $.getJSON(
            url, function (data) {
                var extent, zoom;
                if (data.extent !== undefined) {
                    extent = new OpenLayers.Bounds(
                        data.extent.left,
                        data.extent.bottom,
                        data.extent.right,
                        data.extent.top);
                    // See #2762 and #2794.
                    map.zoomToExtent(extent, true);
                }
            });
    });
}


/* set up map actions */
function setUpMapActions() {
    fillSidebar();
    setUpAnimationSlider();
    setUpTransparencySlider();
    setUpMapLoadDefaultLocation();
}


/* Refreshes map-actions and lizard-map-wms divs, then inits js. */
/* Looks a bit like jQuery.fn.updateWorkspace part. Needs refactoring. */
function refreshMapActionsDivs() {
    var $holder;
    $holder = $('<div/>');
    $holder.load(
        './ #page',
        function () {
            $(".map-actions").html(
                $('.map-actions', $holder).html());
            $("#lizard-map-wms").html(
                $('#lizard-map-wms', $holder).html());
            refreshLayers();
            setUpMapActions();
        });
}

/* Reload map-actions: put all initialization functions here for map actions
(above map, load/save location/ empty temp workspace)

OBSOLETE, should be integrated with other load functions
*/
function reloadMapActions() {
    $(".map-actions").load(
        "./ .map-action",
        setUpMapActions
    );
}


/* L3 */
/* Clicking a workspace-acceptable toggles the
   workspace-acceptable. If it is enabled it also shows up in your
   workspace (if it is visible). */
function setUpWorkspaceAcceptable() {

    function indicateWorkspaceItemBusy($workspace_item) {
        $workspace_item.removeClass("workspace-acceptable");
        $workspace_item.addClass("waiting-lineitem");
    }

    function reenableWorkspaceItem($workspace_item) {
        $workspace_item.addClass("workspace-acceptable");
        $workspace_item.removeClass("waiting-lineitem");
    }

    $(".workspace-acceptable").live("click", function (event) {
        var name, adapter_class, adapter_layer_json, url_item_toggle,
        $workspace, html, $workspace_acceptable;

        $workspace_acceptable = $(this);
        indicateWorkspaceItemBusy($workspace_acceptable);

        name = $(this).attr("data-name");
        adapter_class = $(this).attr("data-adapter-class");
        adapter_layer_json = $(this).attr("data-adapter-layer-json");
        $workspace = $(".workspace");
        url_item_toggle = $workspace.attr(
            "data-url-lizard-map-workspace-item-toggle");
        $.post(
            url_item_toggle,
            {name: name,
             adapter_class: adapter_class,
             adapter_layer_json: adapter_layer_json
            },
            function (just_added) {
                if (just_added === "true") {
                    // console.log("selected");
                    $workspace_acceptable.addClass("selected");
                } else {
                    // console.log("not selected");
                    $workspace_acceptable.removeClass("selected");
                }
                // refreshMapActionsDivs();
                $(".workspace").updateWorkspace();
                //stretchOneSidebarBox();
            });
        reenableWorkspaceItem($workspace_acceptable);
        return false;
    });
}


/* Make the following workspace buttons work:
- Trashcan next to "My Workspace" (workspace-empty-trigger)
- (-) next to workspace-items (workspace-item-delete)

L3
*/
function setUpWorkspaceButtons() {
    // Trashcan next to "My Workspace"
    $(".workspace-empty-trigger").live('click', function () {
        var $workspace, workspace_id, url;
        $workspace = $(this).parents("div.workspace");
        workspace_id = $workspace.attr("data-workspace-id");
        url = $workspace.attr("data-url-lizard-map-workspace-item-empty");
        addProgressAnimationIntoWorkspace();
        $.post(
            url, {workspace_id: workspace_id},
	    function (data) {
	        //remove progress
                $workspace.find(".sidebarbox-action-progress").remove();
                $workspace.updateWorkspace();
            });
    });
    // Delete workspace item
    $(".workspace-item-delete").live('click', function () {
        var $workspace, workspace_id, url, object_id;
        $workspace = $(this).parents("div.workspace");
        workspace_id = $workspace.attr("data-workspace-id");
        url = $workspace.attr(
            "data-url-lizard-map-workspace-item-delete");
        object_id = $(this).parents(".workspace-item").attr("data-object-id");
        $(this).parents(".workspace-item").addClass("waiting-lineitem");
        $.post(
            url,
            { object_id: object_id },
            function (is_deleted) {
                $workspace.updateWorkspace();
            });
        return false;
    });
    // // Trashcan next to "Collage"
    // $(".collage-empty-trigger").live('click', function () {
    //     var $workspace, collage_id, url;
    //     $workspace = $(this).parents("div.workspace");
    //     collage_id = $(this).attr("data-collage-id");
    //     url = $workspace.attr("data-url-lizard-map-collage-empty");
    //     addProgressAnimationIntoWorkspace();
    //     $.post(
    //         url, {collage_id: collage_id},
    //         function (data) {
    //             //remove progress
    //             $workspace.find(".sidebarbox-action-progress").remove();
    //             $workspace.updateWorkspace();
    //         });
    // });
    // // Delete snippet
    // $(".snippet-delete").live('click', function () {
    //     var $workspace, workspace_id, url, object_id;
    //     $workspace = $(this).parents("div.workspace");
    //     workspace_id = $workspace.attr("data-workspace-id");
    //     url = $workspace.attr(
    //         "data-url-lizard-map-snippet-delete");
    //     object_id = $(this).parents(".snippet").attr("data-object-id");
    //     $(this).parents(".snippet").addClass("waiting-lineitem");
    //     $.post(
    //         url,
    //         { object_id: object_id },
    //         function () {
    //             $workspace.updateWorkspace();
    //             // Reload the collage_popup if it is already present
    //             if (isCollagePopupVisible()) {
    //                 $(".collage").collagePopup();
    //             }
    //         });
    //     return false;
    // });
    // // Make snippetnames clickable.
    // $("div.snippet-name").live('click', function (event) {
    //     var $snippet, $workspace, url, snippet_id;
    //     $snippet = $(this).parents("li.snippet");
    //     $workspace = $(this).parents("div.workspace");
    //     url = $workspace.attr("data-url-lizard-map-snippet-popup");
    //     snippet_id = $snippet.attr("data-object-id");
    //     $.getJSON(
    //         url,
    //         { snippet_id: snippet_id },
    //         function (data) {
    //             show_popup(data);
    //         }
    //     );
    // });
}


/* Updates the date popup from a select or input tag */
function updateDateSelectOrInput() {
    var url, $form;
    $form = $(this).parents("form");
    url = $form.attr("action");
    $.post(
        url,
        $form.serialize(),
        function () {
            // Update the popup. Note: We cannot use load, because the
            // overlay properties will get lost
            $.get("./", {}, function (data) {
                var new_contents, curr_period_title;
                new_contents = $(data).find(
                    "#summary-datepicker-contents").html();
                $("#summary-datepicker-contents").html(new_contents);
                curr_period_title = $(data).find(
                    "#summary-datepicker-a").attr("title");
                $("#summary-datepicker-a").attr("title", curr_period_title);
            });
            reloadGraphs();
            // Check for items with .show_on_date_change and show 'em.
            $('.show_on_date_change').slideDown();
        });
}


// Updates date div from server when fields change.
function setUpDateUpdate() {
    $("#summary-datepicker form input").live(
        'change', updateDateSelectOrInput);
    $("#summary-datepicker form select").live(
        'change', updateDateSelectOrInput);
}


function setUpDatePopup() {
    $(".popup-trigger").live('mouseover', function () {
        if (!$(this).data("popup-initialized")) {
            $(this).data("popup-initialized", true);
            $(this).overlay();
        }
    });
}


function setUpNotFoundPopup() {
    $("#not_found_popup_trigger").overlay();
}


function nothingFoundPopup() {
    $("#not_found_popup_trigger").click();
    setTimeout(function () {
        $("#not_found_popup .close").click();
    },
              2000);
}


function setUpGraphEditPopup() {
    $(".graph_edit_trigger").overlay();
}


// /*
// Empty the temp workspace
// */
// function setUpEmptyTempInteraction() {
//     $(".workspace-empty-temp").live("click", function () {
//         var $workspace, url, workspace_item_id;
//         $(this).css("cursor", "progress");
//         $workspace = $(".workspace");
//         url = $workspace.attr("data-url-lizard-map-workspace-item-delete");
//         workspace_item_id = $(this).attr("data-workspace-item-id");
//         $.post(
//             url,
//             {object_id: workspace_item_id},
//             function (workspace_id) {
//                 refreshMapActionsDivs();
//                 // remove highlighting
//                 $(".workspace-acceptable").removeClass("selected");
//             }
//         );
//     });
// }


/* Handle a click */
/* Assumes there is 1 "main" workspace. Adds workspace_id to request. Only required when viewing workspaces of others */
function popup_click_handler(x, y, map) {
    var extent, radius, url, user_workspace_id;
    extent = map.getExtent();
    radius = Math.abs(extent.top - extent.bottom) / 30;  // Experimental, seems to work good
    $("#map_").css("cursor", "progress");
    url = $(".workspace").attr("data-url-lizard-map-search-coordinates");
    user_workspace_id = $(".workspace").attr("data-workspace-id");
    if (url !== undefined) {
        $.getJSON(
            url,
            { x: x, y: y, radius: radius, srs: map.getProjection(),
              user_workspace_id: user_workspace_id},
            function (data) {
                show_popup(data);
                $("#map").css("cursor", "default");
            }
        );
    }
}


/* Handle a hover */
/* Assumes there is 1 "main" workspace. Adds workspace_id to request. Only required when viewing workspaces of others */
function popup_hover_handler(x, y, map) {
    /* Show name of one item when hovering above a map */
    var extent, radius, url, user_workspace_id;
    extent = map.getExtent();
    radius = Math.abs(extent.top - extent.bottom) / 30;  // experimental, seems to work good
    url = $(".workspace").attr("data-url-lizard-map-search-name");
    user_workspace_id = $(".workspace").attr("data-workspace-id");
    if (url !== undefined) {
        $.getJSON(
            url,
            { x: x, y: y, radius: radius, srs: map.getProjection(),
              user_workspace_id: user_workspace_id},
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
                var center_x, center_y, ol_extent;
                // If we do not get extent, just forget it.
                if ((extent.north !== null) &&
                    (extent.south !== null) &&
                    (extent.east !== null) &&
                    (extent.west !== null))
                {
                    ol_extent = new OpenLayers.Bounds(
                        extent.west, extent.south,
                        extent.east, extent.north);
                    map.zoomToExtent(ol_extent, true);
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


/*
Sends current extent and name of visible base layer.
*/
function mapSaveLocation() {
    var url, extent, visible_base_layer_name, i;
    url = $("#lizard-map-wms").attr("data-save-location-url");
    if ($("#map").length > 0) {
        extent = map.getExtent();
        visible_base_layer_name = "";

        // Find the active base layer.
        for (i = 0; i < map.layers.length; i = i + 1) {
            if (map.layers[i].isBaseLayer && map.layers[i].visibility) {
                visible_base_layer_name = map.layers[i].name;
                break;
            }
        }
        $.ajax({
            type: 'POST',
            url: url,
            data: {bottom: extent.bottom,
                   left: extent.left,
                   right: extent.right,
                   top: extent.top,
                   base_layer_name: visible_base_layer_name},
            async: false,
            success: function () {}
        });
    }
}


function setupVideoPopup() {
    // Show popup
    $("#intro_popup").overlay({
        // custom top position
        top: 200,
        mask: {
            color: '#fff',
            loadSpeed: 200,
            opacity: 0.5
        },
        closeOnClick: true,
        load: true
    });
}


function  setupTableToggle() {
    // For collapsible tables in popups
    $('.toggle_button').live('click', function (event) {
        var $wrapper;
        $wrapper = $(this).closest('.toggle_table_wrapper');
        $('table', $wrapper).slideDown('fast');
        $(this).hide();
    });
}


// Initialize all workspace actions.
$(document).ready(function () {
    // Touched for L3
    // setUpToggleWorkspaceItem();
    setUpWorkspaceAcceptable();
    // setUpEmptyTempInteraction();

    // Untouched
    setUpWorkspaceButtons();
    setUpDatePopup();
    setUpDateUpdate();
    setUpNotFoundPopup();
    setUpAnimationSlider();
    setUpTransparencySlider();
    setUpGraphEditPopup();
    setUpWorkspaceItemPanToLayer();

    // Set up legend edit.
    setUpLegendEdit();

    setUpMapLoadDefaultLocation();

    /* Workspace functions, requires jquery.workspace.js */
    $(".workspace").workspaceInteraction();

    // voor collage view, nu nog nutteloos voor popup
    $(".add-snippet").snippetInteraction();
    $("a.lizard-map-link").lizardMapLink();
    // Optional popup video link.
    setupVideoPopup();
    setupTableToggle();
});


// Beforeunload: this function is called just before leaving the page
// and loading the new page. Unload however is called after loading
// the new page.
$(window).bind('beforeunload', function () {
    mapSaveLocation(); // Save map location when 'before' leaving page.
});
