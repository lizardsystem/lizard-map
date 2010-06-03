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

/* Workspace functions, requires jquery.workspace.js */

// Initialize all workspace actions.
$(document).ready(function(){
    $(".workspace").workspaceInteraction();
    $(".add-snippet").snippetInteraction();
    $("a.lizard-map-link").lizardMapLink();
});
