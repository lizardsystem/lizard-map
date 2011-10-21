// jslint configuration; btw: don't put a space before 'jslint' below.
/*jslint browser: true */
/*global $ */

/* REST api with jQuery */


function makeHtml(data) {
    var items = [];
    console.log(typeof data);
    if (typeof data === "string") {
        return data;
    }
    if (typeof data === "function") {
        return data;
    }
    $.each(data, function (key, val) {
        console.log(key, val);
        if (val === null) {
            items.push('<li><span>' + key + '</span></li>');
        } else if ((typeof val === "string") && (val.indexOf('http://') === 0)) {
            items.push('<li><a href="' + val + '" class="rest-api">' + key + '</a></li>');
        } else {
            //console.log(val);
            items.push('<li><span>' + key + '</span>' + makeHtml(val) + '</li>');
        }
     });
    //console.log(items);
    return $('<ul/>', {html: items.join('')}).html();
}


function apiRequest(target) {
    var url;
    url = $(target).attr("href");
    $.getJSON(url, function (data) {
        $(target).parents(".rest-api-container").html(makeHtml(data));
    });
 }


/* a hrefs with class "rest-api":
fetch url and build "something" out of it.
*/
function setUpRestApiLinks() {
    $("a.rest-api").live("click", function(event) {
        event.preventDefault();
        apiRequest(event.target);
        return false;
    });

    // Initial
    $("a.rest-api").each(function () {
        apiRequest(this);
    });
}


$(document).ready(function () {
    setUpRestApiLinks();
});
