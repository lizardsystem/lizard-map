// jslint configuration; btw: don't put a space before 'jslint' below.
/*jslint browser: true */

// in use (26-09-2012)
// left workspace + collage checkboxes
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

// in use (03-02-2012)
// main (single) popup
function setup_movable_dialog() {
    // used by open_popup
    $('body').append('<div id="movable-dialog"><div id="movable-dialog-content"></div></div>');
    var options = {
        autoOpen: false,
        title: '',
        width: 650,
        height: 480,
        zIndex: 10000,
        close: function (event, ui) {
            // clear contents on close
            $('#movable-dialog-content').empty();
        }
    };

    // make an exception for iPad
    if (isAppleMobile) {
        // dragging on touchscreens isn't practical
        options.draggable = false;
        // resizing neither
        options.resizable = false;
        // make width 90% of the entire window
        options.width = $(window).width() * 0.9;
        // make height 80% of the entire window
        options.height = $(window).height() * 0.8;
    }

    $('#movable-dialog').dialog(options);
}

// in use (26-09-2012)
// main (single) popup
function open_popup(show_spinner) {
    $("#movable-dialog-content").empty();
    if (show_spinner === undefined || show_spinner) {
        var $loading = $('<img src="/static_media/lizard_ui/ajax-loader.gif" class="popup-loading-animation" />');
        $("#movable-dialog-content").append($loading);
    }
    $("#movable-dialog").dialog("open");
}

// in use (26-09-2012)
// main (single) popup
function set_popup_content(data) {
    var html, overlay, i;
    if (data !== null) {
        if (data instanceof jQuery) {
            $("#movable-dialog-content").empty().append(data);
        }
        else if (data.html && data.html.length !== 0) {
            // We got at least 1 result back.
            if (data.html.length === 1) {
                // Just copy the contents directly into the target div.
                $("#movable-dialog-content").html(data.html[0]);
                // Have the graphs fetch their data.
                reloadGraphs();
            } else {
                // Build up html with tabs.
                html = '<div id="popup-tabs"><ul>';
                for (i = 0; i < data.html.length; i += 1) {
                    html += '<li><a href="#popup-tab-' + (i + 1) + '">';
                    html += data.tab_titles[i];
                    html += '</a></li>';
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
                    show: function (event, ui) {
                        // Have the graphs fetch their data.
                        reloadGraphs();
                    },
                    create: function (event, ui) {
                        // Have the graphs fetch their data.
                        reloadGraphs();
                    }
                });
            }
            $("#popup-subtabs").tabs({
                idPrefix: 'popup-subtab',
                selected: 0
            });
            $(".add-snippet").snippetInteraction();
        }
        else if (data.indexOf && data.indexOf("div") != -1) {
            // Apparantly data can also contain an entire <html> document
            $("#movable-dialog-content").html(data);
            // Have the graphs fetch their data.
            reloadGraphs();
        }
        else {
            var nothingFoundMessage = '';
            if (lizard_map && lizard_map.nothingFoundMessage) {
                nothingFoundMessage = lizard_map.nothingFoundMessage;
            }
            else {
                // Backwards compatibility
                nothingFoundMessage = "Er is niets rond deze locatie gevonden.";
            }
            $("#movable-dialog-content").html(nothingFoundMessage);
        }
    }
}

// in use (26-09-2012)
// mouseover when hovering over the map
var $map_tooltip;
function init_map_tooltip(map) {
    $map_tooltip = $('<div id="maptooltip"/>')
        .css({
            'position': 'absolute',
            'top': 0,
            'left': 0,
            'padding': '0.4em 0.6em',
            'border-radius': '0.5em',
            'border': '1px solid #111',
            'background-color': '#fff',
            'z-index': 2000,
            'display': 'none'
        })
        .appendTo("#map");
}
function show_map_tooltip(data, map) {
    if (data.name !== "" && data.name !== undefined) {
        var content = '&nbsp;&nbsp;&nbsp;&nbsp;' + data.name +
            '&nbsp;&nbsp;&nbsp;&nbsp;';
        var lonlat = new OpenLayers.LonLat(data.x, data.y);
        var pixel = map.baseLayer.getViewPortPxFromLonLat(lonlat);
        $map_tooltip.css({
            top: pixel.y + 10,
            left: pixel.x + 10
        });
        $map_tooltip.html(content);
        $map_tooltip.show();
    }
}
function hide_map_tooltip() {
    if ($map_tooltip) {
        $map_tooltip.hide();
    }
}

/* Make workspaces sortable and droppable

Needed: data attribute .data-url-lizard-map-workspace-item-reorder on
the <div class="workspace">
<ul> at depth 2
*/

// in use (26-09-2012)
// draggable workspace items (left)
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
        $workspace.liveCheckboxes();
    });
};

/* Refresh workspace-acceptables. They should light up if the item is
in given workspace. */

// in use (26-09-2012)
// highlight item in left map tree on select
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

// in use (26-09-2012)
// new map or reordered layers
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
                //$(".workspace-items", $workspace).html(
                //    $('.workspace-items', $holder).html());
                $("#edit-workspace").parent().html(
                    $('#edit-workspace', $holder).parent().html());
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
                $(".workspace").workspaceInteraction();
            }
        );
    });
};

/* React on click "add snippet"
requires
.data-url-lizard-map-snippet-add
*/

// in use (26-09-2012)
// when something is added to the collage
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
                        $(".workspace").find(".snippet-list").load("./ .snippet");
                        // Optional: close ourselves?
                    });
            }
        });
    });
};

// in use (26-09-2012)
// when popup with possible graphs is first opened
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

// in use (26-09-2012)
// zoom to extent button
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

// in use (26-09-2012)
// used by a button when a saved workspace is opened
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

// in use (26-09-2012)
// when clicked left near workspace empty button
function workspaceSavePopup(data) {
    // ensure current extent is stored in the session (on the
    // server side)
    mapSaveLocation();
    open_popup();
    set_popup_content(data);
    $('#workspace-save-submit').click(function(event) {
        event.preventDefault();
        $form = $('#workspace-save-form');
        $.post(
            $form.attr("action"), $form.serialize()
        )
        .success(
            function (data) {
                // send result to popup
                set_popup_content(data);
            }
        )
        .error(
            function (data) {
                // send result to popup
                // call self, to ensure click handler is attached again
                workspaceSavePopup(data.responseText);
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

/* L3 */
/* Clicking a workspace-acceptable toggles the
   workspace-acceptable. If it is enabled it also shows up in your
   workspace (if it is visible). */

// in use (26-09-2012)
// list of map layers (workspace)
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
}

/* Generic POST click handling: do preAction, post, if success do
postAction. */
function actionPostClick(event, preAction, postAction, parameters) {
    var url, target, target_id;
    event.preventDefault();

    url = $(event.target).attr("href");
    if (url === undefined) {
        // find in parents
        url = $(event.target).parents('a').attr("href");
    }
    target_id = $(event.target).attr("data-target-id");
    if (target_id === undefined) {
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
                div = $("<div/>").html(data).find(".dialog-box").find(target_id);
                target.html(div.html());
            }
            if (postAction !== undefined) {
                postAction();
            }
            if ($(event.target).hasClass("reload-after-action")) {
                window.location.reload();
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
        undefined,
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
    if (url === undefined) {
        // find in parents
        url = $(event.target).parents('.collage-popup').attr("href");
    }

    open_popup();
    $.getJSON(url, function (data) {
        set_popup_content(data);
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
function popup_click_handler(lon, lat, map, x_pixel, y_pixel) {
    var extent, radius, url, user_workspace_id;
    extent = map.getExtent();
    $("#map").css("cursor", "progress");
    url = $(".workspace").attr("data-url-lizard-map-search-coordinates");
    user_workspace_id = $(".workspace").attr("data-workspace-id");
    if (url !== undefined) {
        open_popup();
		// Get the current active CQL filters
		var cql_filters = JSON.stringify(
			$('#lizard-map-wms').data('wms-cql_filters'));
        $.getJSON(
            url,
            { x: lon, y: lat,
			  extent_left: extent.left,
			  extent_bottom: extent.bottom,
			  extent_right: extent.right,
			  extent_top: extent.top,
			  height: map.size.h,
			  width: map.size.w,
			  x_pixel: x_pixel,
			  y_pixel: y_pixel,
			  cql_filters: cql_filters,
			  srs: map.getProjection(),
              user_workspace_id: user_workspace_id
			  },

            function (data) {
                set_popup_content(data);
                $("#map").css("cursor", "default");
            }
        );


    }
}


/* Handle a hover */
/* Assumes there is 1 "main" workspace. Adds workspace_id to request. Only required when viewing workspaces of others */
function popup_hover_handler(lon, lat, map, x_pixel, y_pixel) {
    /* Show name of one item when hovering above a map */
    var extent, radius, url, user_workspace_id;
    extent = map.getExtent();

    url = $(".workspace").attr("data-url-lizard-map-search-name");
    user_workspace_id = $(".workspace").attr("data-workspace-id");
	var cql_filters = JSON.stringify(
		$('#lizard-map-wms').data('wms-cql_filters'));

    if (url !== undefined) {
        $.getJSON(
            url,
            { x: lon, y: lat,
			  extent_left: extent.left,
			  extent_bottom: extent.bottom,
			  extent_right: extent.right,
			  extent_top: extent.top,
			  height: map.size.h,
			  width: map.size.w,
			  x_pixel: x_pixel,
			  y_pixel: y_pixel,
			  cql_filters: cql_filters,
			  srs: map.getProjection(),
              user_workspace_id: user_workspace_id},
            function (data) {
                show_map_tooltip(data, map);
            }
        );
    }
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


function setUpCollageTablePopup() {
    $(".collage-table-popup").click(function (event) {
        var url;
        event.preventDefault();
        url = $(this).attr("href");
        open_popup();
        $.get(
            url,
            function(data) {
                set_popup_content(data);
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
    $.each(wms_layers, function (k, v) {
        v.mergeNewParams({'random': Math.random()});
    });
}


/* L3 is multiple selection turned on? */
function multipleSelection() {
    return $("a.map-multiple-selection").hasClass("active");
}

// handle a click in multiselect mode
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
                var box_x = e.pageX, box_y = e.pageY;
                if (isIE && ieVersion == 8) {
                    box_x = e.clientX;
                    box_y = e.clientY;
                }
                spawnCustomMovingBox(10, 10, box_x, box_y);
                var div;
                div = $(data).find("#edit-collage");
                $("#edit-collage").html(div.html());
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
        is_default, layer_names, identifier, is_base_layer, is_single_tile;
        layer_type = $(this).attr("data-layer-type");
        layer_name = $(this).attr("data-layer-name");
        is_default = $(this).attr("data-default");
        is_base_layer = ($(this).attr("data-is-base-layer") === 'True');
        is_single_tile = ($(this).attr("data-is-single-tile") === 'True');

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
                     'transparent': !is_base_layer},
                    {'isBaseLayer': is_base_layer,
                     'visibility': is_base_layer,
                     'numZoomLevels': 25,
                     'singleTile': is_single_tile,
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

function refreshWmsLayers() {
    // Add wms layers from workspace items.
    var $lizard_map_wms, osm_url, i, ids_found;
    ids_found = [];
    $lizard_map_wms = $("#lizard-map-wms");
    $(".workspace-wms-layer").each(function () {
        var name, url, params, options, id, index, animatable, needs_custom_handler;
        // WMS id, different than workspace ids.
        animatable = $(this).attr("data-workspace-wms-animatable");
        needs_custom_handler = $(this).attr("data-workspace-wms-needs-custom-handler");
        if (animatable === 'true' || needs_custom_handler === 'true') { return; }
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
        // HACK: force reproject = false for layers which still have this defined (in the database no less)
        // reprojection is deprecated
        if (options.reproject) {
            delete options['reproject'];
        }
        index = parseInt($(this).attr("data-workspace-wms-index"));

        // Add cql_filtering
        var layer_filters = $(this).data("workspace-wms-cql_filters");
        var selected_filters = $('#lizard-map-wms').data('wms-cql_filters');
        var cql_filters_arr = [];
        // Add the filters that are selected and available for this layer.
        for (key in selected_filters){
            if ($.inArray(key, layer_filters) !== -1){
                cql_filters_arr.push(key + '=' + selected_filters[key]);
            }
        }

        // Add possible cql_filters from the layer definition.
        if (params['cql_filter'] !== undefined) {
            cql_filters_arr.push(params['cql_filter']);
        }

        var cql_filters = '';
        if (cql_filters_arr.length > 0) {
            //Put the filters in geoserver format
            cql_filters = cql_filters_arr.join(' AND ');
        }


        // Each layer of a combined layer needs a cql_filter.
        if (cql_filters !== '') {
            var layerslength = params['layers'].split(',').length - 1;
            for (var i = 1; i <= layerslength; i ++) {
                cql_filters += ';' + cql_filters;
            }
        }

        if (wms_layers[id] === undefined) {
            // Create it.
            if (cql_filters.length > 0){
                // There are filters so add them to the request.
                params['cql_filter'] = cql_filters;
            }

            // add currently selected date range to url
            // HACK: viewstate is currently globally accessible
            var view_state = get_view_state();
            view_state = to_date_strings(view_state, false, true);
            if (/time|tijd/i.test(name) && view_state !== undefined) {
                if (view_state.dt_start && view_state.dt_end) {
                    params['time'] = view_state.dt_start + '/' + view_state.dt_end;
                }
            }

            var layer = new OpenLayers.Layer.WMS(name, url, params, options);
            wms_layers[id] = layer;
            map.addLayer(layer);
            layer.setZIndex(1000 - index); // looks like passing this via options won't work properly
        }
        else {
            // Update it.
            var layer = wms_layers[id];
            if (cql_filters.length > 0){
                // Update the layer if a cql_filter is used
                // with the new cql_filter params.
                layer.mergeNewParams({'cql_filter': cql_filters});
            }

            // add currently selected date range to url
            // HACK: viewstate is currently globally accessible
            var view_state = get_view_state();
            view_state = to_date_strings(view_state, false, true);
            if (/time|tijd/i.test(name) && view_state !== undefined) {
                if (view_state.dt_start && view_state.dt_end) {
                    var extraParams = {'time': view_state.dt_start + '/' + view_state.dt_end};
                    layer.mergeNewParams(extraParams);
                }
            }

            // set the correct Zindex
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
    // Set up animation control panel. No worries, it cleans itself up when
    // running multiple times.
    init_animation();
    init_control_panel();
}


/* Adds all layers (base + workspaces) to map. Refreshes all
workspaces. Layers from other sources are assumed to be 'static' */
function refreshLayers() {
    refreshBackgroundLayers();
    refreshWmsLayers();
}


function ZoomSlider(options) {
    var control = new OpenLayers.Control.PanZoomBar(options);

    OpenLayers.Util.extend(control, {
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
    return control;
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

function setUpMap() {
    var options, base_layer, MapClickControl, MapHoverControl,
	    layerSwitcherControl,
        map_click_control, zoom_panel, map_hover_control,
        javascript_click_handler_name, javascript_hover_handler_name,
        $lizard_map_wms, projection, display_projection, start_extent,
        start_extent_left, start_extent_top, start_extent_right,
        start_extent_bottom, max_extent, max_extent_left, max_extent_top,
        max_extent_right, max_extent_bottom;

    window.setUpMapDimensions();

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
        // rijksdriehoek
        options = {
            projection: new OpenLayers.Projection(projection),
            displayProjection: new OpenLayers.Projection(display_projection),
            units: "m",
            resolutions: [364, 242, 161, 107, 71, 47, 31, 21, 14, 9, 6, 4, 2.7, 1.8, 0.9, 0.45, 0.2, 0.1, 0.05, 0.025, 0.0125],
            maxExtent: max_extent,
            controls: []
        };
    }
    else
    {
        alert("Lizard-map onjuist geconfigureerd. Wilt U een kaart op deze pagina? Gebruik anders een andere template.");
    }

    // Map is globally defined.
    // Configure OpenLayers to retry loading tiles once
    OpenLayers.IMAGE_RELOAD_ATTEMPTS = 2;

    // Tell OpenLayers we manually load the theme, so we can control
    // the load order.
    options.theme = null;

    map = new OpenLayers.Map('map', options);
    // OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;

    refreshLayers();

    // Set up controls, zoom and center.
	LayerSwitcherControl = new OpenLayers.Control.NensLayerSwitcher();

    map.addControl(LayerSwitcherControl);
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
                hide_map_tooltip();
                var lonlat;
                lonlat = map.getLonLatFromViewPortPx(e.xy);
                if (multipleSelection()) {
                    addMultipleSelection(lonlat.lon, lonlat.lat, map, e);
                } else {
                    eval(javascript_click_handler_name)(
                        lonlat.lon, lonlat.lat, map, e.xy.x, e.xy.y);
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
                    lonlat.lon, lonlat.lat, map, e.xy.x, e.xy.y);
            },

            onMove: function (evt) {
                hide_map_tooltip();
            }
        });
    }

	if (!isAppleMobile) {
		zoom_panel = new OpenLayers.Control.Panel();
		zoom_panel.addControls([ new ZoomSlider({ zoomStopHeight: 3 }) ]);
		map.addControl(zoom_panel);
	}
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
    init_map_tooltip(map);

    // actually add the handers: keep these here for full iPad compatibility
    if (javascript_click_handler_name) {
        map_click_control = new MapClickControl();
        map.addControl(map_click_control);
        map_click_control.activate();
    }
    if (!isAppleMobile && javascript_hover_handler_name !== undefined) {
        map_hover_control = new MapHoverControl();
        map.addControl(map_hover_control);
        map_hover_control.activate();
    }
}

/* map-multiple-selection button */
function setUpMultipleSelection() {
    $(".map-multiple-selection").live("click", function () {
        $(this).find('i').toggleClass("icon-star-empty");
        $(this).find('i').toggleClass("icon-star");
        $(this).toggleClass("active");
    });
}

/* REST api with jQuery */
function makeHtml(data) {
    var items = [];
    // console.log(typeof data);
    if (typeof data === "string") {
        return data;
    }
    if (typeof data === "function") {
        return data;
    }
    $.each(data, function (key, val) {
        // console.log(key, val);
        if (val === null) {
            items.push('<li><span>' + key + '</span></li>');
        } else if ((typeof val === "string") && (val.indexOf('http://') === 0)) {
            items.push('<li><a href="' + val + '" class="rest-api">' + key + '</a></li>');
        } else {
            items.push('<li><span>' + key + '</span>' + makeHtml(val) + '</li>');
        }
     });
    return $('<ul/>', {html: items.join('')}).html();
}


function apiRequest(target) {
    var url;
    url = $(target).attr("href");
    $.getJSON(url, function (data) {
        $(target).parents(".rest-api-container").html(makeHtml(data));
    });
}

/**
 * Resize the graphs to the given maximum width and reload them.
 *
 * @param {number} max_image_width maximum width to resize each graph to
 * @param {function} callback function to call when a graph has been reloaded
 */
function reloadGraphs(max_image_width, callback, force) {
    // New Flot graphs
    $('.dynamic-graph').each(function () {
        reloadDynamicGraph($(this), callback, force);
    });
}

function reloadDynamicGraph($graph, callback, force) {
    // check if graph is already loaded
    if (force !== true && $graph.attr('data-graph-loaded')) return;

    // the wonders of asynchronous programming
    if ($graph.attr('data-graph-loading')) return;

    // check if element is visible (again):
    // flot can't draw on an invisible surface
    if ($graph.is(':hidden')) return;

    // determine whether to use flot or the image graph
    var flot_graph_data_url = $graph.attr('data-flot-graph-data-url');
    var image_graph_url = $graph.attr('data-image-graph-url');
    var graph_type;
    if (isIE && ieVersion < 9) {
        graph_type = 'image';
    }
    else {
        graph_type = (flot_graph_data_url) ? 'flot' : 'image';
    }
    var url = (graph_type == 'flot') ? flot_graph_data_url : image_graph_url;

    // add currently selected date range to url
    // HACK: viewstate is currently only in lizard_map,
    // but graphs are here, in lizard_ui, for some reason
    var view_state = get_view_state();
    view_state = to_date_strings(view_state);
    if (view_state !== undefined) {
        if (view_state.dt_start && view_state.dt_end) {
            url += '&' + $.param({
                dt_start: view_state.dt_start,
                dt_end: view_state.dt_end
            });
        }
    }

    if (url) {
        // add a spinner
        var $loading = $('<img src="/static_media/lizard_ui/ajax-loader.gif" class="graph-loading-animation" />');
        $graph.empty().append($loading);
        $graph.attr('data-graph-loading', 'true');

        // remove spinner when loading has finished (either with or without an error)
        var on_loaded = function () {
            $graph.removeAttr('data-graph-loading');
            $loading.remove();
        };

        // set attribute and call callback when drawing has finished
        var on_drawn = function () {
            $graph.attr('data-graph-loaded', 'true');
            if (callback !== undefined) {
                callback();
            }
        };

        // show a message when loading has failed
        var on_error = function () {
            on_loaded();
            $graph.html('Fout bij het laden van de gegevens. Te veel data. Pas uw tijdsperiode aan of exporteer de tijdreeks.');
        };

        // for flot graphs, grab the JSON data and call Flot
        if (graph_type == 'flot') {
            $.ajax({
                url: url,
                method: 'GET',
                dataType: 'json',
                success: function (response) {
                    on_loaded();

                    // tab might have been hidden in the meantime
                    // so check if element is visible again:
                    // we can't draw on an invisible surface
                    if ($graph.is(':hidden')) return;

                    var plot = flotGraphLoadData($graph, response);
                    on_drawn();
                    //bindPanZoomEvents($graph);
                },
                timeout: 20000,
                error: on_error
            });
        }
        // for static image graphs, just load the image as <img> element
        else if (graph_type == 'image') {
            var get_url_with_size = function () {
                // compensate width slightly to prevent a race condition
                // with the parent element
                var width = Math.round($graph.width() * 0.95);
                // add available width and height to url
                var url_with_size = url + '&' + $.param({
                    width: width,
                    height: $graph.height()
                });
                return url_with_size;
            };

            var update_size = function () {
                var $img = $(this);
                $img.data('current-loaded-width', $img.width());
                $img.data('current-loaded-height', $img.height());
            };

            var on_load_once = function () {
                on_loaded();

                // tab might have been hidden in the meantime
                // so check if element is visible again:
                // we can't draw on an invisible surface
                if ($graph.is(':hidden')) return;

                $graph.append($(this));
                on_drawn();
            };

            var $img = $('<img/>')
                .one('load', on_load_once) // ensure this is only called once
                .load(update_size)
                .error(on_error)
                .attr('src', get_url_with_size());

            var update_src = function () {
                $img.attr('src', get_url_with_size());
            };

            // list to parent div resizes, but dont trigger updating the image
            // until some time (> 1 sec) has passed.
            var timeout = null;
            $graph.resize(function () {
                if (timeout) {
                    // clear old timeout first
                    clearTimeout(timeout);
                }
                timeout = setTimeout(update_src, 1500);
            });
        }
    }
}

var MS_SECOND = 1000;
var MS_MINUTE = 60 * MS_SECOND;
var MS_HOUR = 60 * MS_MINUTE;
var MS_DAY = 24 * MS_HOUR;
var MS_MONTH = 30 * MS_DAY;
var MS_YEAR = 365 * MS_DAY;

/**
 * Draw the response data to a canvas in DOM element $graph using Flot.
 *
 * @param {$graph} DOM element which will be replaced by the graph
 * @param {response} a dictionary containing graph data such as x/y values and labels
 */
function flotGraphLoadData($container, response) {
    var data = response.data;
    if (data.length === 0) {
        $container.html('Geen gegevens beschikbaar.');
        return;
    }
    // Convert ISO 8601 strings to seconds since ECMAScript epoch
    for (var i=0; i<data.length; i++) {
        var line = data[i];
        for (var j=0; j<line.data.length; j++) {
            line.data[j][0] = moment(line.data[j][0]).toDate().getTime();
        }
    }
    var t0 = moment().toDate().getTime();
    var markings = [
        { color: '#d22', xaxis: { from: t0, to: t0 }, lineWidth: 2 }
    ];
    var defaultOpts = {
        series: {
            points: { show: true, hoverable: true, radius: 1 },
            shadowSize: 0
        },
        yaxis: {
            zoomRange: [false, false],
            panRange: false
        },
        xaxis: {
            mode: "time",
            zoomRange: [1 * MS_MINUTE, 400 * MS_YEAR],
            timezone: 'utc'
        },
        grid: { hoverable: true, labelMargin: 15, markings: markings },
        pan: { interactive: true },
        zoom: { interactive: true }
    };
    if (isAppleMobile) {
        // enable touch
        defaultOpts.touch = { pan: 'xy', scale: 'x', autoWidth: false, autoHeight: false };
        // disable flot.navigate pan & zoom
        defaultOpts.pan.interactive = false;
        defaultOpts.zoom.interactive = false;
    }

    // set up elements nested in our assigned parent div
    $container.css('position', 'relative');
    // first row
    var $graph_row = $('<div class="flot-graph-row" />')
        .css({
            position: 'absolute',
            left: 0, top: 0, bottom: 48, right: 0
        });
    var $y_label_text_wrapper = $('<div/>')
        .css({
            position: 'absolute',
            bottom: 80,
            width: 20
        });
    var $y_label_text = $('<div class="flot-graph-y-label-text" />')
        .css({
            'white-space': 'nowrap',
            'background-color': '#fff'
        })
        .transform({rotate: '-90deg'})
        .html(response.y_label);
    $y_label_text_wrapper.append($y_label_text);
    var $y_label = $('<span class="flot-graph-y-label" />')
        .css({
            position: 'absolute',
            left: 0, top: 0, bottom: 0, width: 20
        });
    $y_label.append($y_label_text_wrapper);
    $graph_row.append($y_label);
    var $graph = $('<span class="flot-graph-canvas" />')
        .css({
            position: 'absolute',
            left: 20, top: 0, bottom: 0, right: 0
        });
    $graph_row.append($graph);
    $container.append($graph_row);

    // second row
    // just a spacer for now, have jquery.flot.axislabels.js draw the actual label
    var $x_label = $('<div class="flot-graph-x-label" />')
        .css({
            position: 'absolute',
            left: 60, bottom: 30, right: 0,
            height: 18
        })
        .html(response.x_label);
    $container.append($x_label);

    // third row
    var $control_row = $('<div class="flot-graph-control-row" />')
        .css({
            position: 'absolute',
            left: 0, bottom: 0, right: 0,
            height: 30
        });
    // controls
    // TODO should implement JavaScript gettext / i18n
    var $c_reset = $('<button title="Reset zoom" class="btn" type="button"><i class="icon-refresh"></i></button>');
    $control_row.append($c_reset);

    var $c_plus = $('<button title="Zoom in" class="btn" type="button"><i class="icon-zoom-in"></i></button>');
    $control_row.append($c_plus);

    var $c_min = $('<button title="Zoom uit" class="btn" type="button"><i class="icon-zoom-out"></i></button>');
    $control_row.append($c_min);

    var $c_bwd = $('<button title="Schuif naar links" class="btn" type="button"><i class="icon-backward"></i></button>');
    $control_row.append($c_bwd);

    var $c_fwd = $('<button title="Schuif naar rechts" class="btn" type="button"><i class="icon-forward"></i></button>');
    $control_row.append($c_fwd);

    $container.append($control_row);

    // initial plot
    var plot = $.plot($graph, data, defaultOpts);
    bindPanZoomEvents($graph);

    if (!isAppleMobile) {
        function showGraphTooltip(x, y, datapoint) {
            var dateFormatted = moment.utc(datapoint[0]).format('LL H:mm');
            var valueFormatted = Math.round(datapoint[1] * 100) / 100;
            $('<div id="graphtooltip">' + dateFormatted + '&nbsp;&nbsp;'+ valueFormatted + '</div>').css({
                'position': 'absolute',
                'top': y - 25,
                'left': x + 5,
                'padding': '0.4em 0.6em',
                'border-radius': '0.5em',
                'border': '1px solid #111',
                'background-color': '#fff',
                'z-index': 11000
            }).appendTo("body");
        }

        $graph.bind("plothover", function (event, pos, item) {
            if (item) {
                $("#graphtooltip").remove();
                showGraphTooltip(item.pageX, item.pageY, item.datapoint);
            } else {
                $("#graphtooltip").remove();
            }
        });
    }

    $c_reset.click(function () {
        $.each(plot.getXAxes(), function (idx, axis) {
            axis.options.min = null;
            axis.options.max = null;
        });
        $.each(plot.getYAxes(), function (idx, axis) {
            axis.options.min = null;
            axis.options.max = null;
        });
        plot.setupGrid();
        plot.draw();
    });
    $c_plus.click(function () {
        plot.zoom({ amount: 2 });
    });
    $c_min.click(function () {
        plot.zoom({ amount: 0.5 });
    });
    $c_bwd.click(function () {
        plot.pan({ left: -500 });
    });
    $c_fwd.click(function () {
        plot.pan({ left: 500 });
    });

    return plot;
}

/**
* Bind several flot graphs together. When navigating through one graph, the other graphs
* should follow the zoom levels, and extent.
* Functions come from the controlnext app. http://github.com/lizardsystem/controlnext
*/
function panAndZoomOtherGraphs(plot) {
    var axes = plot.getAxes();
    var xmin = axes.xaxis.min;
    var xmax = axes.xaxis.max;
    $('.flot-graph-canvas').each(function () {
        var otherPlot = $(this).data('plot');
        if (plot !== otherPlot) {
            var otherXAxisOptions = otherPlot.getAxes().xaxis.options;
            otherXAxisOptions.min = xmin;
            otherXAxisOptions.max = xmax;
            if ($(this).is(':visible')) {
                otherPlot.setupGrid();
                otherPlot.draw();
            }
        }
    });
}

function bindPanZoomEvents($graph) {
    // fix IE performance
    if (isIE && ieVersion < 9) {
        return;
    }

    $graph.bind('plotzoom', function (event, plot) {
        panAndZoomOtherGraphs(plot);
    });

    $graph.bind('plotpan', function (event, plot) {
        panAndZoomOtherGraphs(plot);
    });
}

/**
 * Take an associative array, and convert all Moment.js objects to
 * ISO8601 datetime strings.
 *
 * @param {Array} assoc_array An associative array containing Moment.js objects.
 * @param {boolean} [inplace] When evaluated to true, conversion happens in place
 * and the original array is modified.
 */
var to_date_strings = function (assoc_array, inplace, wms_compatible) {
    if (!inplace)
        assoc_array = $.extend({}, assoc_array);
    $.each(assoc_array, function(k, v) {
        if (v) {
            if (moment.isMoment(v)) {
                if (wms_compatible === true) {
                    assoc_array[k] = v.format('YYYY-MM-DDTHH:mm:ss') + 'Z';
                }
                else {
                    assoc_array[k] = v.format('YYYY-MM-DDTHH:mm:ssZ');
                }
            }
            else if (v instanceof Object) {
                to_date_strings(v, true);
            }
        }
    });
    return assoc_array;
};

/**
 * Take an associative array, and convert all string items whose key contain 'date', or
 * starting with 'dt', to a Moment.js date object.
 *
 * @param {Object} An associative array containing dates, e.g.
 * <pre>{'a': 'foo', 'dt_start': '2012-09-28T22:00:00.000Z'}</pre>.
 * @param {boolean} [inplace] When evaluated to true, conversion happens in place
 * and the original array is modified.
 */
var to_date_objects = function (assoc_array, inplace) {
    if (!inplace)
        assoc_array = $.extend({}, assoc_array);
    $.each(assoc_array, function(k, v) {
        if (k && v) {
            if (typeof v == 'string' && (
                 k.substring(0, 2) == 'dt' || k.indexOf('date') != -1 || k == 'start' || k == 'end'
            )) {
                // convert to Moment.js date object
                assoc_array[k] = moment.utc(v);
            }
            else if (v instanceof Object) {
                to_date_objects(v, true);
            }
        }
    });
    return assoc_array;
};

/**
 * Like $.ajax, but data is converted to json (with optional datetime-awareness).
 */
var lizard_api_put = function (ajax_opts, convert_datetimes) {
    var opts = {
        type: 'PUT',
        contentType: 'application/json',
        dataType: 'json'
    };
    $.extend(opts, ajax_opts);
    if (convert_datetimes)
        opts.data = $.toJSON(to_date_strings(opts.data));
    else
        opts.data = $.toJSON(opts.data);
    return $.ajax(opts);
};

/**
 * Like $.ajax, but datetimes in the data are parsed to Moment.js objects.
 */
var lizard_api_get = function (ajax_opts, convert_datetimes) {
    var opts = {
        type: 'GET',
        contentType: 'application/json',
        dataType: 'json'
    };
    $.extend(opts, ajax_opts);
    var _success = opts.success;
    if (convert_datetimes && _success) {
        opts.success = function (data, textStatus, jqXHR) {
            return _success(to_date_objects(data), textStatus, jqXHR);
        };
    }
    return $.ajax(opts);
};

/**
 * Use by lizard-ui!
 */
function get_view_state() {
    return _view_state;
}

function set_view_state(params) {
    $.extend(_view_state, params);
    save_view_state_to_server();
}

function save_view_state_to_server() {
    // update the session on the server side
    var view_state = _view_state;
    lizard_api_put({
        url: '/map/view_state_service/', // TODO
        data: view_state,
        success: function (data) {
        }
    }, true);
}

function setup_view_state() {
    var view_state = _view_state;
    if ($('.popup-date-range').exists()) {
        $('.popup-date-range').data('daterangepicker').setRange(view_state.range_type, view_state.dt_start, view_state.dt_end);
        daterangepicker_label_update();
    }
    reloadGraphs();
}

function daterangepicker_label_update() {
    var view_state = _view_state;
    var html = view_state.dt_start.format('LL') + ' &mdash; ' + view_state.dt_end.format('LL');
    $('.popup-date-range span.action-text').html(html);
    // fix IE9 not being able to determine width
    if (isIE && ieVersion == 9) {
        $('.popup-date-range span.action-text').parent().parent().width(300);
    }
}

function setup_daterangepicker() {
    if ($('.popup-date-range').exists()) {
        var daterangepicker_options = {
            opens: 'left'
        };
        if (lizard_map && lizard_map.daterangepicker_options) {
            // Use the options as configured by the Django template.
            $.extend(daterangepicker_options, lizard_map.daterangepicker_options);
        }
        else {
            // Backwards compatibility: use some default options.
            $.extend(daterangepicker_options, {
                format: 'DD-MM-YYYY',
                locale: {
                    applyLabel:'Bevestigen',
                    cancelLabel:'Annuleren',
                    customRangeLabel:'Handmatige invoer',
                    daysOfWeek:['zo', 'ma', 'di', 'wo', 'do', 'vr','za'],
                    monthNames:['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'],
                    firstDay:0
                },
                ranges: {
                    'Afgelopen dag': [
                        moment.utc().subtract('days', 1),
                        moment.utc(),
                        'today'
                    ],
                    'Afgelopen 2 dagen': [
                        moment.utc().subtract('days', 2),
                        moment.utc(),
                        '2_day'
                    ],
                    'Afgelopen week': [
                        moment.utc().subtract('weeks', 1),
                        moment.utc(),
                        'week'
                    ],
                    'Afgelopen maand': [
                        moment.utc().subtract('months', 1),
                        moment.utc(),
                        'month'
                    ],
                    'Afgelopen jaar': [
                        moment.utc().subtract('years', 1),
                        moment.utc(),
                        'year'
                    ]
                }
            });
        }
        var picker = $('.popup-date-range').daterangepicker(
            daterangepicker_options,
            function (range_type, dt_start, dt_end) {
                set_view_state({range_type: range_type, dt_start: dt_start, dt_end: dt_end});
                daterangepicker_label_update();
                // hack to support reloading after changing the date (collage page)
                if ($('.popup-date-range').hasClass('reload-after-action')) {
                    setTimeout(window.location.reload, 1337);
                }
                else {
                    reloadGraphs(undefined, undefined, true);
                    refreshWmsLayers();
                }
            }
        );
    }
}

function setUpSidebarPopupDisappearing () {
  $("#sidebar").scroll(function() {
    // Fixing 'zombie' popovers when the user scrolls with an info icon popover enabled
    $('.has_popover').each(function(i,v){ $(v).popover("hide"); });
  });
}

function setup_location_list () {
    var $element = $('.popup-location-list');
    if ($element.exists()) {
        var template = '' +
        '<div class="location-list">' +
            '<form class="form-search">' +
                '<legend>Zoek naar locaties</legend>' +
                '<input type="text" class="search-query" placeholder="Type ten minste drie karakters..." style="width:300px"/>' +
                '<button type="submit" class="btn" style="margin-left:10px">Zoek</button>' +
            '</form>' +
            '<div class="results" />' +
        '</div>';
        var $container = $(template);
        var $form = $container.find('.form-search');
        var $input = $container.find('input');
        var $button = $container.find('button');
        var $results = $container.find('.results');

        function show (e) {
            open_popup(false);
            set_popup_content($container);

            $input.focus();
            $button.click(search);
            $form.submit(search);

            // show some initial search results
            $input.val('');
            setTimeout(search, 500);

            if (e) {
                e.stopPropagation();
                e.preventDefault();
            }
            return false;
        }

        function search (e) {
            var params = $.param({
                name: $input.val()
            });
            $results.empty();
            var $loading = $('<img src="/static_media/lizard_ui/ajax-loader.gif" class="popup-loading-animation" />');
            $results.append($loading);
            lizard_api_get({
                url: '/map/location_list_service/?' + params, // TODO
                success: function (data) {
                    $results.empty();
                    if (data.length === 0) {
                        $results.html('Niets gevonden.');
                    }
                    else {
                        $.each(data, function () {
                            var item = this;
                            var $link = $('<a title="Toevoegen aan selectie" data-target-id="#edit-collage" class="ss_sprite ss_star collage-add" />')
                                .attr('data-adapter-class', item[0])
                                .attr('data-adapter-layer-json', item[1])
                                .attr('data-identifier', item[2])
                                .attr('data-name', item[3])
                                .attr('href', item[5])
                                .html(item[4]);
                            var $div = $('<div/>')
                                .append($link);
                            $results.append($div);
                        });
                    }
                }
            }, false);

            if (e) {
                e.stopPropagation();
                e.preventDefault();
            }
            return false;
        }

        $element.on('click', show);
    }
}

$(document).ready(function () {
    setup_daterangepicker();
    setup_view_state();
    setup_movable_dialog();
    setup_location_list();
    setUpWorkspaceAcceptable();
    setUpActions();
    setUpDataFromUrl();
    setUpWorkspaceButtons();
    setUpWorkspaceItemPanToLayer();
    setUpMapLoadDefaultLocation();
    setUpWorkspaceLoad();
    setUpWorkspaceSavePopup();
    setUpCollageTablePopup();
    setUpSidebarPopupDisappearing();
    $(".workspace").workspaceInteraction();
    if ($('#map').exists()) {
        setUpMap();
        setUpMultipleSelection();
    }
});
