/* helper functions in graph edit screen */

function graph_post(obj, key, value) {
    var url, workspace_item_id, identifier_json;
    url = $(obj).attr("data-url");
    workspace_item_id = $(obj).attr("data-workspace-item-id");
    identifier_json = $(obj).attr("data-identifier-json");
    $.post(url,
           {key: key, value: value,
            workspace_item_id: workspace_item_id,
            identifier_json: identifier_json}, function() {
               reloadGraphs();
           });
}

function graph_add_maximum() {
    return graph_post(this, 'line_max', 1);
}

function graph_add_minimum() {
    return graph_post(this, 'line_min', 1);
}

function graph_add_average() {
    return graph_post(this, 'line_avg', 1);
}

function graph_add_legend() {
    return graph_post(this, 'legend', 1);
}

function graph_save_snippet() {
    var url, workspace_item_id, workspace_item_location_identifier;
    var workspace_item_location_shortname, workspace_item_location_name;
    url = $(this).attr("data-url");
    workspace_item_id = $(this).attr("data-workspace-item-id");
    workspace_item_location_identifier = $(this).attr("data-workspace-item-location-identifier");
    workspace_item_location_shortname = $(this).attr("data-workspace-item-location-shortname");
    workspace_item_location_name = $(this).attr("data-workspace-item-location-name");
    $.post(url,
           {workspace_item_id: workspace_item_id,
            workspace_item_location_identifier: workspace_item_location_identifier,
            workspace_item_location_shortname: workspace_item_location_shortname,
            workspace_item_location_name: workspace_item_location_name
           }, function() {
               reloadGraphs();
           });
}

$(document).ready(function () {
    $(".graph-add-maximum").bind("click", graph_add_maximum);
    $(".graph-add-minimum").bind("click", graph_add_minimum);
    $(".graph-add-average").bind("click", graph_add_average);
    $(".graph-add-legend").bind("click", graph_add_legend);
    $(".graph-save-snippet").bind("click", graph_save_snippet);
});
