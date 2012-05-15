// lizard_leaflet uses the module pattern, function is called at the end!
var lizard_leaflet = function () {

    var map; // Module-private, holds the Leaflet Map instance

    // Lizard-map config
    // These can't be initialized until the page has loaded, but then they're
    // constant.
    var projection;
    var display_projection;
    var projection_proj4js = new Proj4js.Proj('EPSG:900913');
    var latlon_proj4js = new Proj4js.Proj('EPSG:4326');

    var setupLizardMap = function () {
	var lizard_map_wms = $("#lizard-map-wms");
	projection = lizard_map_wms.attr("data-projection");
	display_projection = lizard_map_wms.attr("data-display_projection");
//	projection_proj4js =  new Proj4js.Proj(projection);
    }

    var toLatLng = function(coordX, coordY) {

	var point = new Proj4js.Point(coordX, coordY);
	Proj4js.transform(projection_proj4js, latlon_proj4js, point);
	return new L.LatLng(point.x, point.y);
    }

    var getStartExtent = function() {
	// Find client-side extra data.
	var lizard_map_wms = $("#lizard-map-wms");

	start_extent_left = lizard_map_wms.attr("data-start-extent-left");
	start_extent_top = lizard_map_wms.attr("data-start-extent-top");
	start_extent_right = lizard_map_wms.attr("data-start-extent-right");
	start_extent_bottom = lizard_map_wms.attr("data-start-extent-bottom");

	// Leaflet wants everything in LatLng, sigh
	bounds = new L.LatLngBounds(
            toLatLng(parseFloat(start_extent_bottom), parseFloat(start_extent_left)),
            toLatLng(parseFloat(start_extent_top), parseFloat(start_extent_right))
	);
	alert(bounds.toBBoxString());
	return bounds;
    }

    var showMap = function () {
	setupLizardMap();

	// Set up projection and bounds.
	// ...
	//var res = [364, 242, 161, 107, 71, 47, 31, 21, 14, 9, 6, 4, 2.7, 1.8, 0.9, 0.45, 0.2];
	// var rdProjStr = "+title=Amersfoort / RD New +proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel +units=m +towgs84=565.2369,50.0087,465.658,-0.406857330322398,0.350732676542563,-1.8703473836068,4.0812 +no_defs <>";
	// var crs = L.CRS.proj4js(
        //     'EPSG:28992',
        //     rdProjStr,
        //     new L.Transformation(1, 0, -1, 0)
	// );
	// alert(crs);
	// var options = {
        //     crs: crs,
        //     //scale: function(zoom) {
        //     //    return 1 / res[zoom];
        //     //},
        //     //continuousWorld: true,
	// };

	map = new L.Map('map');

	// add OSM map layer (hosted by cloudmade)
	var cloudmadeUrl = 'http://{s}.tile.cloudmade.com/BC9A493B41014CAABB98F0471D759707/997/256/{z}/{x}/{y}.png';
	var cloudmadeAttribution = 'Map data &copy; 2011 OpenStreetMap contributors, Imagery &copy; 2011 CloudMade';
	var cloudmade = new L.TileLayer(cloudmadeUrl, {maxZoom: 18, attribution: cloudmadeAttribution});
	map.addLayer(cloudmade);

	map.fitBounds(getStartExtent());
    }

    return {
	'showMap': showMap
    };
}();

