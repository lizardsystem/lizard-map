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


/*
Workspace plugin

A workspace needs to have a couple of data items (defined on the <div
class="workspace>):

data-url-lizard-map-workspace-item-edit
data-url-lizard-map-workspace-item-reorder
data-url-lizard-map-workspace-item-add
data-url-lizard-map-workspace-item-delete

css class drophover

A workspace needs:

attr("data-workspace_id")
<ul> inside with class workspace_items at depth 2
workspace_trash class inside workspace
workspace_item_checkbox class in ul.workspace_items
*/

/* Bind/Live checkboxes

$("a.url-lizard-map-workspace-item-edit").attr("href");
*/

function isCollagePopupVisible() {
    return ($("#dialog-content div:first-child").length !== 0 &&
            $("#dialog-content div:first-child").data("is_collage_popup") &&
            $("#dialog").css("display") === "block");
}

jQuery.fn.liveCheckboxes = function () {
    return this.each(function () {
        var $workspace;
        $workspace = $(this);
        $workspace.find(".workspace-item-checkbox").live('click', function () {
            var url, $list_item;
            url = $workspace.attr("data-url-lizard-map-workspace-item-edit");
            $list_item = $(this).closest('li');
            $list_item.addClass("waiting-lineitem");
            $.ajax({
                url: url,
                data: { workspace_item_id: this.id, visible: this.checked },
                success: function () {
                    $workspace.updateWorkspace();
                },
                type: "POST",
                async: false
            });
        });
    });
};

function show_popup(data) {
    var html, overlay, i;
    if (data !== null) {
        if (data.html && data.html.length !== 0) {
            // We got at least 1 result back.
            if (data.html.length === 1) {
                // Just copy the contents directly into the target div.
                $("#movable-dialog-content").html(data.html[0]);
            } else {
                // Build up html with tabs.
                html = '<div id="popup-tabs"><ul>';
                for (i = 0; i < data.html.length; i += 1) {
                    html += '<li><a href="#popup-tab-' + (i + 1) + '">Tabblad ';
                    html += (i + 1) + '</a></li>';
                }
                html += '</ul>';
                for (i = 0; i < data.html.length; i += 1) {
                    html += '<div id="popup-tab-' + (i + 1) + '">';
                    html += data.html[i];
                    html += '</div>';
                }
                html += '</div>';

                // Copy the prepared HTML to the target div.
                $("#movable-dialog-content").html(html);

                // Call jQuery UI Tabs to actually instantiate some tabs.
                $("#popup-tabs").tabs({
                    idPrefix: 'popup-tab',
                    selected: 0,
                    show: function(event, ui) {
                        // Do an initial resize for IE8.
                        resizeGraph($(ui.panel).find('.flot-graph'));
                    }
                });
            }
            $("#popup-subtabs").tabs({
                idPrefix: 'popup-subtab',
                selected: 0
            });
            // All set, open the dialog.
            $("#movable-dialog").dialog("open");
            // Have the graphs fetch their data.
            reloadGraphs();
            $(".add-snippet").snippetInteraction();
        }
        else if (data.indexOf && data.indexOf("div") != -1) {
            // Apparantly data can also contain an entire <html> document
            $("#movable-dialog-content").html(data);
            $("#movable-dialog").dialog("open");
        }
        else {
            nothingFoundPopup();
        }
    }
}

var hover_popup;

function init_hover_popup(map) {
    hover_popup = new OpenLayers.Popup('hover-popup',
                                 new OpenLayers.LonLat(0, 0),
                                 new OpenLayers.Size(300, 300),
                                 '',
                                 false);
    hover_popup.maxSize = new OpenLayers.Size(300, 300);
    hover_popup.border = "1px solid black";
    hover_popup.autoSize = true;
    map.addPopup(hover_popup);
}

function show_hover_popup(data, map) {
    if (data.name !== "" && data.name !== undefined) {
        var content = '&nbsp;&nbsp;&nbsp;&nbsp;' + data.name +
            '&nbsp;&nbsp;&nbsp;&nbsp;';
        hover_popup.lonlat = new OpenLayers.LonLat(data.x, data.y);
        hover_popup.setContentHTML(content);
        hover_popup.updatePosition();
        hover_popup.updateSize();
        hover_popup.show();
    }
}

function hide_hover_popup() {
    hover_popup.contentHTML = '';
    hover_popup.hide();
}

/* Make workspaces sortable and droppable

Needed: data attribute .data-url-lizard-map-workspace-item-reorder on
the <div class="workspace">

<ul> at depth 2

L3
*/

jQuery.fn.workspaceInteraction = function () {
    return this.each(function () {
        var $workspace, workspace_id, workspaceItems, snippet_list;
        // Make the items in a workspace sortable.
        $workspace = $(this);
        workspaceItems = $workspace.find(".workspace-items");
        workspaceItems.sortable({
            update: function (event, ui) {
                var url, order;
                // very strange... $workspace becomes the <ul> element
                // (which is workspaceItems)...  using workspaceItems
                url = $workspace.attr("data-url-lizard-map-workspace-item-reorder");
                order = workspaceItems.sortable("serialize");
                $.post(
                    url,
                    order,
                    function () {
                        workspaceItems.parent().parent().updateWorkspace();
                    }
                );
            },
            helper: 'clone',
            connectWith: '.workspace-items',
            cursor: 'move',
            revert: 'true',
            placeholder: 'ui-sortable-placeholder',
            items: '.workspace-item'
        });
        // // Make collage clickable. (DONE: should be collage-popup)
        // $(".collage-popup", $workspace).live('click',
        //                                $(".collage").collagePopup);
        // Make checkboxes work.
        $workspace.liveCheckboxes();
        // Initialize the graph popup.
        //$('#dialog').overlay({});  // Necessary?
    });
};


/* Refresh workspace-acceptables. They should light up if the item is
in given workspace. */
function updateWorkspaceAcceptableStatus() {
    var workspace_items, $workspace;
    $workspace = $(".workspace");  // Later make this an option?
    workspace_items = $workspace.find(".workspace-item");

    $(".workspace-acceptable").each(function () {
        var wa_adapter_class, wa_adapter_layer_json, selected, visible;
        selected = false;
        visible = true;
        wa_adapter_class = $(this).attr("data-adapter-class");
        wa_adapter_layer_json = $(this).attr(
            "data-adapter-layer-json");

        workspace_items.each(function () {
            var adapter_class, adapter_layer_json, $workspace_item;
            $workspace_item = $(this);
            adapter_class = $workspace_item.attr(
                "data-adapter-class");

            if (wa_adapter_class === adapter_class) {
                adapter_layer_json = $workspace_item.attr(
                    "data-adapter-layer-json");
                if (wa_adapter_layer_json === adapter_layer_json) {
                    selected = true;
                    if ($workspace_item.attr("data-visible") === "False") {
                        visible = false;
                    }
                }
            }
        });
        if (selected && visible) {
            $(this).addClass("selected");
            $(this).removeClass("selected-invisible");
        } else if (selected && !visible) {
            $(this).addClass("selected-invisible");
            $(this).removeClass("selected");
        } else {
            $(this).removeClass("selected");
            $(this).removeClass("selected-invisible");
        }
    });
}


// Update workspace boxes and their visible layers. L3
jQuery.fn.updateWorkspace = function () {
    return this.each(function () {
        var $workspace, workspace_id, $holder;
        $workspace = $(this);
        workspace_id = $workspace.attr("data-workspace-id");
        $holder = $('<div/>');

        // Holder trick for replacing several items with just one server call:
        // see http://tinyurl.com/32xacr4 .
        $holder.load(
            './ #page',
            function () {
                $(".workspace-items", $workspace).html(
                    $('.workspace-items', $holder).html());
                // $(".snippet-list", $workspace).html(
                //     $('.snippet-list', $holder).html());
                //fillSidebar();
                $(".map-actions").html(
                    $('.map-actions', $holder).html());
                $("#lizard-map-wms").html(
                    $('#lizard-map-wms', $holder).html());
                $("#rightbar").html(
                    $('#rightbar', $holder).html());
                // $("#collage").html(
                //     $('#collage', $holder).html());
                //reloadGraphs();
                // reload map layers
                if ($("#map").length > 0) {
                    refreshLayers(); // from lizard_wms.js
                }
                // Is this enough? See also refreshMapActionsDivs in
                // lizard_map

                // TODO: there refreshes are also used in lizard_map:
                // replaceItems. See if we can bring it together.
                updateWorkspaceAcceptableStatus();

                //setUpAnimationSlider();
                //setUpTransparencySlider();
                //setUpTooltips();
                // Enable sorting. Some functions
                // (setUpAddWorkspaceItem) turns sorting off.
               //$(".workspace ul.workspace-items").sortable("enable");
            }
        );
    });
};

/* React on click "add snippet"

requires

.data-url-lizard-map-snippet-add

*/
jQuery.fn.snippetInteraction = function () {
    return this.each(function () {
        $(this).click(function (event) {
            var workspace_id, url, workspace_item_id,
                workspace_item_location_identifier,
                workspace_item_location_shortname,
                workspace_item_location_name;
            event.preventDefault();
            workspace_id = $(this).attr("data-workspace-id");
            url = $("#workspace-" + workspace_id).attr("data-url-lizard-map-snippet-add");  // should work, but workspace id is wrong
            // url = $(".workspace").attr("data-url-lizard-map-snippet-add");
            workspace_item_id = $(this).attr("data-workspace-item-id");
            workspace_item_location_identifier = $(this).attr("data-item-identifier");
            workspace_item_location_shortname = $(this).attr("data-item-shortname");
            workspace_item_location_name = $(this).attr("data-item-name");
            if (url !== undefined) {
                $.post(
                    url,
                    {
                        workspace_item_id: workspace_item_id,
                        workspace_item_location_identifier: workspace_item_location_identifier,
                        workspace_item_location_shortname: workspace_item_location_shortname,
                        workspace_item_location_name: workspace_item_location_name
                    },
                    function () {
                        // refresh collage
                        $(".workspace").find(".snippet-list").load("./ .snippet",
                                                                   fillSidebar);
                        // Optional: close ourselves?
                    });
            }
        });
    });
};


// Obsolete
function workspaceItemOrSnippet(object) {
    if ($(object).is(".workspace-item")) {
        return true;
    }
    if ($(object).is(".snippet")) {
        return true;
    }
    return false;
    //.workspace_item .snippet
}


function addProgressAnimationIntoWorkspace() {
    $("#trash1").after('<img src="/static_media/lizard_ui/ajax-loader3.gif" class="sidebarbox-action-progress" data-src="" />');
}


/* Load a lizard-map page by only replacing necessary parts

Replaces:
- breadcrumbs
- app part

Setup the js of page
Load workspaces

Then change the url (???)

*/

jQuery.fn.lizardMapLink = function () {
    $(this).click(function (event) {
        var popup_login, next;
        popup_login = $(this).attr("data-popup-login");
        if (popup_login !== undefined) {
            // So we need login.
            event.preventDefault();
            // Fill "next" field.
            next = $(this).attr("href");
            $("#login-form-next").attr("value", next);
            // "Click" on it.
            $("#login-button").click();
        }
    });
};


/*
Check if selector returns any elements

Used like:
$("#notAnElement").exists();
*/
jQuery.fn.exists = function () {
    return this.length !== 0;
}

function resizeGraph($el) {
    if ($el) {
        var plot = $el.data('plot');
        if (plot) {
            plot.resize();
            plot.setupGrid();
            plot.draw();
            return true;
        }
    }
    return false;
}

function setupDatepicker(div) {
    // Nice Jquery date picker with dropdowns for year and month
    div.find(".datepicker").datepicker({
	dateFormat:"yy-mm-dd",
	changeMonth: true,
	changeYear: true,
	showAnim: ''
    });
}

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
		if (wms_layers.hasOwnProperty(index)) {
		    // Some layers start out at a lower opacity. If the opacity slider
		    // is set to 100%, they should be at that lower opacity.
		    // Store the original opacity in the wms_layer object itself.
		    if (!wms_layers[index].hasOwnProperty("originalOpacity") &&
		       wms_layers[index].hasOwnProperty("opacity")) {
			wms_layers[index].originalOpacity = wms_layers[index].opacity;
		    } else {
			wms_layers[index].originalOpacity = 1;
		    }

                    wms_layers[index].setOpacity((ui.value/100) * wms_layers[index].originalOpacity);
		}
            }
        }
    });
}


/* L3 */
function setUpMapLoadDefaultLocation() {
    $(".map-load-default-location").live("click", function (event) {
        var url;
        event.preventDefault();
        url = $(this).attr("href");
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

function dateRangePopup(data) {
    show_popup(data);
    setupDatepicker($('#date-range-form'));
    $('#date-range-submit').click(function(event) {
        event.preventDefault();
        $("#movable-dialog").dialog("close");
        return false;
    });
    $("#date-range-form input").change(
        dateRangeOnChange);
    $("#date-range-form select").change(
        dateRangeOnChange);
}

function dateRangeOnChange(event) {
    var $form;
    event.preventDefault();
    $form = $('#date-range-form');
    $.post(
        $form.attr("action"), $form.serialize()
    )
    .success(
        function (data) {
            // send result to popup again
            dateRangePopup(data);
        }
    );
    return false;
}

function setUpDateRangePopup() {
    $(".popup-date-range").live("click", function (event) {
        var url;
        event.preventDefault();
        url = $(this).attr("href");
        $.get(
            url,
            function(data) {
                dateRangePopup(data);
            }
        );
    });
}

function setUpWorkspaceLoad() {
    $(".workspace-load").live("click", function (event) {
        var url;
        event.preventDefault();
        url = $(this).attr("href");
        id = $(this).attr("data-workspace-id");
        $.post(
            url,
            {
                id: id
            },
            function(data) {
            	result = $.parseJSON(data);
            	if (result['redirect'])
            	    window.location.href = result['redirect'];
            }
        );
    });
}

function workspaceSavePopup(data) {
    show_popup(data);
    $('#workspace-save-submit').click(function(event) {
        event.preventDefault();
        $form = $('#workspace-save-form');
        $.post(
            $form.attr("action"), $form.serialize()
        )
        .success(
            function (data) {
                // send result to popup
                show_popup(data);
            }
        );
        return false;
    });
}

function setUpWorkspaceSavePopup() {
    $(".popup-workspace-save").live("click", function (event) {
        var url;
        event.preventDefault();
        url = $(this).attr("href");
        $.get(
            url,
            function(data) {
                workspaceSavePopup(data);
            }
        );
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
        event.preventDefault();
        $workspace_acceptable = $(this);
        indicateWorkspaceItemBusy($workspace_acceptable);

        name = $(this).attr("data-name");
        adapter_class = $(this).attr("data-adapter-class");
        adapter_layer_json = $(this).attr("data-adapter-layer-json");
        $workspace = $(".workspace");
        url_item_toggle = $workspace.attr(
            "data-url-lizard-map-workspace-item-toggle");

        /* New bootstrap-era interaction */
        if (!$(this).hasClass('selected')) {
            var $layer_button, $moving_box, move_down, move_right;
            $layer_button = $(".secondary-sidebar-button");
            $("#page").after('<div id="moving-box">');
            $moving_box = $("#moving-box");
            $moving_box.offset($(this).offset());
            $moving_box.width($(this).width());
            $moving_box.height($(this).height());
            move_down = $layer_button.offset().top - $(this).offset().top;
            move_right = $layer_button.offset().left - $(this).offset().left;
            $moving_box.animate({
                left: '+=' + move_right,
                top: '+=' + move_down,
                width: $layer_button.width(),
                height: $layer_button.height()
                }, 1000, function() {
                    $moving_box.remove();
                });
            /* xxx */
        }
        if ($(this).hasClass('selected')) {
            var $layer_button, $moving_box, move_up, move_left;
            $layer_button = $(".secondary-sidebar-button");
            $("#page").after('<div id="moving-box">');
            $moving_box = $("#moving-box");
            $moving_box.offset($layer_button.offset());
            $moving_box.width($layer_button.width());
            $moving_box.height($layer_button.height());
            move_up = $layer_button.offset().top - $(this).offset().top;
            move_left = $layer_button.offset().left - $(this).offset().left;
            $moving_box.animate({
                left: '-=' + move_left,
                top: '-=' + move_up,
                width: 0,
                height: 0
                }, 1000, function() {
                    $moving_box.remove();
                });
            /* xxx */
        }
        /* End of new bootstrap-era interaction */

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
            // updateWorkspaceAcceptableStatus();
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


/* L3 pop up the dialog: OBSOLETE */
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


/* Create array with ids to be replaced.
 There may be some empty strings in this list. */
function dialogReplaceItemIds() {
    var ids;
    ids = $("#movable-dialog").data("replace-items").split(" ");
    return ids;
}


/* L3 dialog replace ids with same items in new_content

Also refreshes known elements after replacing specific ids.
*/
function replaceItems(ids, new_content) {
    var replace_items, id, div, $replace_with, i, replaced_count,
        refresh_map, refresh_animation_slider;
    // Place a div around everything to allow searching through the
    // root objects.
    div = $("<div/>").html(new_content);

    refresh_map = false;
    refresh_animation_slider = false;

    for (i in ids) {
        if (i !== undefined) {
            id = ids[i];
            if (id !== "") {
                $replace_with = div.find("#" + id);
                // There should be only one.
                $("#" + id).replaceWith($replace_with[0]);
                if (id === 'date-range') {
                    refresh_map = true;
                    refresh_animation_slider = true;
                }
            }
        }
    }

    // Gui elements that are initialized after replacing items.
    if (refresh_animation_slider) {
        setUpAnimationSlider();
    }
    if (refresh_map) {
        if ($("#map").exists()) {
            refreshLayers(); // from lizard_wms.js
        }
    }
}

/* L3 Dialog size */
function dialogSize(size) {
    // new dialog in L3.1
    /*
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
    */
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
            //div = $("<div/>").html(data).find(".dialog-box");
            //dialogContent(div);
            //dialogOverlay();
            show_popup(data);
            // Dialogs may contain datepicker fields, activate them here.
            setupDatepicker(div);
        })
        .error(function (data) {
            messagePopup("Fout bij laden van dialoog. " +
                         "Probeert U het later nog eens.");
        });
    $("#dialog").data("submit-on-change", false);
    // All ids that have to be replaced in the original page. Space
    // separated.
    $("#dialog").data("replace-items", "");  // Reset
    $("#dialog").data(
        "replace-items", $(event.target).attr("data-replace-items"));
    //dialogSize($(event.target).attr("data-size"));
    return false;
}

function helpDialogClick(event) {
    var url, overlay, size, msg;
    event.preventDefault();

    $('a.ajax-help-dialog').each(function(index) {
        url = $(this).attr("href");
        $.get(url)
            .success(function(data) {
                show_popup(data);
            })
            .error(function(data) {
                messagePopup("Fout bij laden van dialoog." +
                             "Probeert u het later nog eens.");
            });
    });
}

function dialogSetupChange(event) {
    $("#dialog").data("submit-on-change", true);
}

/* L3 Pressing submit in dialog box */
function dialogSubmit(event, afterSubmit) {
    var $form, ids;
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
                ids = dialogReplaceItemIds();
                replaceItems(ids, context.responseText);
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

function openNewWindowAfterSubmit(event) {
    return dialogSubmit(event, function(context) {
	/* The URL to open is stored in a link with class
	   "new-window-url". */
	as = $('<div/>').
	    html(context.responseText).
	    find(".new-window-url");

	as.each(function(i, a) {
	    window.open(a.href, '_');
	});
    });
}

/* L3 Generic dialog code that works on a hrefs.

- Define an a href with class "ajax-dialog" or "ajax-dialog-onchange"
- Optionally add attributes:
  - data-reload-after-submit="true": reloads the page after successful submit
  - data-replace-items="title_id1 title_id2": replaces given tag ids
    after submit (or onchange).

The actions are as follows:
1) Click: get contents from href url and display in div #dialog
2) On submit, check result and close if success. Remain open with
   result if error.

*/
function setUpDialogs() {
    //$(".ajax-dialog").live("click", dialogClick);
    //$(".ajax-help-dialog").live("click", helpDialogClick);
    //$(".ajax-dialog-onchange").live("click", dialogClick);
    //$(".ajax-dialog-onchange").live("click", dialogSetupChange);
    // Handle submit button in forms in a dialog. Exclude alternative-submit.
    //$("#movable-dialog input:submit:not(.alternative-submit)").live(
    //    "click", dialogSubmit);
    // Handle ajax-dialog-onchange, which submit on changes.
    //$("#movable-dialog form input").live(
    //    "change", dialogOnChange);
    //$("#movable-dialog form select").live(
    //    "change", dialogOnChange);

    // TODO: split this part. It is for specific lizard-map workspace stuff.
    // For workspace changes: live our own handler
    //$("#movable-dialog input:submit.update-workspace-after").live(
    //    "click", updateWorkspaceAfterSubmit);
    //$("#movable-dialog input:submit.reload-screen-after").live(
    //    "click", reloadScreenAfterSubmit);
    //$("#movable-dialog input:submit.open-new-window-after").live(
	//"click", openNewWindowAfterSubmit);
}


/* Generic POST click handling: do preAction, post, if success do
postAction. */
function actionPostClick(event, preAction, postAction, parameters) {
    var url, target, target_id;
    event.preventDefault();

    url = $(event.target).attr("href");
    if (url == undefined) {
        // find in parents
        url = $(event.target).parents('a').attr("href");
    }
    target_id = $(event.target).attr("data-target-id");
    if (target_id == undefined) {
        // find in parents
        target_id = $(event.target).parents('a').attr("data-target-id");
    }
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
                // If there are any tipsy tooltips, hide them first
                $(".tipsy").hide();

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


/* Empty workspace and collage items */
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
        undefined,
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
        undefined,
        {object_id: object_id, visible: visible, action: 'update'}
    );
}


/* click on collage-add item */
function actionPostCollageAdd(event) {
    var $target, adapter_class, name, adapter_layer_json, identifier;
    /* New bootstrap-era interaction */
   {
        var $layer_button, $moving_box, move_down, move_right;
        $layer_button = $(".secondary-sidebar-button");
        $("#page").after('<div id="moving-box">');
        $moving_box = $("#moving-box");
        $moving_box.offset($(this).offset());
        $moving_box.width($(this).width());
        $moving_box.height($(this).height());
        move_down = $layer_button.offset().top - $(this).offset().top;
        move_right = $layer_button.offset().left - $(this).offset().left;
        $moving_box.animate({
            left: '+=' + move_right,
            top: '+=' + move_down,
            width: $layer_button.width(),
            height: $layer_button.height()
            }, 1000, function() {
                $moving_box.remove();
            });
    }
    $target = $(event.target);
    name = $target.attr("data-name");
    adapter_class = $target.attr("data-adapter-class");
    adapter_layer_json = $target.attr("data-adapter-layer-json");
    identifier = $target.attr("data-identifier");
    return actionPostClick(
        event,
        undefined,
        undefined,
        {name: name, adapter_class: adapter_class, adapter_layer_json: adapter_layer_json, identifier: identifier}
    );
}

/* Collage popup: still old-fashioned. Same for single collage-item or
whole collage. */
function collagePopup(event) {
    var url;
    event.preventDefault();

    url = $(event.target).attr("href");
    if (url == undefined) {
        // find in parents
        url = $(event.target).parents('a.collage-popup').attr("href");
    }

    $.getJSON(url, function (data) {
        show_popup(data);
    });
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


/* L3.1 popup with "niets gevonden" */
function nothingFoundPopup() {
    messagePopup("Er is niets rond deze locatie gevonden.");
}


function messagePopup(message) {
    $("#movable-dialog-content").html(message);
    $("#movable-dialog").dialog("open");
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
                show_hover_popup(data, map);
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
        workspace_item_id = $(this).parents("[data-object-id]").attr(
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

function collageEditPopup(data) {
    show_popup(data);
    //setupDatepicker($('#collage-edit-form'));
    setUpAggPeriodField();
    $('#collage-edit-submit').click(function(event) {
        event.preventDefault();
        $form = $('#collage-edit-form');
        $.post(
            $form.attr("action"), $form.serialize()
        )
        .success(
            function (data) {
                // send result to popup again
                collageEditPopup(data);
            }
        );
    });
}

function setUpCollageEditPopup() {
    $(".collate-edit-popup").click(function (event) {
        var url;
        event.preventDefault();
        url = $(this).attr("href");
        $.get(
            url,
            function(data) {
                collageEditPopup(data);
            }
        );
    });
}

function setUpAggPeriodField() {
    // Set restrict_to_month on enabled or disabled
    $("select#id_aggregation_period").change(function (event) {
        // 4 is MONTH
        if (this.value === "4") {
            $("select#id_restrict_to_month").removeAttr("disabled");
        } else {
            $("select#id_restrict_to_month").attr("disabled", "True");
            $("select#id_restrict_to_month").each(function () {
                this.value = "0";
            });
        }
    });
}


function setUpCollageTablePopup() {
    $(".collage-table-popup").click(function (event) {
        var url;
        event.preventDefault();
        url = $(this).attr("href");
        $.get(
            url,
            function(data) {
                show_popup(data);
            }
        );
    });
}


// Beforeunload: this function is called just before leaving the page
// and loading the new page. Unload however is called after loading
// the new page.
$(window).bind('beforeunload', function () {
    mapSaveLocation(); // Save map location when 'before' leaving page.
});



/*jslint browser: true */
/*jslint evil: true */
/*jslint nomen: false */
/*global $, OpenLayers, popup_click_handler, popup_hover_handler, alert,
G_PHYSICAL_MAP, G_SATELLITE_MAP, G_NORMAL_MAP, G_HYBRID_MAP, TouchHandler,
stretchOneSidebarBox */

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
    return $("a.map-multiple-selection").hasClass("active");
}

/* L3 click on (lon, lat) in multiple select mode

Borrowed from popup_click_handler
*/
function addMultipleSelection(x, y, map, e) {
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
                spawnCustomMovingBox(10, 10, e.pageX, e.pageY);
                var div;
                div = $(data).find("#edit-collage");
                $("#edit-collage").html(div.html());

                //stretchOneSidebarBox();
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
                     transitionEffect: 'resize',
                     tileOptions: {crossOriginKeyword: null}
                    });
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

// obsolete as everything is a WMS layer now
/*
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
*/


function refreshWmsLayers() {
    // Add wms layers from workspace items.
    var $lizard_map_wms, osm_url, i, ids_found;
    ids_found = [];
    $lizard_map_wms = $("#lizard-map-wms");
    $(".workspace-wms-layer").each(function () {
        var name, url, params, options, id, index;
        // WMS id, different than workspace ids.
        id = $(this).attr("data-workspace-wms-id");
        ids_found.push(id);
        name = $(this).attr("data-workspace-wms-name");
        url = $(this).attr("data-workspace-wms-url");
        params = $(this).attr("data-workspace-wms-params");
        params = $.parseJSON(params);
        // Fix for partial images on tiles
        params['tilesorigin'] = [map.maxExtent.left, map.maxExtent.bottom];
        options = $(this).attr("data-workspace-wms-options");
        options = $.parseJSON(options);
        index = parseInt($(this).attr("data-workspace-wms-index"));
        if (wms_layers[id] === undefined) {
            // Create it.
            var layer = new OpenLayers.Layer.WMS(name, url, params, options);
            wms_layers[id] = layer;
            map.addLayer(layer);
            layer.setZIndex(1000 - index); // looks like passing this via options won't work properly
        }
        else {
            // Update it.
            var layer = wms_layers[id];
            layer.setZIndex(1000 - index);
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
    //refreshWorkspaceLayers();
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

function spawnCustomMovingBox(width, height, x, y) {
    var $layer_button, $moving_box, move_down, move_right;
    $layer_button = $(".secondary-sidebar-button");
    $("#page").after('<div id="moving-box">');
    $moving_box = $("#moving-box");
    $moving_box.offset({left:x, top:y});
    $moving_box.width(width);
    $moving_box.height(height);
    move_down = $layer_button.offset().top - y;
    move_right = $layer_button.offset().left - x;
    $moving_box.animate({
        left: '+=' + move_right,
        top: '+=' + move_down,
        width: $layer_button.width(),
        height: $layer_button.height()
        }, 1000, function() {
            $moving_box.remove();
        });
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
    if (projection === "EPSG:900913" || projection === "EPSG:3857")
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
                if (multipleSelection()) {
                    addMultipleSelection(lonlat.lon, lonlat.lat, map, e);
                } else {
                    eval(javascript_click_handler_name)(
                        lonlat.lon, lonlat.lat, map);
                }
            }
        });
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
                hide_hover_popup();
            }
        });
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
    init_hover_popup(map);

    // actually add the handers: keep these here for full iPad compatibility
    if (javascript_click_handler_name) {
        map_click_control = new MapClickControl();
        map.addControl(map_click_control);
        map_click_control.activate();
    }
    if (javascript_hover_handler_name !== undefined) {
        map_hover_control = new MapHoverControl();
        map.addControl(map_hover_control);
        map_hover_control.activate();
    }
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
    $(".map-multiple-selection").live("click", function () {
        $(this).toggleClass("active");
    });
}



/* Helper functions in graph edit screen.  Needs lizard.js in
order to function correctly.  */
function graph_save_snippet() {
    // The actual graph props are already stored in session on server
    var url, workspace_item_id, workspace_item_location_identifier,
        workspace_item_location_shortname, workspace_item_location_name;
    url = $(this).attr("data-url");
    workspace_item_id = $(this).attr("data-workspace-item-id");
    workspace_item_location_identifier = $(this).attr("data-workspace-item-location-identifier");
    workspace_item_location_shortname = $(this).attr("data-workspace-item-location-shortname");
    workspace_item_location_name = $(this).attr("data-workspace-item-location-name");
    $.post(
        url,
        {workspace_item_id: workspace_item_id,
         workspace_item_location_identifier: workspace_item_location_identifier,
         workspace_item_location_shortname: workspace_item_location_shortname,
         workspace_item_location_name: workspace_item_location_name
        }, function () {
            reloadGraphs();
        });
}

function graph_options_submit(event) {
    // send all graph properties to server and reload page
    var $form, url;
    event.preventDefault();
    $form = $(this).parents("form.graph-options");
    url = $form.attr("action");
    $.post(
        url,
        $form.serialize(),
        function () {
            // Always reload page: statistics & graphs can be different.
            location.reload();
        });
}

function graph_line_options_submit(event) {
    // send all graph properties to server and reload graphs
    var $form, url;
    event.preventDefault();
    $form = $(this).parents("form.graph-line-options");
    url = $form.attr("action");
    $.post(
        url,
        $form.serialize(),
        function () {
            reloadGraphs();
            $("div.close").click();
        });
}

function setGraphFilterMonth() {
    var $form, status;
    $form = $(".popup-graph-edit-global");
    $form.each(function () {
        status = $(this).find("input:radio:checked").attr("value");
        if (status === "4") { // 4 is "MONTH"
            $(this).find(".graph-filter-month").attr("disabled", false);
        } else {
            $(this).find(".graph-filter-month").attr("disabled", true);
        }
    });
}

function setUpGraphForm() {
    // Set current status.
    setGraphFilterMonth();

    // Setup click.
    $(".popup-graph-edit-global input:radio").click(setGraphFilterMonth);
}



/* REST api with jQuery */


function makeHtml(data) {
    var items = [];
    console.log(typeof data);
    if (typeof data === "string") {
        return data;
    }
    if (typeof data === "function") {
        return data;
    }
    $.each(data, function (key, val) {
        console.log(key, val);
        if (val === null) {
            items.push('<li><span>' + key + '</span></li>');
        } else if ((typeof val === "string") && (val.indexOf('http://') === 0)) {
            items.push('<li><a href="' + val + '" class="rest-api">' + key + '</a></li>');
        } else {
            //console.log(val);
            items.push('<li><span>' + key + '</span>' + makeHtml(val) + '</li>');
        }
     });
    //console.log(items);
    return $('<ul/>', {html: items.join('')}).html();
}


function apiRequest(target) {
    var url;
    url = $(target).attr("href");
    $.getJSON(url, function (data) {
        $(target).parents(".rest-api-container").html(makeHtml(data));
    });
 }


/* a hrefs with class "rest-api":
fetch url and build "something" out of it.
*/
function setUpRestApiLinks() {
    $("a.rest-api").live("click", function(event) {
        event.preventDefault();
        apiRequest(event.target);
        return false;
    });

    // Initial
    $("a.rest-api").each(function () {
        apiRequest(this);
    });
}



$(document).ready(function () {
    // Used by show_popup
    $('body').append('<div id="movable-dialog"><div id="movable-dialog-content"></div></div>');
    $('#movable-dialog').dialog({
        autoOpen: false,
        title: '',
        width: 450,
        height: 480,
        zIndex: 10000
    });
});


// Initialize all workspace actions.
$(document).ready(function () {
    // New bootstrappy stuff.
    // TODO EJVOS $("#map").height($("#content").height());

    // Touched/new for L3
    setUpWorkspaceAcceptable();
    setUpDialogs();
    eraseDialogContentsOnClose();
    setUpActions();
    setUpDataFromUrl();

    // Untouched
    setUpWorkspaceButtons();
    //setUpAnimationSlider();
    //setUpTransparencySlider();
    setUpWorkspaceItemPanToLayer();

    // Set up legend edit.
    setUpLegendEdit();

    setUpMapLoadDefaultLocation();
    setUpWorkspaceLoad();
    setUpWorkspaceSavePopup();
    setUpDateRangePopup();
    setUpCollageEditPopup();
    setUpCollageTablePopup();

    /* Workspace functions, requires jquery.workspace.js */
    $(".workspace").workspaceInteraction();

    // voor collage view, nu nog nutteloos voor popup
    //$(".add-snippet").snippetInteraction();
    //$("a.lizard-map-link").lizardMapLink();
    // Optional popup video link.
    //setupVideoPopup();
    setupTableToggle();
});



$(document).ready(function () {
    showMap();
    setDownloadImageLink();
    setUpMultipleSelection();
});


$(document).ready(function () {
    $(".graph-save-snippet").click(graph_save_snippet);
    $("input.graph-line-options-submit").click(graph_line_options_submit);
    $("input.graph-options-submit").click(graph_options_submit);
    setUpGraphForm();
});


$(document).ready(function () {
    setUpRestApiLinks();
});
