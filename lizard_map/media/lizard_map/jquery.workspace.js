/*
Workspace plugin

Globally defined requirements
*/

/*
updates the workspace box using an ajax call
globally defined requirements:

$("a.url-lizard-map-workspace-items").attr("href");

requirements:

matched items must have <ul> inside with class workspace_items
matched items must have attr("workspace_id")
*/
jQuery.fn.updateWorkspaceBox = function() {
  return this.each(function(){
      $workspace = $(this);
      var url = $("a.url-lizard-map-workspace-items").attr("href");
      var workspace_id = $workspace.attr("workspace_id");
      workspace_items = $workspace.find("ul.workspace_items");
      $.ajax({
          url: url,
          data: {workspace_id: workspace_id},
          success: function(workspace_items_li) {
              // prevent looping error: test destroying object before overwrite: does not work
              //workspace_items.sortable("destroy"); 
              //workspace_items.droppable("destroy");
              //workspace_items.find("li.workspace_item").remove();
              //console.debug($workspace);
              // replace list items with new list items
              //alert(workspace_items_li);
              workspace_items.html(workspace_items_li);
              workspace_items.bindCheckboxes();
              //$workspace.workspaceInteraction();
              stretchOneSidebarBox(); // from lizard_ui
          },
          type: "GET",
          async: false
      });
      
  });
};

/* Bind checkboxes */
  jQuery.fn.bindCheckboxes = function() {
      return this.each(function(){
          $workspace = $(this);
          $workspace.find(".workspace_item_checkbox").bind('click', function() {
              var url = $("a.url-lizard-map-workspace-item-edit").attr("href");
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

globally defined requirements:
$("a.url-lizard-map-workspace-item-reorder").attr("href");
$("a.url-lizard-map-workspace-item-add").attr("href");

matching objects require (needs cleanup):
this.attr("workspace_id");
$("#workspace_"+workspace_id+".workspace_items");

*/
jQuery.fn.workspaceInteraction = function() {
    return this.each(function(){
        // Make the items in a workspace sortable.
        $workspace = $(this);
        var workspace_id = $workspace.attr("workspace_id");
        workspaceItems = $workspace.find("ul.workspace_items");
        workspaceItems.sortable({
            update: function (event, ui) {
                var url = $("a.url-lizard-map-workspace-item-reorder").attr("href");
                var order = $("#workspace_"+workspace_id+".workspace_items"
                    ).sortable("serialize");
                $.post(url + "?workspace_id="+workspace_id,
                       order,
                       function(workspace_id) {
                           // very strange... $workspace becomes the <ul> element...
                           $workspace.parent().parent().updateWorkspace();
                       }
                      );
            },
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
                name = ui.draggable.attr("name");
                // ^^^ TODO: this attr name might be dangerous.
                layer_method = ui.draggable.attr("layer_method");
                layer_method_json = ui.draggable.attr("layer_method_json");
                var url = $("a.url-lizard-map-workspace-item-add").attr("href");
                // Make workspace item out of it.
                $.post(url,
                       { workspace_id: workspace_id,
                         name: name,
                         layer_method: layer_method,
                         layer_method_json: layer_method_json
                       },
                       function(workspace_id) {
                           // very strange... $workspace becomes the <ul> element...
                           $workspace.parent().parent().updateWorkspace();
                       }
                      );
            }
        });
        // Make the trash working
        $workspace.workspaceTrashBox();
    });
}


// Update workspace boxes and their visible layers.
jQuery.fn.updateWorkspace = function() {
    return this.each(function(){
        var $this = $(this);
        var workspace_id = $this.attr("workspace_id");
        updateLayer(workspace_id); // from lizardgis
        $this.updateWorkspaceBox();
    });
};


/* Make a workspace trashbox 

accepts workspace_item classes

globally defined requirements:
$("a.url-lizard-map-workspace-item-delete").attr("href");

css class drophover

requirements:
workspace_trash class inside workspace

*/
  jQuery.fn.workspaceTrashBox = function() {
      return this.each(function(){
          var $workspace = $(this);
          var $workspace_trash = $workspace.find(".workspace_trash");
          var url = $("a.url-lizard-map-workspace-item-delete").attr("href");
          $workspace_trash.droppable({
              accept: '.workspace_item',
              hoverClass: 'drophover',
              drop: function(event, ui) {
                  workspace_item_id = ui.draggable.attr("value");
                  ui.draggable.remove();  // for visual snappyness
                  $.ajax({
                      url: url,
                      data: { workspace_item_id: workspace_item_id },
                      success: function(workspace_id) {
                          $workspace.updateWorkspace(); // vreemde looping bug
                          // location.reload();
                      },
                      type: "POST",
                      async: false
                  });
              }
          });
      });
  }
