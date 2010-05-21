demo_map_click_handler = function(x, y, map) {

    var show_popup = function(data) {
        popup = new OpenLayers.Popup("some_id",
                                     new OpenLayers.LonLat(x,y),
                                     new OpenLayers.Size(200,200),
                                     data,
                                     true);
        popup.panMapIfOutOfView = true;
        map.addPopup(popup);
    };

    var msg = ("You clicked near " + x + " N, " +
               + y + " E");
    show_popup(msg);

    // $.get("/map/workspace/2/clickinfo/", { x: x, y: y },
    //       show_popup
    //      );
};

/* Workspace functions */
// Bind checkboxes of workspace_items to an action.
bindCheckboxes = function() {
  $(".workspace_item_checkbox").bind('click', function() {
    var url = $("a.url-lizard-map-workspace-item-edit").attr("href");
    $.ajax({
      url: url,
      data: { workspace_item_id: this.id, visible: this.checked },
      success: function(workspace_id) {updateWorkspace(workspace_id)},
      type: "POST",
      async: false
    });
  });
};

// Make workspace sortable
addWorkspaceSortableDroppable = function() {

  // Make the items in a workspace sortable.
  $("ul.workspace_items").sortable({
    update: function() {
      var workspace_id = $(this).attr("workspace_id");
      var url = $("a.url-lizard-map-workspace-item-reorder").attr("href");
      var order = $("#workspace_"+workspace_id+".workspace_items"
                   ).sortable("serialize");
      $.post(url + "?workspace_id="+workspace_id,
             order,
             updateWorkspace(workspace_id)
            );
    },
    connectWith: '.workspace_items',
    cursor: 'move',
    revert: 'true',
    placeholder: 'ui-sortable-placeholder'
  });
  // Make the workspace droppable, only accept items with the class
  // '.workspace-acceptable'.
  $("ul.workspace_items").droppable({
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
      var workspace_id = $(this).attr("workspace_id");
      // Make workspace item out of it.
      $.post(url,
             { workspace_id: workspace_id,
               name: name,
               layer_method: layer_method,
               layer_method_json: layer_method_json
             },
             updateWorkspace(workspace_id)
            );
    }
  });
}

// Update workspace sidebarbox.
// deze zorgt soms voor een looping foutmelding
updateWorkspaceBox = function(workspace_id) {
  var url = $("a.url-lizard-map-workspace-items").attr("href");
  $.ajax({
    url: url,
    data: {workspace_id: workspace_id},
    success: function(workspace_items_li) {
      // prevent looping error: test destroying object before overwrite: does not work
      // $("ul#workspace_" + workspace_id).sortable("destroy"); 
      // replace list items with new list items
        $("ul#workspace_" + workspace_id).html(workspace_items_li);
        bindCheckboxes();
      // addWorkspaceSortable(workspace_id);
    },
    type: "GET",
    async: false
  });
};

// Update workspace boxes and their visible layers.
updateWorkspace = function(workspace_id) {
  updateLayer(workspace_id);
  updateWorkspaceBox(workspace_id);
  stretchOneSidebarBox();
};

// Initialize all workspace actions.
$(document).ready(function(){
  addWorkspaceSortableDroppable();

    // {% for workspace in workspaces.user %}
  // Make the items in a workspace sortable.
  // Make the workspace droppable, only accept items with the class
  // '.workspace-acceptable'.
    // updateWorkspaceBox({{ workspace.id }});
    // {% endfor %}

    
  $(".workspace_trash").droppable({
    accept: '.workspace_item',
    hoverClass: 'drophover',
    drop: function(event, ui) {
      workspace_item_id = ui.draggable.attr("value");
      ui.draggable.remove();  // for visual snappyness
      var url = $("a.url-lizard-map-workspace-item-delete").attr("href");
      $.ajax({
        url: url,
        data: { workspace_item_id: workspace_item_id },
        success: function(workspace_id) {
            updateWorkspace(workspace_id);
            //location.reload();
        },
        type: "POST",
        async: false
      });
    }
  });

  // Make checkboxes of workspace_items respond when clicked.
  bindCheckboxes();
});
