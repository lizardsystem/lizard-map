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

function graph_action_reload() {
    // send all graph properties to server and reload page
    var $form, url;
    $form = $(this).parents("form.graph-options");
    url = $form.attr("data-url");
    $.post(
        url,
        $form.serialize(),
        function () {
            // Always reload page: statistics & graphs can be different.
            location.reload();
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

function setGraphFilterMonth() {
    var $form, status;
    $form = $(".popup-graph-edit-global");
    $form.each(function () {
        status = $(this).find("input:radio:checked").attr("value");
        if (status === 4) { // 4 is "MONTH"
            $(this).find(".graph-filter-month").attr('disabled', false);
        } else {
            $(this).find(".graph-filter-month").attr('disabled', true);
        }
    });
}

function setUpGraphForm() {
    // Set current status.
    setGraphFilterMonth();

    // Setup click.
    $(".popup-graph-edit-global input:radio").click(setGraphFilterMonth);
}

$(document).ready(function () {
    $(".graph-save-snippet").bind("click", graph_save_snippet);
    $(".graph-action").bind("click", graph_action);
    $(".graph-action-reload").bind("click", graph_action_reload);
    //graph_action();  // update graph with current options
    setUpGraphForm();
});
