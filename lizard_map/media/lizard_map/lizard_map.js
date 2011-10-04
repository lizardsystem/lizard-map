// jslint configuration; btw: don't put a space before 'jslint' below.
/*jslint browser: true */
/*global $, OpenLayers, window, updateLayers, addProgressAnimationIntoWorkspace,
stretchOneSidebarBox, reloadGraphs, fillSidebar, show_popup,
alert, setUpTooltips,
hover_popup, layers, wms_layers, map, refreshLayers, isCollagePopupVisible,
updateWorkspaceAcceptableStatus */

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
    $("#map-load-default-location").live("click", function () {
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

    // Set initial status.
    updateWorkspaceAcceptableStatus();

    // We want to refresh workspace-acceptables after clicking an
    // accordion tab. Not accidently a click is also triggered after
    // loading next pane.
    try {
        $("#accordion").data("tabs").onClick(function (event) {
            updateWorkspaceAcceptableStatus();
        });
    } catch (e) {
        // Nothing. There is no accordion.
    }
}


/* L3 dialog contents */
function dialogContent(content) {
    $("#dialog-content").html(content);
}


function dialogText(title, content) {
    var html;
    html = "<h1>" + title + "</h1>" +
        "<p>" + content + "</p>";
    dialogContent(html);
    dialogSize("s");
    dialogOverlay();
}


/* L3 pop up the dialog */
function dialogOverlay() {
    var overlay;
    // In some screens it will not pop up the first time unless load: true
    overlay = $("#dialog").overlay({load: true});
    // load:true only works the first time.
    overlay.load();  // Pop up
}

/* L3 close dialog after delay */
function dialogCloseDelay() {
    setTimeout(function () {
        $("#dialog .close").click();
    }, 2000);
}

/* L3 close dialog */
function dialogClose() {
    $("#dialog .close").click();
}


/* L3 dialog replace ids */
function dialogReplaceTitles(new_content) {
    var replace_titles, id, ids, div, title, i;
    // Create array with ids to be replaced.
    // There may be some empty strings in this list.
    ids = $("#dialog").data("replace-titles").split(" ");

    // Place a div around everything to allow searching through the
    // root objects.
    div = $("<div/>").html(new_content);

    for (i in ids) {
        if (i !== undefined) {
            id = ids[i];
            if (id !== "") {
                title = div.find("#" + id);
                $("#" + id).attr("title", title.html());
            }
        }
    }
}

/* L3 Dialog size */
function dialogSize(size) {
    if (size === "xs") {
        // Extra Small
        $("#dialog").css("width", "20em");
        $("#dialog").css("min-height", "7em");
    } else if (size === "s") {
        // Small
        $("#dialog").css("width", "30em");
        $("#dialog").css("min-height", "10em");
    } else {
        // Default
        $("#dialog").css("width", "40em");
        $("#dialog").css("min-height", "15em");
    }
}


/* L3 Click on dialog. Initially fill contents by get. Configure some
settings. */
function dialogClick(event) {
    var url, overlay, size;
    event.preventDefault();

    url = $(event.target).attr("href");
    $.get(url)
        .success(function (data) {
            var div;
            // Put data in extra html to find root-level .dialog-box
            div = $("<div/>").html(data).find(".dialog-box");
            dialogContent(div);
            dialogOverlay();
        })
        .error(function (data) {
            dialogContent("Fout bij laden van dialoog. " +
                          "Probeert U het later nog eens.");
            dialogOverlay();
            dialogCloseDelay();
        });
    $("#dialog").data("submit-on-change", false);
    // All ids that have to be replaced in the original page. Space
    // separated.
    $("#dialog").data("replace-titles", "");  // Reset
    $("#dialog").data(
        "replace-titles", $(event.target).attr("data-replace-titles"));
    dialogSize($(event.target).attr("data-size"));
    return false;
}

function helpDialogClick(event) {
    var url, overlay, size, msg;
    event.preventDefault();

    $('a.ajax-help-dialog').each(function(index) {
        url = $(this).attr("href");
        $.get(url)
            .success(function(data) {
                dialogContent(data);
                dialogOverlay();
            })
            .error(function(data) {
                dialogContent("Fout bij laden van dialoog." +
                              "Probeert u het later nog eens.");
                dialogOverlay();
                dialogCloseDelay();
            });
    });
}

/* L3 Onchange on dialog: only on ajax-dialog-onchange */
function dialogOnChange(event) {
    var $form;
    // console.log("dialog onchange");
    event.preventDefault();
    if ($("#dialog").data("submit-on-change")) {
        // console.log("onchange submit");
        $form = $(event.target).parents("form");
        $.post(
            $form.attr("action"), $form.serialize(),
            function (data, status, context) {/* Strange: never comes here*/},
            "json")
            .error(
                function (context)
                {
                    var div;
                    div = $("<div/>").html(context.responseText).find(
                        ".dialog-box");
                    // Bad request: wrong input
                    // Or 200, or else... all the same
                    dialogReplaceTitles(context.responseText);
                    dialogContent(div);
                    dialogOverlay();
                    return false;
                });
    }
    return false;
}

function dialogSetupChange(event) {
    $("#dialog").data("submit-on-change", true);
}

/* L3 Pressing submit in dialog box */
function dialogSubmit(event, afterSubmit) {
    var $form;
    event.preventDefault();
    $form = $(event.target).parents("form");
    // Strange: everything goes to .error
    $.post(
        $form.attr("action"), $form.serialize(),
        function (data, status, context) {}, "json")
        .error(function (context) {
            var div;
            div = $("<div/>").html(context.responseText).find(".dialog-box");
            if (context.status === 400) {
                // Bad request: wrong input
                dialogContent(div);
                dialogOverlay();
            } else if (context.status === 200) {
                dialogReplaceTitles(context.responseText);
                if ($("#dialog").data("submit-on-change")) {
                    // Close immediately, because the contents don't change.
                    if (afterSubmit === undefined) {
                        dialogClose();
                    } else {
                        afterSubmit(context);
                    }
                } else {
                    // Show success message, then close.
                    dialogContent(div);
                    dialogOverlay();
                    if (afterSubmit === undefined) {
                        dialogCloseDelay();
                    } else {
                        afterSubmit(context);
                    }
                }
            } else if (context.status === 403) {
                // Forbidden: display whole page
                dialogContent(context.responseText);
                dialogOverlay();
                dialogCloseDelay();
            } else {
                // Unknown error
                dialogContent("Fout bij opslaan, " +
                              "probeert U het later nog eens.");
                dialogOverlay();
                dialogCloseDelay();
            }
            return false;
        });
    return false;
}


function updateWorkspaceAfterSubmit(event) {
    return dialogSubmit(event, function (context) {
        return $(".workspace").updateWorkspace();
    });
}

function reloadScreenAfterSubmit(event) {
    return dialogSubmit(event, function (context) {
        dialogText("Herladen pagina",
                   "De pagina wordt opnieuw geladen.");
        window.location.reload();
    });
}

/* L3 Generic dialog code that works on a hrefs.

- Define an a href with class "ajax-dialog" or "ajax-dialog-onchange"
- Optionally add attributes:
  - data-reload-after-submit="true": reloads the page after successful submit
  - data-replace-titles="title_id1 title_id2": replaces given tag ids
    after submit (or onchange).

The actions are as follows:
1) Click: get contents from href url and display in div #dialog
2) On submit, check result and close if success. Remain open with
   result if error.

*/
function setUpDialogs() {
    $(".ajax-dialog").live("click", dialogClick);
    $(".ajax-help-dialog").live("click", helpDialogClick);
    $(".ajax-dialog-onchange").live("click", dialogClick);
    $(".ajax-dialog-onchange").live("click", dialogSetupChange);
    // Handle submit button in forms in a dialog. Exclude alternative-submit.
    $("#dialog input:submit:not(.alternative-submit)").live(
        "click", dialogSubmit);
    // Handle ajax-dialog-onchange, which submit on changes.
    $("#dialog form input").live("change", dialogOnChange);
    $("#dialog form select").live("change", dialogOnChange);

    // TODO: split this part. It is for specific lizard-map workspace stuff.
    // For workspace changes: live our own handler
    $("#dialog input:submit.update-workspace-after").live(
        "click", updateWorkspaceAfterSubmit);
    $("#dialog input:submit.reload-screen-after").live(
        "click", reloadScreenAfterSubmit);
}


/* Generic POST click handling: do preAction, post, if success do
postAction. */
function actionPostClick(event, preAction, postAction, parameters) {
    var url, target, target_id;
    event.preventDefault();

    url = $(event.target).attr("href");
    target_id = $(event.target).attr("data-target-id");
    if (target_id !== undefined) {
        target = $(target_id);
    } else {
        target = undefined;
    }
    if (preAction !== undefined) {
        preAction();
    }
    if (parameters === undefined) {
        parameters = {};
    }
    $.post(url, parameters)
        .success(function (data) {
            var div, html;
            if (target !== undefined) {
                div = $("<div/>").html(data).find(".dialog-box").find(target_id);
                target.html(div.html());
            }
            if (postAction !== undefined) {
                postAction();
            }
            if ($(event.target).hasClass("reload-after-action")) {
                // TODO: De-activate possible actions.
                // Show dialog.
                dialogText("Herladen pagina",
                           "De pagina wordt opnieuw geladen.");
                location.reload();
            }
        })
        .error(function (data) {
            target.html("Fout bij actie. Herlaad pagina en probeer opnieuw");
        });
    return false;
}


/* Actions to do after server returns from post */
function postClickWorkspaceEmpty() {
    var $workspace;
    $workspace = $("#edit-workspace");
    // Remove progress.
    $workspace.find(".sidebarbox-action-progress").remove();
    $workspace.updateWorkspace();
}


/* Empty collage items */
function actionPostClickEmpty(event) {
    return actionPostClick(
        event,
        addProgressAnimationIntoWorkspace,
        postClickWorkspaceEmpty
    );
}

/* Delete collage item */
function actionPostDeleteCollageItem(event) {
    var object_id;
    object_id = $(event.target).parents(
        ".collage-item").attr("data-object-id");
    return actionPostClick(
        event,
        undefined,
        stretchOneSidebarBox,
        {object_id: object_id, action: 'delete'}
    );
}

/* Click checkbox on collage item. */
function actionPostEditCollageItem(event) {
    var object_id, visible, $collage_item;
    $collage_item = $(event.target).parents(".collage-item");
    object_id = $collage_item.attr("data-object-id");
    visible = $collage_item.find(".collage-item-checkbox").attr("checked");
    return actionPostClick(
        event,
        undefined,
        stretchOneSidebarBox,
        {object_id: object_id, visible: visible, action: 'update'}
    );
}


/* click on collage-add item */
function actionPostCollageAdd(event) {
    var $target, adapter_class, name, adapter_layer_json, identifier;
    $target = $(event.target);
    name = $target.attr("data-name");
    adapter_class = $target.attr("data-adapter-class");
    adapter_layer_json = $target.attr("data-adapter-layer-json");
    identifier = $target.attr("data-identifier");
    return actionPostClick(
        event,
        undefined,
        stretchOneSidebarBox,
        {name: name, adapter_class: adapter_class, adapter_layer_json: adapter_layer_json, identifier: identifier}
    );
}

/* Collage popup: still old-fashioned. Same for single collage-item or
whole collage. */
function collagePopup(event) {
    var url;
    event.preventDefault();

    url = $(event.target).attr("href");
    $.getJSON(url, function (data) {
        show_popup(data);
    });
    dialogSize("");  // Reset to default.
    return false;
}

/* Actions post or get an url, then replaces tag data-target-id in
current page. */
function setUpActions() {
    $(".action-post").live("click", actionPostClick);
    // Empty workspace AND empty collage.
    $(".action-post-workspace-empty").live("click", actionPostClickEmpty);
    // Delete collage item
    $(".collage-item-delete").live(
        "click", actionPostDeleteCollageItem);
    // Edit (visibility of) collage item
    $(".collage-item-checkbox").live(
        "click", actionPostEditCollageItem);
    // Collage-popup.
    $(".collage-popup").live(
        "click", collagePopup);
    // Add to collage
    $(".collage-add").live("click", actionPostCollageAdd);
}


/*
Erase the contents of the popup when the user closes the popup
*/
function eraseDialogContentsOnClose() {
    $("#dialog").live("onClose", function () {
        $("#dialog-content").empty();
    });
}


/* L3 popup with "niets gevonden" */
function nothingFoundPopup() {
    dialogText("Niets gevonden",
               "Er is niets rond deze locatie gevonden.");
    dialogCloseDelay();
}


/* Make the following workspace buttons work:
- Trashcan next to "My Workspace" (workspace-empty-trigger)
- (-) next to workspace-items (workspace-item-delete)

L3
*/
function setUpWorkspaceButtons() {
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
}


/* Handle a click */
/* Assumes there is 1 "main" workspace. Adds workspace_id to request. Only required when viewing workspaces of others */
function popup_click_handler(x, y, map) {
    var extent, radius, url, user_workspace_id;
    extent = map.getExtent();
    radius = Math.abs(extent.top - extent.bottom) / 30;  // Experimental, seems to work good
    $("#map").css("cursor", "progress");
    url = $(".workspace").attr("data-url-lizard-map-search-coordinates");
    user_workspace_id = $(".workspace").attr("data-workspace-id");
    if (url !== undefined) {
        $.getJSON(
            url,
            { x: x, y: y, radius: radius, srs: map.getProjection(),
              user_workspace_id: user_workspace_id},
            function (data) {
                dialogSize("");  // default size
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
                    map.zoomToExtent(ol_extent);
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


/* TODO: Upgrade to L3*/
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


// TODO: Is this still used?
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


// TODO: Can probably be removed.
function setupTableToggle() {
    // For collapsible tables in popups
    $('.toggle_button').live('click', function (event) {
        var $wrapper;
        $wrapper = $(this).closest('.toggle_table_wrapper');
        $('table', $wrapper).slideDown('fast');
        $(this).hide();
    });
}


function setUpDataFromUrl() {
    // A div with class "data-from-url" will fetch data from attribute
    // data-url and paste the contents in the div. The reason is that
    // the calculation time for some objects can be long.
    var $div;
    $div = $("div.data-from-url");
    $div.each(function () {
        var url;
        url = $(this).attr("data-url");
        if (url !== undefined) {
            // Put in progress animation
            $(this).html(
                '<img src="/static_media/lizard_ui/ajax-loader.gif" />');
            // Load actual data.
            $(this).load(url + " .dialog-box");
        }
    });
}


// Initialize all workspace actions.
$(document).ready(function () {
    // Touched/new for L3
    setUpWorkspaceAcceptable();
    setUpDialogs();
    eraseDialogContentsOnClose();
    setUpActions();
    setUpDataFromUrl();

    // Untouched
    setUpWorkspaceButtons();
    setUpAnimationSlider();
    setUpTransparencySlider();
    setUpWorkspaceItemPanToLayer();

    // Set up legend edit.
    setUpLegendEdit();

    setUpMapLoadDefaultLocation();

    /* Workspace functions, requires jquery.workspace.js */
    $(".workspace").workspaceInteraction();

    // voor collage view, nu nog nutteloos voor popup
    //$(".add-snippet").snippetInteraction();
    //$("a.lizard-map-link").lizardMapLink();
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
