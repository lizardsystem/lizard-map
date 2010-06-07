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

setUpWorkspaceAcceptable = function() {
    // Set up draggability for current and future items.
    // See http://tinyurl.com/29lg4y3 .
    $(".workspace-acceptable").live("mouseover", function() {
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
    $(".workspace-acceptable").live("click", function(event) {
        $(".workspace-acceptable").removeClass("selected");
        $(this).addClass("selected");
        var name = $(this).attr("data-name");
        var layer_method = $(this).attr("data-layer_method");
        var layer_method_json = $(this).attr("data-layer_method_json");
        var url_add_item_temp = $(".workspace").attr(
            "data-url-lizard-map-session-workspace-add-item-temp");
        $.post(url_add_item_temp,
               { name: name,
                 layer_method: layer_method,
                 layer_method_json: layer_method_json
               },
               function(workspace_id) {
                   updateLayer(workspace_id);
               });
        stretchOneSidebarBox();
    });
};


// Initialize all workspace actions.
$(document).ready(function(){
    setUpWorkspaceAcceptable();
    /* Workspace functions, requires jquery.workspace.js */
    $(".workspace").workspaceInteraction();
    $(".add-snippet").snippetInteraction();
    $("a.lizard-map-link").lizardMapLink();
});
