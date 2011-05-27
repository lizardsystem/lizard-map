/*jslint browser: true */
/*jslint evil: true */
/*global $, OpenLayers, TouchHandler, map */


var lastPosition, myLocation, recenter, myLocationLayer;


function setRecenter(value) {
    var html;
    recenter = value;
    if (recenter) {
        map.setCenter(new OpenLayers.LonLat(
            lastPosition.coords.longitude,
            lastPosition.coords.latitude).transform(
                map.displayProjection, map.getProjectionObject()));
        html = "<a href='javascript:setRecenter( false );'><img src='images/location.png' width=18 height=18 border=0></a> Autocenter " +
            lastPosition.coords.longitude +  "&deg; " + lastPosition.coords.latitude + "&deg;";

    }
    else {
        html = "<a href='javascript:setRecenter( true );'><img src='images/location-bw.png' width=18 height=18 border=0></a> Autocenter";

    }
    // document.getElementById("notes").innerHTML = html;
}


function positionUpdate(position) {
    lastPosition = position;
    myLocation.move(new OpenLayers.LonLat(
        lastPosition.coords.longitude,
        lastPosition.coords.latitude).transform(
            map.displayProjection, map.getProjectionObject()));
    if (recenter) {
        map.setCenter(new OpenLayers.LonLat(
            lastPosition.coords.longitude,
            lastPosition.coords.latitude).transform(
                map.displayProjection, map.getProjectionObject()));
    }
    setRecenter(recenter);
}


function positionUpdateFail(error) {
    document.getElementById("notes").innerHTML = error.message;
}



/* Adds touch functionality and current location*/
function initializeTouch() {

    // Add touch handler for iPad, iPhone, Android
    this.touchhandler = new TouchHandler(map, 10);

    // Zoom to current location, add handler for following current location
    if (navigator.geolocation !== undefined) {
        myLocationLayer = new OpenLayers.Layer.Vector("Location");
        myLocation = new OpenLayers.Feature.Vector(
            new OpenLayers.Geometry.Point(-100, 40).transform(
                map.displayProjection, map.getProjectionObject()),
            {isBaseLayer: false},
            {externalGraphic: '/static_media/lizard_map/location.png',
             graphicHeight: 18, graphicWidth: 18});
        myLocationLayer.addFeatures(myLocation);
        map.addLayer(myLocationLayer);

        navigator.geolocation.watchPosition(
            positionUpdate, positionUpdateFail);
    }

}


$(document).ready(initializeTouch);
