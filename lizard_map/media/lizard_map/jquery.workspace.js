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
jQuery.fn.liveCheckboxes = function() {
    return this.each(function(){
        $workspace = $(this);
        $workspace.find(".workspace_item_checkbox").live('click', function() {
            var url = $workspace.attr("data-url-lizard-map-workspace-item-edit");
            $.ajax({
                url: url,
                data: { workspace_item_id: this.id, visible: this.checked },
                success: function(workspace_id) {
                    $workspace.updateWorkspace();
                },
                type: "POST",
                async: false
            });
        });
    });
};

/* Make workspaces sortable and droppable

Needed: data attributes on the <div class="workspace">:

.data.url-lizard-map-workspace-item-reorder
.data-url-lizard-map-workspace-item-add

matching objects require (needs cleanup):
this.attr("data-workspace_id");
<ul> at depth 2

TODO: use jquery live to bind all future workspaces?

*/
jQuery.fn.workspaceInteraction = function() {
    return this.each(function(){
        // Make the items in a workspace sortable.
        $workspace = $(this);
        var workspace_id = $workspace.attr("data-workspace_id");
        var workspaceItems = $workspace.find("ul.workspace_items");
        workspaceItems.sortable({
            update: function (event, ui) {
                // very strange... $workspace becomes the <ul> element
                // (which is workspaceItems)...  using workspaceItems
                var url = $workspace.attr("data-url-lizard-map-workspace-item-reorder");
                var order = workspaceItems.sortable("serialize");
                $.post(url + "?workspace_id="+workspace_id,
                       order,
                       function(workspace_id) {
                           workspaceItems.parent().parent().updateWorkspace();
                       }
                      );
            },
            helper: 'clone',
            connectWith: '.workspace_items',
            cursor: 'move',
            revert: 'true',
            placeholder: 'ui-sortable-placeholder'
        });
        // Make the workspace droppable, only accept items with the class
        // '.workspace-acceptable'.
        workspaceItems.droppable({
            accept: '.workspace-acceptable',
            hoverClass: 'drophover',
            drop: function(event, ui) {
                // Fade out draggable item.
                ui.helper.fadeOut();
                // Get layer_method and parameters from url.
                var name = ui.draggable.attr("data-name");
                // ^^^ TODO: this attr name might be dangerous.
                var layer_method = ui.draggable.attr("data-layer_method");
                var layer_method_json = ui.draggable.attr("data-layer_method_json");
                var url = $workspace.attr("data-url-lizard-map-workspace-item-add");
                // Make workspace item out of it.
                $.post(url,
                       {workspace_id: workspace_id,
                        name: name,
                        layer_method: layer_method,
                        layer_method_json: layer_method_json
                       },
                       function(workspace_id) {
                           // very strange... $workspace becomes the
                           // <ul> element, using workspaceItems...
                           workspaceItems.parent().parent().updateWorkspace();
                       }
                      );
            }
        });
        // Snippets. Using sortable instead of draggable because
        // draggable applies to li and sortable applies to ul element
        snippet_list = $workspace.find("ul.snippet_list");
        snippet_list.sortable({
            helper: 'clone'
        });
        // Make the trash working
        $workspace.workspaceTrashBox();
        // Make checkboxes work
        $workspace.liveCheckboxes();
    });
}


// Update workspace boxes and their visible layers.
jQuery.fn.updateWorkspace = function() {
    return this.each(function(){
        var $this = $(this);
        var workspace_id = $this.attr("data-workspace_id");
        // reload map layers
        updateLayer(workspace_id); // from lizardgis
        // reload workspace items: TODO: works only with a single workspace
        // item.
        $(this).find(".workspace_items").load("./ .workspace_item",
                                             fillSidebar);
    });
};

/* React on click "add snippet"

requires

.data-url-lizard-map-snippet-add

*/
    jQuery.fn.snippetInteraction = function() {
        return this.each(function() {
            $(this).click(function(event) {
                event.preventDefault();
                console.log("add-snippet");
                var workspace_id = $(this).attr("data-workspace-id");
                var url = $("#workspace_" + workspace_id).attr("data-url-lizard-map-snippet-add");
                var workspace_item_id = $(this).attr("data-workspace-item-id");
                var workspace_item_location_identifier = $(this).attr("data-item-identifier");
                var workspace_item_location_shortname = $(this).attr("data-item-shortname");
                var workspace_item_location_name = $(this).attr("data-item-name");
                if (url !== undefined) {
                    $.post(
                        url,
                        {
                            workspace_item_id: workspace_item_id,
                            workspace_item_location_identifier: workspace_item_location_identifier,
                            workspace_item_location_shortname: workspace_item_location_shortname,
                            workspace_item_location_name: workspace_item_location_name
                        },
                        function() {
                            // refresh collage
                            $(".workspace").find(".snippet_list").load("./ .snippet");
                        });
                }
            });
        });
    }


    function workspaceItemOrSnippet(object)
    {
        if ($(object).is(".workspace_item")) {return true;}
        if ($(object).is(".snippet")) {return true;}
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
  jQuery.fn.workspaceTrashBox = function() {
      return this.each(function(){
          var $workspace = $(this);
          var $workspace_trash = $workspace.find(".workspace_trash");
          // delete workspace items
          var url_workspace_item = $workspace.attr("data-url-lizard-map-workspace-item-delete");
          var url_snippet = $workspace.attr("data-url-lizard-map-snippet-delete");
          $workspace_trash.droppable({
              accept: workspaceItemOrSnippet,
              hoverClass: 'drophover',
              drop: function(event, ui) {
                  var object_id = ui.draggable.attr("data-object_id");
                  ui.draggable.remove();  // for visual snappyness
                  if (ui.draggable.is(".workspace_item")) {
                      var url = url_workspace_item;
                  } else {
                      //snippet
                      var url = url_snippet;
                  }
                  $.ajax({
                      url: url,
                      data: { object_id: object_id },
                      success: function() {
                          // reload workspace items: looping error
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
  }

  /* Load a lizard-map page by only replacing necessary parts

Replaces:
- breadcrumbs
- app part

Setup the js of page
Load workspaces

Then change the url (???)

*/
  jQuery.fn.lizardMapLink = function() {
      $(this).click(function(event) {
          event.preventDefault();
          var url = event.currentTarget;
          $.get(
              url,
              function(responseText, textStatus, xmlHttpRequest) {
                  //alert($(responseText).find("div#head-extras").html());
                  // replace sidebar
                  $("#sidebar").html($(responseText).find("#sidebar").html());
                  setUpScreen();
                  $(".workspace").workspaceInteraction();
                  //$(".workspace").updateWorkspaceBox();
                  // $("#head-extras").html($(responseText).find("#head-extras").html());

                  var headExtras = $(responseText).find("div#head-extras").html();
                  $("div#head-extras").html(headExtras);

                  // replace breadcrumbs
                  $("#breadcrumbs").html($(responseText).find("#breadcrumbs").html());
                  $("a.lizard-map-link").lizardMapLink(); //affects breadcrumbs AND sidebar

                  // replace title... where is it???
                  //console.debug($(responseText).find("title"));
                  //$("title").replaceWith($(responseText).find("title"));

              }
          );

          // probeersel, je kunt niet het voorste gedeelte aanpassen
          window.location.hash = event.currentTarget;
      });
  }
