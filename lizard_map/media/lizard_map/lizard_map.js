// jslint configuration; btw: don't put a space before 'jslint' below.
/*jslint browser: true */
/*global $, OpenLayers, window, updateLayer, stretchOneSidebarBox,
reloadGraphs, fillSidebar, show_popup */

var animationTimer;

function setUpAnimationSlider() {
    $("#animation-slider").slider({
        min: parseInt($("#animation-slider").attr("data-min")),
        max: parseInt($("#animation-slider").attr("data-max")),
        step: parseInt($("#animation-slider").attr("data-step")),
        value: parseInt($("#animation-slider").attr("data-value")),
        slide: function (event, ui) {
            if (animationTimer) {
                clearTimeout(animationTimer);
            }
            animationTimer = setTimeout(
                function () {
                    // Do actual work.
                    //console.log(ui.value);
                    $.ajax({
                        type: "POST",
                        url: $("#animation-slider").attr("data-ajax-path"),
                        data: "slider_value="+ui.value,
                        success: function(data) {
                            console.log("Load was performed");
                        }
                    });
                },
                300);
        }
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
                updateLayer(workspace_id);
                $(".map-actions").load(
                    "./ .map-action",
                    function () {
                        fillSidebar();
                        setUpAnimationSlider();
                    });
            });
        stretchOneSidebarBox();
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
                $(".map-actions").load(
                    "./ .map-action",
                    function () {
                        fillSidebar();
                        setUpAnimationSlider();
                    });
                // remove highlighting
                $(".workspace-acceptable").removeClass("selected");
            }
        );
    });
}


// Commented out: lizard-ui now has generic support for it (see the
// in-browser documentation).
// function loadSizedImages() {


function popup_click_handler(x, y, map) {
    var extent, radius, url;
    extent = map.getExtent();
    radius = Math.abs(extent.top - extent.bottom) / 30;  // experimental, seems to work good
    $("#map_OpenLayers_ViewPort").css("cursor", "progress");
    url = $(".workspace").attr("data-url-lizard-map-search-coordinates");
    if (url !== undefined) {
        $.getJSON(
            url,
            { x: x, y: y, radius: radius },
            function (data) {
                $("#map_OpenLayers_ViewPort").css("cursor", "default");
                show_popup(data, map);
            }
        );
    }
}



// Initialize all workspace actions.
$(document).ready(function () {
    setUpWorkspaceAcceptable();
    setUpDatePopup();
    setUpDateChoice();
    setUpNotFoundPopup();
    setUpEmptyTempInteraction();
    setUpAnimationSlider();
    setUpGraphEditPopup();

    /* Workspace functions, requires jquery.workspace.js */
    $(".workspace").workspaceInteraction();
    $(".add-snippet").snippetInteraction(); // voor collage view, nu nog nutteloos voor popup
    // $("a.lizard-map-link").lizardMapLink();
});
