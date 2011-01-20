// jslint configuration
/*jslint browser: true */
/*global $, jQuery, OpenLayers, window, map, updateLayer, fillSidebar,
setUpScreen, nothingFoundPopup, reloadGraphs, reloadMapActions,
setUpTransparencySlider, setUpAnimationSlider, setUpTooltips */


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

jQuery.fn.liveCheckboxes = function () {
    return this.each(function () {
        var $workspace;
        $workspace = $(this);
        $workspace.find(".workspace-item-checkbox").live('click', function () {
            var url = $workspace.attr("data-url-lizard-map-workspace-item-edit");
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
    });
};



/* Shows an "jquery tools overlay" popup, data must have the following properties:
data.html

Previously it also needed:
data.id
data.x
data.y
data.big
But those aren't used anymore.
*/

function show_popup(data, map) {
    if (data !== null) {
        if (data.html !== "" && data.html !== undefined) {
            var overlay;
            $('#graph-popup-content').html(data.html);
            overlay = $('#graph-popup').overlay();
            overlay.load();
            reloadGraphs();
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
                                     new OpenLayers.Size(300, 35),
                                     content,
                                     false);
        popup.maxSize = new OpenLayers.Size(300, 35);
        popup.border = "1px solid black";
        popup.autoSize = true;
        map.addPopup(popup);
    }
}


jQuery.fn.collagePopup = function () {
    var url, collage_id;
    url = $(this).parent().attr("data-url-lizard-map-collage-popup");
    collage_id = $(this).attr("data-collage-id");
    $.getJSON(
        url,
        { collage_id: collage_id },
        function (data) {
            show_popup(data, map);
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
                        // very strange... $workspace becomes the
                        // <ul> element, using workspaceItems...
                        // TODO: empty temp workspace
                        workspaceItems.parent().parent().updateWorkspace();
                        $(".workspace-empty-temp").click(); // "click" the empty temp workspace
                    }
                );
            }
        });
        // Make collage clickable. (TODO: should be collage-popup)
        $(".collage", $workspace).live('click',
                                       $(this).collagePopup);
        // Snippets. Using sortable instead of draggable because
        // Draggable applies to li and sortable applies to ul element
        snippet_list = $workspace.find("ul.snippet-list");
        snippet_list.sortable({
            helper: 'clone',
            items: 'li.snippet'
        });
        // Make snippets clickable... for eternity.
        snippet_list.find("li.snippet").live('click', function (event) {
            var url, snippet_id;
            url = $workspace.attr("data-url-lizard-map-snippet-popup");
            snippet_id = $(this).attr("data-object-id");
            $.getJSON(
                url,
                { snippet_id: snippet_id },
                function (data) {
                    show_popup(data, map);
                }
            );
            //snippet(snippet_id, map); // attention: from krw_waternet.js
        });

        // Make the trash working.
        $workspace.workspaceTrashBox();
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
        // reload map layers
        updateLayer(workspace_id); // from lizardgis
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
                fillSidebar();
                $(".map-actions").html(
                    $('.map-actions', $holder).html());
                setUpAnimationSlider();
                setUpTransparencySlider();
                setUpTooltips();
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

/* Make a workspace trashbox

accepts workspace_item classes

globally defined requirements:
.data-url-lizard-map-workspace-item-delete

css class drophover

requirements:
workspace_trash class inside workspace

*/

jQuery.fn.workspaceTrashBox = function () {
    return this.each(function () {
        var $workspace, workspace_trash, url_workspace_item, url_snippet;
        $workspace = $(this);
        workspace_trash = $workspace.find(".workspace-trash");
        // delete workspace items
        url_workspace_item = $workspace.attr("data-url-lizard-map-workspace-item-delete");
        url_snippet = $workspace.attr("data-url-lizard-map-snippet-delete");
        workspace_trash.droppable({
            accept: workspaceItemOrSnippet,
            hoverClass: 'drophover',
            activeClass: 'dropactive',
            drop: function (event, ui) {
                var object_id, url;
                object_id = ui.draggable.attr("data-object-id");
                ui.draggable.remove();  // for visual snappyness
                if (ui.draggable.is(".workspace-item")) {
                    url = url_workspace_item;
                } else {
                    //snippet
                    url = url_snippet;
                }
                $.ajax({
                    url: url,
                    data: { object_id: object_id },
                    success: function () {
                        // TODO: reload workspace items: looping error
                        //$(this).find(".workspace_items").load("./ .workspace_item");
                        //$("ul.workspace_items").load("./ .workspace_item");
                        //$("ul.workspace_items").sortable("destroy");
                        //$("ul.workspace_items").draggable("destroy");
                        location.reload();
                    },
                    type: "POST",
                    async: false
                });
            }
        });
    });
};

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
