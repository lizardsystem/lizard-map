// jslint configuration; btw: don't put a space before 'jslint' below.
/*jslint browser: true */

var flot_x_global_min, flot_x_global_max, flot_reload_timeout;
var reload_faulty_timeout;


// in use (26-09-2012)
// left workspace + collage checkboxes
jQuery.fn.liveCheckboxes = function () {
    return this.each(function () {
        var $workspace = $(this);
        $workspace.find(".workspace-item-toggle-visiblity").live('click', function () {
            var url = $workspace.attr("data-url-lizard-map-workspace-item-edit");
            var $workspaceItem = $(this).parents('.workspace-item');
            var isVisible = $workspaceItem.data('visible').toLowerCase() == 'true';
            var newIsVisible = !isVisible;
            var id = $workspaceItem.data('object-id');
            $.ajax({
                url: url,
                data: { workspace_item_id: id, visible: newIsVisible },
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
        width: 600,
        height: 480,
        zIndex: 5000,
        close: function (event, ui) {
            // clear contents on close
            $('#movable-dialog-content').empty();
            // remove any added popup markers from map
            clearMapMarkers();
        },
        position: { my: 'left center', at: 'left+15% center', of: window }
    };

    // make an exception for iPad
    if (isAppleMobile) {
        // dragging on touchscreens isn't practical
        options.draggable = false;
        // resizing neither
        options.resizable = false;
        // make width 90% of the entire window
        options.width = $(window).width() * 0.7;
        // make height 80% of the entire window
        options.height = $(window).height() * 0.7;
    }

    $('#movable-dialog').dialog(options);
}

var boxAwesomeTabIndex = 0;

function boxAwesomeAddTab(marker) {
    var iconClass = 'icon-pushpin';
    var tabId = 'box-awesome-content-popup-' + (boxAwesomeTabIndex++);

    var $ul = $('#box-awesome-tabs > ul');
    var $content = $('#box-awesome-tabs > .tab-content');

    // close other tabs
    $ul.find('.popup-li').remove();
    $content.find('.popup-div').remove();
    // /close other tabs

    var $newLi = $('<li class="popup-li">');
    var $link = $('<a data-toggle="tab">').attr('href', '#' + tabId);
    var $icon = $('<i>').addClass(iconClass);

    var $tabContent = $('<div class="popup-div">')
          .addClass('tab-pane sidebar-inner')
          .attr('id', tabId);

    // var $closeBtn = $('<button type="button" class="close">&times;</button>')
    // .on('click', function (event) {
    // removeMapMarker(marker);
    // $newLi.remove();
    // $tabContent.remove();
    // $ul.find('a:last').trigger('click');
    // });
    // disabled multiple tab support
    // $link.on('click', function (event) {
    // resetColorAllMarkers();
    // adjustedPanTo(marker.lonlat.lon, marker.lonlat.lat);
    // marker.icon.setUrl(window.iconUrlRed);
    // });

    // var $closeBtnPane = $('<div style="height: 20px;">')
    // .append($closeBtn)
    // .appendTo($tabContent);

    var $popupContentPane = $('<div>')
          .html('<div class="popup-loading-animation"></div>')
          .appendTo($tabContent);

    $link.append($icon);
    $newLi.append($link);

    $ul.append($newLi);
    $content.append($tabContent);

    $link.tab('show');
    return $popupContentPane;
}

function boxAwesomeSetContent($contentPane, data) {
    var html, overlay, i;
    if (data !== null) {
        if (data instanceof jQuery) {
            $contentPane.empty().append(data);
        }
        else if (data.html && data.html.length !== 0) {
            // We got at least 1 result back.
            if (data.html.length === 1) {
                // Just copy the contents directly into the target div.
                $contentPane.html(data.html[0]);
                // Have the graphs fetch their data.
                reloadGraphsIn($contentPane);
            }
            else {
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
                $contentPane.html(html);

                // Call jQuery UI Tabs to actually instantiate some tabs.
                $contentPane.find("#popup-tabs").tabs({
                    idPrefix: 'popup-tab',
                    selected: 0,
                    show: function (event, ui) {
                        // Have the graphs fetch their data.
                        reloadGraphsIn($contentPane);
                    },
                    create: function (event, ui) {
                        // Have the graphs fetch their data.
                        reloadGraphsIn($contentPane);
                    }
                });
            }
            $contentPane.find("#popup-subtabs").tabs({
                idPrefix: 'popup-subtab',
                selected: 0
            });
        }
        else if (data.indexOf && data.indexOf("div") != -1) {
            // Apparantly data can also contain an entire <html> document
            $contentPane.html(data);
            // Have the graphs fetch their data.
            reloadGraphsIn($contentPane);
        }
        else {
            $contentPane.html(gettext("Nothing has been found around this location."));
        }
    }
}

// in use (26-09-2012)
// main (single) popup
function open_popup(show_spinner) {
    $("#movable-dialog-content").empty();
    if (show_spinner === undefined || show_spinner) {
        var $loading = $('<img src="/static_media/lizard_ui/ajax-loader.gif" class="popup-loading-animation">');
        $("#movable-dialog-content").append($loading);
    }
    $("#movable-dialog").dialog('option', {title: ''});
    $("#movable-dialog").dialog("open");
}

// in use (26-09-2012)
// main (single) popup
function set_popup_content(data, title) {
    var html, overlay, i;
    if (data !== null) {
        if (data instanceof jQuery) {
            $("#movable-dialog-content").empty().append(data);
        }
        else if (data.html && data.html.length !== 0) {
            if (title) {
                $("#movable-dialog").dialog('option', {title: title});
            }
            // We got at least 1 result back.
            if (data.html.length === 1) {
                // Just copy the contents directly into the target div.
                $("#movable-dialog-content").html(data.html[0]);
                // Have the graphs fetch their data.
                reloadGraphs();
            }
            else {
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
        }
        else if (data.indexOf && data.indexOf("div") != -1) {
            // Apparantly data can also contain an entire <html> document
            $("#movable-dialog-content").html(data);
            // Have the graphs fetch their data.
            reloadGraphs();
        }
        else {
            $("#movable-dialog-content").html(gettext("Nothing has been found around this location."));
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
    // Make the items in a workspace sortable.
    this.each(function () {
        var $workspace = $(this);
        var $workspaceItems = $workspace.find(".workspace-items");
        var onUpdate = function (event, ui) {
            var url = $workspace.attr("data-url-lizard-map-workspace-item-reorder");
            var order = $workspaceItems.sortable("serialize");
            $.post(
                url,
                order,
                function () {
                    $workspace.updateWorkspace();
                }
            );
        };
        /*
          $workspaceItems.sortable({
          update: onUpdate,
          helper: 'clone',
          connectWith: '.workspace-items',
          cursor: 'move',
          revert: 'true',
          placeholder: 'workspace-item-sortable-placeholder',
          items: '.workspace-item'
          });
        */
        $workspace.find('.workspace-item-move-up').on('click', function (event) {
            var $workspaceItem = $(this).parents('.workspace-item');
            $workspaceItem.prev().before($workspaceItem);
            onUpdate();
        });
        $workspace.find('.workspace-item-move-down').on('click', function (event) {
            var $workspaceItem = $(this).parents('.workspace-item');
            $workspaceItem.next().after($workspaceItem);
            onUpdate();
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
                //if ($('#edit-workspace', $holder).length === 0) {
                //    debugger;
                //}

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
                if (result.redirect)
                    window.location.href = result.redirect;
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
            $layer_button = $("#map");
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
              target.html(gettext("Error on action. Reload the page and try it again."));
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
    event.preventDefault();
    var $target, adapter_class, name, adapter_layer_json, identifier;
    /* New bootstrap-era interaction */
    {
        var $collage_button, $moving_box, move_down, move_right;
        $collage_button = $("#action-collage-link");
        $("#page").after('<div id="moving-box">');
        $moving_box = $("#moving-box");
        $moving_box.offset($(this).offset());
        $moving_box.width($(this).width());
        $moving_box.height($(this).height());
        move_down = $collage_button.offset().top - $(this).offset().top;
        move_right = $collage_button.offset().left - $(this).offset().left;
        $moving_box.animate({
            left: '+=' + move_right,
            top: '+=' + move_down,
            width: $collage_button.width(),
            height: $collage_button.height()
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

function resetColorAllMarkers() {
    $.each(window.popupClickMarkersLayer.markers, function (idx) {
        this.setUrl(window.iconUrl);
    });
}

function addMapMarker(x, y) {
    if (window.popupClickMarkersLayer) {
        var marker = new OpenLayers.Marker(new OpenLayers.LonLat(x, y), window.popupClickMarkerIcon.clone());
        window.popupClickMarkersLayer.addMarker(marker);
        return marker;
    }
}

function removeMapMarker(marker) {
    if (window.popupClickMarkersLayer && marker) {
        window.popupClickMarkersLayer.removeMarker(marker);
    }
}

function clearMapMarkers() {
    if (window.popupClickMarkersLayer) {
        window.popupClickMarkersLayer.clearMarkers();
    }
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
	// clear existing markers, add a new marker
        clearMapMarkers();
        //resetColorAllMarkers();
        var marker = addMapMarker(lon, lat);

        var $contentPane = boxAwesomeAddTab(marker);

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
                boxAwesomeSetContent($contentPane, data);
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
        is_default, layer_names, identifier, is_base_layer, is_single_tile,
	zoomlevel;
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
                    google_type = google.maps.MapTypeId.TERRAIN;
                }
                else if (data_google_type === "3") {
                    google_type = google.maps.MapTypeId.HYBRID;
		    zoomlevel = 20;
                }
                else if (data_google_type === "4") {
                    google_type = google.maps.MapTypeId.SATELLITE;
		    zoomlevel = 21;

                } else {
                    google_type = '';
                }
                base_layer = new OpenLayers.Layer.Google(
                    layer_name,
                    {type: google_type,
                     transitionEffect: 'resize',
                     sphericalMercator: true,
                     numZoomLevels: zoomlevel});
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
        var name, url, params, options, info, id, index, animatable;
        // WMS id, different than workspace ids.
        //animatable = $(this).attr("data-workspace-wms-animatable");
        //if (animatable === 'true') { return; }
        id = $(this).attr("data-workspace-wms-id");
        ids_found.push(id);
        name = $(this).attr("data-workspace-wms-name");
        url = $(this).attr("data-workspace-wms-url");
        params = $(this).attr("data-workspace-wms-params");
        params = $.parseJSON(params);
        // Fix for partial images on tiles
        params.tilesorigin = [map.maxExtent.left, map.maxExtent.bottom];
        options = $(this).attr("data-workspace-wms-options");
        options = $.parseJSON(options);
        info = $(this).attr("data-workspace-wms-info");
        if (info) {
            info = $.parseJSON(info);
        }
        // HACK: force reproject = false for layers which still have this defined (in the database no less)
        // reprojection is deprecated
        if (options.reproject) {
            delete options.reproject;
        }
        options.displayInLayerSwitcher = true;
        index = parseInt($(this).attr("data-workspace-wms-index"));

        // Add cql_filtering
        var layer_filters = $(this).data("workspace-wms-cql_filters");
        var cql_filters_arr = [];

        var selected_filters = $('#lizard-map-wms').data('wms-cql_filters');
	var operator = 'AND'; // Use AND as the default operator.

	if (typeof(selected_filters) != "undefined") {
	    var keys = selected_filters.keys;
	    var values = selected_filters.values;
	    operator = selected_filters.operator;

	    // Add the filters that are selected and available for this layer.
	    for (var i=0; i<keys.length; i++) {
		if ($.inArray(keys[i], layer_filters) !== -1){
		    cql_filters_arr.push(keys[i] + '=' + values[i]);
		}
	    }

	}

        // Add possible cql_filters from the layer definition.
        if (params['.cql_filter'] !== undefined) {
            cql_filters_arr.push(params.cql_filter);
        }

        var cql_filters = '';
        if (cql_filters_arr.length > 0) {
            //Put the filters in geoserver format
            cql_filters = cql_filters_arr.join(
		' ' + operator + ' ');
        }


        // Each layer of a combined layer needs a cql_filter.
        if (cql_filters !== '') {
            var layerslength = params.layers.split(',').length - 1;
            for (var i = 1; i <= layerslength; i ++) {
                cql_filters += ';' + cql_filters;
            }
        }
        var view_state, layer;

        if (wms_layers[id] === undefined) {
            // Create it.
            if (cql_filters.length > 0){
                // There are filters so add them to the request.
                params.cql_filter = cql_filters;
            }
            // add currently selected date range to url
            // HACK: viewstate is currently globally accessible
            view_state = get_view_state();
            view_state = to_date_strings(view_state, false, true);
            if (info && info.timepositions && view_state !== undefined) {
                if (view_state.dt_start && view_state.dt_end) {
                    params.time = view_state.dt_start + '/' + view_state.dt_end;
                }
            }

            layer = new OpenLayers.Layer.WMS(name, url, params, options);
            wms_layers[id] = layer;
            map.addLayer(layer);
            layer.setZIndex(1000 - index); // looks like passing this via options won't work properly
        }
        else {
            // Update it.
            layer = wms_layers[id];
            if (cql_filters.length > 0){
                // Update the layer if a cql_filter is used
                // with the new cql_filter params.
                layer.mergeNewParams({'cql_filter': cql_filters});
            }
            // add currently selected date range to url
            // HACK: viewstate is currently globally accessible
            view_state = get_view_state();
            view_state = to_date_strings(view_state, false, true);
            if (info && info.timepositions && view_state !== undefined) {
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
    //init_animation();
    //init_control_panel();
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
	    px = new OpenLayers.Pixel(425, 43);
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
    OpenLayers.Renderer.SVG.prototype.MAX_PIXEL = Number.MAX_VALUE;

    // add a layer which shows where the user has clicked
    // expose marker layer via window, might as well since everying is exposed this way
    window.popupClickMarkersLayer = new OpenLayers.Layer.Markers(
        'Popup markers',
        {
            displayInLayerSwitcher: false
        }
    );
    var popupClickMarkerSize = new OpenLayers.Size(21, 25);
    var popupClickMarkerOffset = new OpenLayers.Pixel(-(popupClickMarkerSize.w/2), -popupClickMarkerSize.h);
    window.iconUrl = 'http://www.openlayers.org/dev/img/marker-green.png';
    window.iconUrlRed = 'http://www.openlayers.org/dev/img/marker.png';
    var openLayersUrlBase = $('#openlayers-script').data('openlayers-url');
    if (openLayersUrlBase) {
        window.iconUrl = openLayersUrlBase + 'img/marker-green.png';
        window.iconUrlRed = openLayersUrlBase + 'img/marker.png';
    }
    window.popupClickMarkerIcon = new OpenLayers.Icon(window.iconUrlRed, popupClickMarkerSize, popupClickMarkerOffset);
    map.addLayer(popupClickMarkersLayer);
    // Note: this needs to happen AFTER adding the layer to the map...
    window.popupClickMarkersLayer.setZIndex(1010);

    // add a control displaying the mouse coordinates
    map.addControl(
        new OpenLayers.Control.MousePosition({
            separator: ', ',
            numDigits: 2
        })
    );

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

function reloadFaultyGraphs() {
    $('.dynamic-graph').each(function () {
        if ($(this).data('fault_when_loading')) {
            reloadDynamicGraph($(this), undefined, true);
        }
    });
}

function reloadZoomableGraphs(max_image_width, callback) {
    $('.dynamic-graph-zoomable').each(function () {
        reloadDynamicGraph($(this), callback, true);
    });
}


function reloadGraphsIn($el) {
    $el.find('.dynamic-graph').each(function () {
        reloadDynamicGraph($(this));
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

    // add currently selected date range to url as a default.
    // HACK: viewstate is currently globally accessible
    // But first look if we've set our flot zoom parameters.
    var view_state = get_view_state();
    view_state = to_date_strings(view_state);
    var offset = $('.popup-date-range').attr('data-offset');
    if (flot_x_global_max) {
        dt_start = moment.utc(flot_x_global_min).format('YYYY-MM-DDTHH:mm:ss') + offset;
        dt_end = moment.utc(flot_x_global_max).format('YYYY-MM-DDTHH:mm:ss') + offset;
        url += '&' + $.param({
            dt_start: dt_start,
            dt_end: dt_end
        });
    }
    else if (view_state !== undefined) {
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
        if (flot_x_global_min) {
            // Flot dynamic reloading; don't empty the graph totally.
            $graph.append($loading);
        } else {
            $graph.empty().append($loading);
        }
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
            $graph.data('fault_when_loading', true);
            if (!flot_x_global_min) {
                // Not flot dynamic reloading; so it is ok to show
                // a graph-disabling html error.
                // The message is shown for 15 seconds, afterwards the graphs
                // are reloaded automatically.
                if (reload_faulty_timeout) {
                    clearTimeout(reload_faulty_timeout);
                }
                reload_faulty_timeout = setTimeout(reloadFaultyGraphs, 15000);
                $graph.html(
                    '<i class="icon-exclamation-sign text-success"></i> ' +
                    'U heeft een grote hoeveelheid data opgevraagd. Het ' +
                    'opbouwen van de grafiek gaat enkele seconden duren.');
            }
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
                timeout: 28000,
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
        if (!flot_x_global_min) {
            $container.html(gettext('No data available at this period.'));
        }
        return;
    }
    // Convert ISO 8601 strings to seconds since ECMAScript epoch
    for (var i=0; i<data.length; i++) {
        var line = data[i];
        for (var j=0; j<line.data.length; j++) {
            line.data[j][0] = moment(line.data[j][0]).toDate().getTime();
        }
    }
    var t0 = moment();
    // HACK FOR LIZARD DEMO: SHOW "CURRENT" TIME
    // So, not actually UTC.
    t0.subtract('minute', moment().zone());
    t0 = t0.toDate().getTime();
    // /HACK
    var markings = [
        { color: '#d22', xaxis: { from: t0, to: t0 }, lineWidth: 2 }
    ];
    var view_state = get_view_state();
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
            zoomRange: [15 * MS_MINUTE, view_state.dt_end - view_state.dt_start],
            timezone: 'utc',
            min: moment(response.x_min).toDate().getTime(),
            max: moment(response.x_max).toDate().getTime()
        },
        grid: { hoverable: true, labelMargin: 15, markings: markings },
        pan: { interactive: true },
        zoom: { interactive: true }
    };
    if (isAppleMobile) {
        // enable touch
        defaultOpts.touch = { pan: 'x', scale: 'x', autoWidth: false, autoHeight: false };
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
              left: 0, bottom: 30, right: 0,
              height: 18,
              'text-align': 'center'
          })
          .html((response.x_label) ? response.x_label : 'Tijd');
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
    var $c_bwd = $('<button title="' + gettext("Slide left") + '" class="btn" type="button"><i class="icon-backward"></i></button>');
    $control_row.append($c_bwd);

    var $center = $('<span style="position: absolute; left: 50%; width:40px; margin-left:-20px;">');
    $control_row.append($center);

    /*
      var $c_reset = $('<button title="' + gettext("Reset zoom") + '" class="btn" type="button"><i class="icon-refresh"></i></button>');
      $center.append($c_reset);

      var $c_plus = $('<button title="' + gettext("Zoom in") + '" class="btn" type="button" style="margin-left:3px;"><i class="icon-zoom-in"></i></button>');
      $center.append($c_plus);

      var $c_min = $('<button title="' + gettext("Zoom uit") + '" class="btn" type="button" style="margin-left:3px;"><i class="icon-zoom-out"></i></button>');
      $center.append($c_min);
    */

    var $c_fwd = $('<button title="' + gettext("Slide right") + '" class="btn pull-right" type="button"><i class="icon-forward"></i></button>');
    $control_row.append($c_fwd);

    $container.append($control_row);

    // initial plot
    var plot = $.plot($graph, data, defaultOpts);
    bindPanZoomEvents($graph);
    bindFullscreenClick($container);

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

    if (!isAppleMobile) {

        $graph.bind("plothover", function (event, pos, item) {
            if (item) {
                $("#graphtooltip").remove();
                showGraphTooltip(item.pageX, item.pageY, item.datapoint);
            } else {
                $("#graphtooltip").remove();
            }
        });
    }

    /*
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
    */
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
    var view_state = get_view_state();
    view_state = to_date_strings(view_state);
    var offset = $('.popup-date-range').attr('data-offset');
    dt_start = moment.utc(xmin).format('YYYY-MM-DDTHH:mm:ss') + offset;
    dt_end = moment.utc(xmax).format('YYYY-MM-DDTHH:mm:ss') + offset;
    if (dt_start < view_state.dt_start) {
        xmin = moment(view_state.dt_start);
    }
    if (dt_end > view_state.dt_end) {
        xmax = moment(view_state.dt_end);
    }

    flot_x_global_min = xmin;
    flot_x_global_max = xmax;
    $('.flot-graph-canvas').each(function () {
        var otherPlot = $(this).data('plot');
        if (otherPlot && plot !== otherPlot) {
            var otherXAxisOptions = otherPlot.getAxes().xaxis.options;
            otherXAxisOptions.min = xmin;
            otherXAxisOptions.max = xmax;
            if ($(this).is(':visible')) {
                otherPlot.setupGrid();
                otherPlot.draw();
            }
        }
    });
    // Reload data if needed, followed by another draw.
    if (flot_reload_timeout) {
        // clear old timeout first
        clearTimeout(flot_reload_timeout);
    }
    flot_reload_timeout = setTimeout(reloadZoomableGraphs, 1000);
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

if (!$.fn.insertAt) {
    $.fn.insertAt = function(index, $parent) {
        return this.each(function() {
            if (index === 0) {
                $parent.prepend(this);
            } else {
                $parent.children().eq(index - 1).after(this);
            }
        });
    };
}

function bindFullscreenClick($container) {

    var $graph = $container.find('.flot-graph-canvas');
    $graph.on('dblclick doubletap', function (event) {
        if ($container.data('is-fullscreen') === true) {
            // already fullscreen, close it again
            $container.parent('.huge-graph-dialog').dialog('close');
        }
        else {
            var $dialog = $('<div class="huge-graph-dialog"></div>');
            $('body').append($dialog);

            var $origParent = $container.parent();
            var origHeight = $container.css('height');
            var origIndex = $container.index();
            $container.css('height', '100%');

            var onClose = function (event, ui) {
                if ($origParent.length > 0) {
                    $container.insertAt(origIndex, $origParent);
                    $container.css('height', origHeight);
                }
                $container.data('is-fullscreen', false);
                $dialog.dialog('destroy');
                $dialog.remove();
            };

            var options = {
                autoOpen: false,
                title: '',
                width: $(window).width() * 0.95,
                height: $(window).height() * 0.95,
                zIndex: 10100,
                draggable: false,
                resizable: false,
                close: onClose
            };

            $dialog.dialog(options);
            $dialog.append($container);
            $container.data('is-fullscreen', true);
            $dialog.dialog('open');
        }
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

function set_view_state(params, callback) {
    $.extend(_view_state, params);
    flot_x_global_min = undefined;
    flot_x_global_max = undefined;
    save_view_state_to_server(callback);
}

function save_view_state_to_server(callback) {
    // update the session on the server side
    var view_state = _view_state;
    lizard_api_put({
        url: '/map/view_state_service/', // TODO: url from data attribute.
        data: view_state,
        success: function (data) {
            callback();
        }
    }, true);
}

function setup_view_state() {
    if ($('.popup-date-range').exists()) {
        var picker = $('.popup-date-range').data('daterangepicker');
        picker.setRange(_view_state.range_type, _view_state.dt_start, _view_state.dt_end);
        _view_state.range_type = picker.rangeType;
        _view_state.dt_start = moment(picker.startDate);
        _view_state.dt_end = moment(picker.endDate);
    }
    reloadGraphs();
}

function setup_daterangepicker() {
    if ($('.popup-date-range').exists()) {
	var ranges = {};
	ranges[gettext('Last day')] = [moment.utc().subtract('days', 1),
				       moment.utc(), 'today'];
        ranges[gettext('Last 2 days')] = [moment.utc().subtract('days', 2),
					  moment.utc(), '2_day'];
        ranges[gettext('Last week')] = [moment.utc().subtract('weeks', 1),
					    moment.utc().add('days', 1),
					    'week_plus_one'];
        ranges[gettext('Last month')] = [moment.utc().subtract('months', 1),
					 moment.utc(), 'month'];
        ranges[gettext('Last half year')] = [moment.utc().subtract('months', 6),
					 moment.utc(), 'halfyear'];
        ranges[gettext('Last year')] = [moment.utc().subtract('years', 1),
					moment.utc(), 'year'];

        var picker = $('.popup-date-range').daterangepicker({
            opens: 'left',
            format: 'DD-MM-YYYY',
            locale: {
                applyLabel:gettext('Apply'),
                cancelLabel:gettext('Cancel'),
                customRangeLabel:gettext('Manual input'),
                daysOfWeek:[gettext('Sun'), gettext('Mon'), gettext('Tue'),
			    gettext('Wed'), gettext('Thu'), gettext('Fri'),
			    gettext('Sat')],
                monthNames:[gettext('January'), gettext('February'), gettext('March'),
			    gettext('April'), gettext('May'), gettext('June'), gettext('July'),
			    gettext('August'), gettext('September'), gettext('October'),
			    gettext('November'), gettext('December')],
                firstDay:0
            },
            ranges: ranges
        },
                                                            function (range_type, dt_start, dt_end) {
                                                                set_view_state({range_type: range_type, dt_start: dt_start, dt_end: dt_end},
                                                                               function () {
                                                                                   // hack to support reloading after changing the date (collage page)
                                                                                   if ($('.popup-date-range').hasClass('reload-after-action')) {
                                                                                       setTimeout(window.location.reload, 1337);
                                                                                   }
                                                                                   else {
                                                                                       reloadGraphs(undefined, undefined, true);
                                                                                       refreshWmsLayers();
                                                                                   }
                                                                               });
                                                            });
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
                        var $link = $('<a title="' + gettext("Add to selection") + '" data-target-id="#edit-collage" class="ss_sprite ss_star collage-add" />')
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


    if ($element.exists()) {
        var template = '' +
              '<div class="location-list">' +
              '<form class="form-search">' +
              '<legend>' + gettext("Search location") + '</legend>' +
              '<input type="text" class="search-query" placeholder="' + gettext("Type at least three characters ...") + '" style="width:300px"/>' +
              '<button type="submit" class="btn" style="margin-left:10px">' + gettext("Zoek") + '</button>' +
              '</form>' +
              '<div class="results" />' +
              '</div>';
        var $container = $(template);
        var $form = $container.find('.form-search');
        var $input = $container.find('input');
        var $button = $container.find('button');
        var $results = $container.find('.results');

        $element.on('click', show);
    }
}

function setup_location_search () {
    function requestSuccess (data) {

	// Define Tab
	var iconClass = 'icon-search';
	var tabId = 'box-awesome-content-search';
	var tabClass = 'box-awesome-tab-search';

	var $ul = $('#box-awesome-tabs > ul');
	var $content = $('#box-awesome-tabs > .tab-content');


	var $newLi = $('<li>').addClass(tabClass);
	var $link = $('<a data-toggle="tab">').attr('href', '#' + tabId);
	var $icon = $('<i>').addClass(iconClass);


	var $tabContent = $('<div>')
	      .addClass('tab-pane sidebar-inner')
	      .attr('id', tabId);

	// Remove old tab

	$ul.find('.' + tabClass).remove();
	$content.find('#' + tabId).remove();

	// Fill tab

	var $closeBtn = $('<button type="button" class="close">&times;</button>')
	      .on('click', function (event) {
		  $newLi.remove();
		  $tabContent.remove();
		  $ul.find('a:last').trigger('click');
	      });

	var $closeBtnPane = $('<div style="height: 20px;">')
	      .append($closeBtn)
	      .appendTo($tabContent);

        var items = [];
        $.each(data, function(key, val) {
            bb = val.boundingbox;
            items.push("<li><a href='#' onclick='chooseAddr(" +
		       bb +
		       ");return false;'>" + val.display_name + '</a></li>');
        });

	var $contentPane = $('<div>');
        if (items.length !== 0) {
            $('<ul/>', {
                html: items.join('')
            }).appendTo($contentPane);
        } else {
            $('<p/>', { html: gettext("Nothing found.") }).appendTo($contentPane);
        }


	$contentPane.appendTo($tabContent);

	$link.append($icon);
	$newLi.append($link);

	$ul.append($newLi);
	$content.append($tabContent);

	$link.tab('show');
    }

    function submitForm (event) {
	event.preventDefault();
	var inp = $('#box-awesome-search input').val();

	// This is a cross-site request, IE9's handling of those
	// is slightly different than other browsers', and JQuery
	// doesn't support IE9's version. Therefore we need to
	// make it an explicit JSONP request. Nominatim supports
	// JSONP through the 'json_callback' GET parameter.
	$.ajax(
	    '//nominatim.openstreetmap.org/search', {
		data: {
		    q: inp,
		    format: "json",
                    limit: 5
		},
		dataType: 'jsonp',
		jsonp: 'json_callback',
		success: requestSuccess});
    }

    $('#box-awesome-search-form').on('submit', submitForm);
}

/* Move the map to the given address. */
function chooseAddr(lat1, lat2, lng1, lng2) {
    var bounds = new OpenLayers.Bounds();
    bounds.extend(new OpenLayers.LonLat(lng1, lat1));
    bounds.extend(new OpenLayers.LonLat(lng2,  lat2));

    bounds.transform('EPSG:4326', map.getProjection());
    map.zoomToExtent(bounds);
}

function setUpCloseSearch () {
    $('#box-awesome-results button').on('click', function (event) {
	$('#box-awesome-results div').empty();
	$('#box-awesome-results').hide();
    });
}

function setUpElevationProfileForMap() {
    bindFullscreenClick($('#elevation-profile-content'));
}

function setUpAppTab(){
    // Select application tab when the request is not on '/'.
    // Normally the user is in an app when the a non '/' path is used.

    // console.log('apptab');
    if (window.location.pathname !== '/'){
	$('#box-awesome-app-tab').tab('show');

	// Have a back button.
	var $button = $(
	    '<button type="button" class="icon-chevron-left close"></button>');
	$('#apps-back-button').html($button);
	$button.on('click', function(event) {
	    window.history.back();
	});
    }
}

function setUpBootstrapTour() {
    var tour_type = $('#lizard-map-wms').data('bootstrap-tour');

    if (tour_type) {
	var tour = setUpTour();
	$('#action-bootstrap-tour').click(function (){
	    tour.restart();
	});
    }
}

function setUpTour(){
    var tour = new Tour({
	template: "<div class='popover tour'><div class='arrow arrow-info'></div><h3 class='popover-title popover-title-info'></h3><div class='popover-content'></div><div class='popover-navigation'><button class='btn btn-default' data-role='prev'>« </button><span data-role='separator'>|</span><button class='btn btn-default' data-role='next'>»</button><button class='btn btn-default' data-role='end'>Stop</button></div></nav></div>"
    });

    var first_step_content = gettext("This information portal works in current browsers: IE9 or higher, Firefox and Chrome.");
    var disclaimer = $('#lizard-map-wms').data('disclaimer-text');
    if (disclaimer) {
        first_step_content = first_step_content + '<br><br>' + disclaimer;
    }
    tour.addSteps([
	{
	    element: "#box-awesome-tabs", // string (jQuery selector) - html element next to which the step popover should be shown
	    title: gettext("Welcome to Lizard"), // string - title of the popover
	    content: first_step_content // string - content of the popover
	},
	{
	    element: "#box-awesome-search button", // string (jQuery selector) - html element next to which the step popover should be shown
	    title: gettext("Search location"), // string - title of the popover
	    content: gettext("Enter the search term and click the magnifying glass."), // string - content of the popover
	    placement: "bottom"
	},
	{
	    element: "#box-awesome-content-themes",
	    title: gettext("Topic maps"),
	    content: gettext("These are the maps sorted for you per topic.")
	},
	{
	    element: "#box-awesome-content-themes",
	    title: gettext("The map"),
	    content: gettext("Click on the map for more information about the object. Does this information contain a chart, double-click to see the chart in full screen.")
	},
	{
	    element: "#box-awesome-tabs ul.nav li:nth-child(2)",
	    title: gettext("Legend"),
	    content: gettext("Here is the legend"),
	    placement: "bottom"
	},
	{
	    element: "#box-awesome-tabs ul.nav li:nth-child(3)",
	    title: gettext("Elevation profile"),
	    content: gettext("Here is the elevation profile."),
	    placement: "bottom"

	},
	{
	    element: "#box-awesome-tabs ul.nav li:nth-child(4)",
	    title: gettext("Apps"),
	    content: gettext("Here are the specific apps."),
	    placement: "bottom"

	},
	{
	    element: "#action-base-layers",
	    title: gettext("Backgroud maps"),
	    content: gettext("Select here a different background map."),
	    placement: "bottom"
	},
	{
	    element: "#action-layers",
	    title: gettext("Maps"),
	    content: gettext("Select a specific map of the topic map to make them (in) visible."),
	    placement: "bottom"
	},
	{
	    element: "#action-calendar",
	    title: gettext("Calendar"),
	    content: gettext("Change in the date selection for date dependent information."),
	    placement: "bottom"
	},
	{
	    element: "#action-bootstrap-tour",
	    title: gettext("Info tour"),
	    content: gettext("Click here to start the tour again. Click stop to end the tour."),
	    placement: "bottom"
	},

    ]);
    tour.init();
    tour.start();
    return tour;
}


function setUpWMSFilter(){
    var $element = $('#action-wms-filter');

    if ($element == []){
	// Return when the element is empty.
	return;
    }

    var dropdownTemplate = _.template('' +
		                      '<li role="presentation">' +
                                      '<a href="#" ' +
		                      'class="wms-filter" '+
				      'id="<%= id %>" >' +
                                      '<% if (checked){ %> <i class="icon-">&#xf00c;</i> <% }%> ' +
   			              '<%= name %> ' +
                                      '</a>' +
                                      '</li>');


    $element.find('.dropdown-toggle').attr('data-toggle', 'dropdown');
    $element.addClass('dropdown');

    // Build the dropdown scaffold
    var filterUl = $('<ul>').attr('id', 'action-wms-filter-ul'
				 ).attr('class', 'dropdown-menu'
				       ).attr('role', 'menu');

    $element.append(filterUl);
    $filterElement = $('#action-wms-filter-ul');

    var filterItems = $('#lizard-map-wms').data('wms-filter');
    if (filterItems) {
        for(var i=0; i<filterItems.length; i++){
            var filterItem = filterItems[i];
            var checked;
            if (filterItem['default'] === true) {
                checked = true;
                // Add the cql_filter for the default filter
                $('#lizard-map-wms').data('wms-cql_filters', filterItem.cql_filter);
            } else {
                checked = false;
            }
            var id = 'wms-filter-id-' + i;
            var template = 	dropdownTemplate(
                {'name': filterItem.name,
                 'checked': checked,
                 'id': id
                });

            $filterElement.append(template);
            // Set the cql data on the newly created element.
            $('#' + id).data('cql-filter', filterItem.cql_filter);

        }
    }

    $filterElement.find('.wms-filter').click(function(e){
	// Remove old checks
	$(e.target).parents('li').find('.wms-filter i').remove();

	// Get the cql filter
	var cql_filter = $(e.target).data('cql-filter');
	// Handle a click on the check mark as well.
	if (typeof(cql_filter) === "undefined"){
	    cql_filter = $(e.currentTarget).data('cql-filter');
	    $(e.currentTarget).prepend('<i class="icon-">&#xf00c;</i>');
	} else {
	    // Add the new check
	    $(e.target).prepend('<i class="icon-">&#xf00c;</i>');
	}
	// Set the new filter
	$('#lizard-map-wms').data('wms-cql_filters', cql_filter);
	refreshWmsLayers();
	e.stopPropagation();
    });


}

$(document).ready(function () {
    setUpWMSFilter(); // Before WMS is initialized. This filters wms layers
    setup_daterangepicker();
    setup_view_state();
    setup_movable_dialog();
    setup_location_list();
    setup_location_search();
    setUpAppTab();
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
    setUpCloseSearch();
    setUpElevationProfileForMap();
    setUpBootstrapTour();
    $('.workspace').workspaceInteraction();

    if ($('#map').exists()) {
        setUpMap();
        setUpMultipleSelection();
    }


});
