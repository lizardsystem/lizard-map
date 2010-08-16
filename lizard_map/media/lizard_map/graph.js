// jslint configuration
/*jslint browser: true */
/*global $, reloadGraphs */

/* Helper functions in graph edit screen.  Needs lizard.js in
order to function correctly.  */
function graph_save_snippet() {
    // the actual graph props are already stored in session on server
    var url, workspace_item_id, workspace_item_location_identifier,
        workspace_item_location_shortname, workspace_item_location_name;
    url = $(this).attr("data-url");
    workspace_item_id = $(this).attr("data-workspace-item-id");
    workspace_item_location_identifier = $(this).attr("data-workspace-item-location-identifier");
    workspace_item_location_shortname = $(this).attr("data-workspace-item-location-shortname");
    workspace_item_location_name = $(this).attr("data-workspace-item-location-name");
    $.post(
        url,
        {workspace_item_id: workspace_item_id,
         workspace_item_location_identifier: workspace_item_location_identifier,
         workspace_item_location_shortname: workspace_item_location_shortname,
         workspace_item_location_name: workspace_item_location_name
        }, function () {
            reloadGraphs();
        });
}

function graph_action() {
    // send all graph properties to server and reload graphs
    var $form, url;
    $form = $(this).parents("form.graph-options");
    url = $form.attr("data-url");
    $.post(
        url,
        $form.serialize(),
        function () {
            reloadGraphs();
            $("div.close").click();
        });
}

$(document).ready(function () {
    $(".graph-save-snippet").bind("click", graph_save_snippet);
    $(".graph-action").bind("click", graph_action);
    graph_action();  // update graph with current options
});
