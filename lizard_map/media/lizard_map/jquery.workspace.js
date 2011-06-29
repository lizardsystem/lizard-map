// jslint configuration
/*jslint browser: true */
/*jslint white: false */
// ^^^ Needed because jslint doesn't like
// this.getPanes().hide().eq(tabIndex).show();...

/*global $, jQuery, OpenLayers, window, map, fillSidebar,
setUpScreen, nothingFoundPopup, reloadGraphs,
reloadLocalizedGraphs, reloadMapActions,
setUpTransparencySlider, setUpAnimationSlider, setUpTooltips,
refreshLayers */


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
    return ($("#graph-popup-content div:first-child").length !== 0 &&
            $("#graph-popup-content div:first-child").data("is_collage_popup") &&
            $("#graph-popup").css("display") === "block");
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
                success: function (workspace_id) {
                    $workspace.updateWorkspace();
                },
                type: "POST",
                async: false
            });
        });
        $workspace.find(".snippet-checkbox").live('click', function () {
            var url, $list_item;
            url = $workspace.attr("data-url-lizard-map-snippet-edit");
            $list_item = $(this).closest('li');
            $list_item.addClass("waiting-lineitem");
            $.ajax({
                url: url,
                data: { snippet_id: this.id, visible: this.checked },
                success: function (snippet) {
                    $workspace.updateWorkspace();
                },
                type: "POST",
                async: false
            });
            // Reload the collage_popup if it is already visible
            if (isCollagePopupVisible()) {
                $(".collage").collagePopup();
            }
        });
    });
};


/* Shows an "jquery tools overlay" popup, data must have the following properties:
data.html

Uses customized "default" effect to make tabs work correctly. See
bottom of this file. It works, but it loads graphs 2 times in case of
tabs. Needs fixing.

Previously it also needed:
data.id
data.x
data.y
data.big
But those aren't used anymore.
*/

function show_popup(data) {
    var html, overlay, i;
    if (data !== null) {
        if (data.html && data.html.length !== 0) {
            // Generates pages with handlers. First only page 0 is visible.
            if (data.html.length === 1) {
                $("#graph-popup-content").html(data.html[0]);
            } else {
                // Build up html with tabs.
                html = '<ul class="tabs css-tabs">';
                for (i = 0; i < data.html.length; i += 1) {
                    html += '<li><a href="#">Resultaat ';
                    html += (i + 1) + '</a></li>';
                }
                html += '</ul><div class="popup-panes">';
                for (i = 0; i < data.html.length; i += 1) {
                    html += '<div class="pane"><div class="pane-content">';
                    html += data.html[i];
                    html += '</div></div>';
                }
                html += '</div>';

                $("#graph-popup-content").html(html);
                $(".tabs").tabs("div.popup-panes > div.pane",
                                {'effect': 'map_popup'});
            }
            overlay = $('#graph-popup').overlay();
            overlay.load();
            if (data.html.length === 1) {
                // The tabs don't do their reload magic.
                reloadGraphs();
            } else {
                // Re-reload the first one.
                reloadLocalizedGraphs(
                    $("div.popup-panes > div.pane")[0]);
            }
            $(".add-snippet").snippetInteraction();
        }
        else {
            nothingFoundPopup();
        }
    }
}


function hover_popup(data, map) {
    if (data.name !== "" &&
        data.name !== undefined) {
        var popup, content;
        content = '&nbsp;&nbsp;&nbsp;&nbsp;' + data.name +
            '&nbsp;&nbsp;&nbsp;&nbsp;';
        $("#hover-popup").remove(); // remove existing popup, if exists
        popup = new OpenLayers.Popup('hover-popup',
                                     new OpenLayers.LonLat(data.x, data.y),
                                     new OpenLayers.Size(300, 300),
                                     content,
                                     false);
        popup.maxSize = new OpenLayers.Size(300, 300);
        popup.border = "1px solid black";
        popup.autoSize = true;
        map.addPopup(popup);
    }
}


jQuery.fn.collagePopup = function () {
    var url, collage_id;
    url = $(this).closest("[data-url-lizard-map-collage-popup]").attr("data-url-lizard-map-collage-popup");
    collage_id = $(this).closest("[data-collage-id]").attr("data-collage-id");
    $.getJSON(
        url,
        { collage_id: collage_id },
        function (data) {
            show_popup(data);
            // Mark popup as being a collage popup
            $("#graph-popup-content div:first-child").data("is_collage_popup", true);

        }
    );

};


/* Make workspaces sortable and droppable

Needed: data attributes on the <div class="workspace">:

.data-url-lizard-map-workspace-item-reorder
.data-url-lizard-map-workspace-item-add

matching objects require (needs cleanup):
this.attr("data-workspace_id");
<ul> at depth 2

TODO: use jquery live to bind all future workspaces?

*/
jQuery.fn.workspaceInteraction = function () {
    return this.each(function () {
        var $workspace, workspace_id, workspaceItems, snippet_list;
        // Make the items in a workspace sortable.
        $workspace = $(this);
        workspace_id = $workspace.attr("data-workspace-id");
        workspaceItems = $workspace.find("ul.workspace-items");
        workspaceItems.sortable({
            update: function (event, ui) {
                var url, order;
                // very strange... $workspace becomes the <ul> element
                // (which is workspaceItems)...  using workspaceItems
                url = $workspace.attr("data-url-lizard-map-workspace-item-reorder");
                order = workspaceItems.sortable("serialize");
                $.post(
                    url + "?workspace_id=" + workspace_id,
                    order,
                    function (workspace_id) {
                        workspaceItems.parent().parent().updateWorkspace();
                    }
                );
            },
            helper: 'clone',
            connectWith: '.workspace-items',
            cursor: 'move',
            revert: 'true',
            placeholder: 'ui-sortable-placeholder',
            items: 'li.workspace-item'
        });
        // Make the workspace droppable, only accept items with the class
        // '.workspace-acceptable'.
        // This is not needed anymore, because you can click the (+).
        workspaceItems.droppable({
            accept: '.workspace-acceptable',
            hoverClass: 'drophover',
            activeClass: 'dropactive',
            drop: function (event, ui) {
                var name, adapter_class, adapter_layer_json, url;
                // Fade out draggable item.
                ui.helper.fadeOut();
                // Get layer_method and parameters from url.
                name = ui.draggable.attr("data-name");
                // ^^^ TODO: this attr name might be dangerous.
                adapter_class = ui.draggable.attr("data-adapter-class");
                adapter_layer_json = ui.draggable.attr("data-adapter-layer-json");
                url = $workspace.attr("data-url-lizard-map-workspace-item-add");
                // Make workspace item out of it.
                $.post(
                    url,
                    {workspace_id: workspace_id,
                     name: name,
                     adapter_class: adapter_class,
                     adapter_layer_json: adapter_layer_json
                    },
                    function (workspace_id) {
                        // "click" the empty temp workspace. To be removed.
                        $(".workspace-empty-temp").click();
                        // very strange... $workspace becomes the
                        // <ul> element, using workspaceItems...
                        // TODO: empty temp workspace
                        workspaceItems.parent().parent().updateWorkspace();
                    }
                );
            }
        });
        // Make collage clickable. (DONE: should be collage-popup)
        $(".collage-popup", $workspace).live('click',
                                       $(".collage").collagePopup);
        // Make checkboxes work.
        $workspace.liveCheckboxes();
        // Initialize the graph popup.
        $('#graph-popup').overlay({});
    });
};


// Update workspace boxes and their visible layers.
jQuery.fn.updateWorkspace = function () {
    return this.each(function () {
        var $workspace, workspace_id, $holder;
        $workspace = $(this);
        workspace_id = $workspace.attr("data-workspace-id");
        // reload workspace items: TODO: works only with a single workspace
        // item.
        $holder = $('<div/>');
        // Holder trick for replacing several items with just one server call:
        // see http://tinyurl.com/32xacr4 .
        $holder.load(
            './ #page',
            function () {
                $(".workspace-items", $workspace).html(
                    $('.workspace-items', $holder).html());
                $(".snippet-list", $workspace).html(
                    $('.snippet-list', $holder).html());
                fillSidebar();
                $(".map-actions").html(
                    $('.map-actions', $holder).html());
                $("#lizard-map-wms").html(
                    $('#lizard-map-wms', $holder).html());
                $("#collage").html(
                    $('#collage', $holder).html());
                reloadGraphs();
                // reload map layers
                if ($("#map").length > 0) {
                    refreshLayers(); // from lizard_wms.js
                }
                // Is this enough? See also refreshMapActionsDivs in lizard_map
                setUpAnimationSlider();
                setUpTransparencySlider();
                setUpTooltips();
                // Enable sorting. Some functions
                // (setUpAddWorkspaceItem) turns sorting off.
                $(".workspace ul.workspace-items").sortable("enable");
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


$(document).ready(function () {
    // Change "default" effect: reload graphs to fix layout.
    $.tools.tabs.addEffect(
        "map_popup",
        function (tabIndex, done) {
            // hide all panes and show the one that is clicked.
	    this.getPanes().hide().eq(tabIndex).show();
            done.call();
            if ($('#graph-popup').is(":visible")) {
                // Don't reload the popup graph if the overlay isn't
                // initialized yet.  There's no width then :-)
                // It *does* reload twice when an overlay is already
                // open, but we'll accept that for now.
                reloadLocalizedGraphs(this.getPanes()[tabIndex]);
            }
        });
});
