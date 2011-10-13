// jslint configuration; btw: don't put a space before 'jslint' below.
/*jslint browser: true */
/*global $ */

/* REST api with jQuery */


/* a hrefs with class "rest-api":
fetch url and build "something" out of it.
*/
function setUpRestApiLinks() {
    $("a.rest-api").live("click", function (event) {
        var url;
        event.preventDefault();
        url = $(this).attr("href");
        $.getJSON(url, function (data) {
            console.log(data);
            $(event.target).html("hallo");
        });
        return false;
    });
}


$(document).ready(function () {
    setUpRestApiLinks();
});
