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
        var adapter_class = $(this).attr("data-adapter-class");
        var adapter_layer_json = $(this).attr("data-adapter-layer-json");
        var url_add_item_temp = $(".workspace").attr(
            "data-url-lizard-map-session-workspace-add-item-temp");
        $.post(url_add_item_temp,
               { name: name,
                 adapter_class: adapter_class,
                 adapter_layer_json: adapter_layer_json
               },
               function(workspace_id) {
                   updateLayer(workspace_id);
               });
        stretchOneSidebarBox();
    });
};

// Date selector: only support for ONE date selector at the moment.

function setUpDateChoice() {
    $.datepicker.setDefaults($.datepicker.regional['nl']);
    $("#id_date_start").datepicker();
    $("#id_date_end").datepicker();
}


function setUpDateAjaxForm(overlay) {
    var form = $("form", overlay);
    form.submit(function() {
        $.post(
            form.attr('action'),
            form.serialize(),
            function(data) {
                // This is the success handler.  Form can contain errors,
                // though.
                var newForm = $(data).find('form');
                form.html(newForm);
                setUpDateChoice();
                var freshForm = $("form", overlay);
                setUpDateAjaxForm(freshForm);
                if (newForm.html().indexOf("rror") == -1) {
                    // No error/Error, so refresh graphs and close the popup.
                    loadCorrectlySizedImages();
                    $("div.close", overlay).click();
                }
            });
        return false;
    });
}


function setUpDatePopup() {
    $(".popup-trigger").live('mouseover', function() {
        if (!$(this).data("popup-initialized")) {
            $(this).data("popup-initialized", true);
            $(this).overlay({
                onLoad: function() {
                    var overlay = this.getOverlay();
                    setUpDateAjaxForm(overlay);
                }
            });

        };
    });
};


// Initialize all workspace actions.
$(document).ready(function(){
    setUpWorkspaceAcceptable();
    setUpDatePopup();
    setUpDateChoice();
    /* Workspace functions, requires jquery.workspace.js */
    $(".workspace").workspaceInteraction();
    // $(".add-snippet").snippetInteraction(); // als het met live werkt kan het hier
    $("a.lizard-map-link").lizardMapLink();
});
