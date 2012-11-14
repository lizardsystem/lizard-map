// Prevent stray console.log's from messing up in IE.
if ( ! window.console ) console = { log: function(){} };


// Resize map viewports on window resize.
$(function() {
    $(window).resize(function(){
        $('#map-a').css('height',  ($("#content").height()/2) + 'px');
        $('#map-b').css('height',  ($("#content").height()/2) + 'px');
        $('#mapawrapper').css('height',  ($("#content").height()/2) - 74 + 'px');
        $('#mapbwrapper').css('height',  ($("#content").height()/2) - 74 + 'px');
    });
});

$(document).keyup(function(e) {
  if (e.keyCode == 27) { // Redirect on escape
    window.location.replace("/analyseopgave/");
  }
});

$(document).ready(function() {
    // Initialize CQL filters
    $('#map-a').data('wms-cql-filters', {'year':'2015', 'scenario': '\'rust\''});
    $('#map-b').data('wms-cql-filters', {'year':'2015', 'scenario': '\'rust\''});

    // Resize map viewports on initial page load
    $('#map-a').css('height',  ($("#content").height()/2) + 'px');
    $('#map-b').css('height',  ($("#content").height()/2) + 'px');

    // Resize menu wrappers to half screen size
    $('#mapawrapper').css('height',  ($("#content").height()/2) - 74 + 'px');
    $('#mapbwrapper').css('height',  ($("#content").height()/2) - 74 + 'px');

    var mapaLayers = {};
    var mapbLayers = {};

    // Define the two base layers
    var baseLayerA = L.tileLayer.wms("http://test.deltaportaal.lizardsystem.nl/service/", {
        layers: 'deltaportaal',
        format: 'image/png',
        transparent: true,
        reuseTiles: true,
        attribution: "KAART A"
    });

    var baseLayerB = L.tileLayer.wms("http://test.deltaportaal.lizardsystem.nl/service/", {
        layers: 'deltaportaal',
        format: 'image/png',
        transparent: true,
        reuseTiles: true,
        attribution: "KAART B"
    });
    
    // Read, split and parse lng/lat/zoom from hash
    var h = document.location.hash.replace('#', '').split(',');

    // Default initial lng/lat/zoom values
    var lat = 51.95442214470791, lng = 5.16082763671875, z = 8;
    if (h[0] && h[1] && h[2]) {
        lat = parseFloat(h[0]);
        lng = parseFloat(h[1]);
        z   = parseFloat(h[2]);
    }

    // Initialize Leaflet Map instances for Map A and Map B
    var mapa = new L.Map('map-a');
    var mapb = new L.Map('map-b');

    // Attach Map instances to window for global access (debugging)
    window.mapa = mapa;
    window.mapb = mapb;


    // CQL variable updating per map
    function updateCQLA(type, value) {
        var cql_filters = $('#map-a').data('wms-cql-filters');
        cql_filters[type] = value;
        $('#map-a').data('wms-cql-filters', cql_filters);
        console.log($('#map-a').data('wms-cql-filters'));
        return true;
    }

    function updateCQLB(type, value) {
        var cql_filters = $('#map-b').data('wms-cql-filters');
        cql_filters[type] = value;
        $('#map-b').data('wms-cql-filters', cql_filters);
        console.log($('#map-b').data('wms-cql-filters'));
        return true;
    }



    // Set the locations and add the baselayer for both maps
    mapa.setView(new L.LatLng(lat, lng), z).addLayer(baseLayerA);
    mapb.setView(new L.LatLng(lat, lng), z).addLayer(baseLayerB);

    // Set scales to the maps
    L.control.scale().addTo(mapa);
    L.control.scale().addTo(mapb);


    var mapaMove = function(e) {
        // Stuff to do when Map A is being panned/zoomed
        var c = mapa.getCenter();
        var z = mapa.getZoom();
        mapb.setView(new L.LatLng(c.lat, c.lng), z);
        document.location.hash = [c.lat, c.lng, z].join(',');
    };
    var mapbMove = function(e) {
        // Stuff to do when Map B is being panned/zoomed
        var c = mapb.getCenter();
        var z = mapb.getZoom();
        mapa.setView(new L.LatLng(c.lat, c.lng), z);
        document.location.hash = [c.lat, c.lng, z].join(',');
    };

    // Bind mapaMove and mapbMove to the 'mouseup' events of Leaflet's Map
    mapa.on('moveend', mapaMove);
    mapb.on('moveend', mapbMove);


    function reloadALayers(self, key, value) {
        // Remove the layer
        mapa.removeLayer(mapaLayers[self.attr('id')]);

        var layer_filters = self.data("workspace-wms-cql-filters");
        var selected_filters = $('#map-a').data('wms-cql-filters');

        var cql_filters = '';

        // Add the filters that are selected and available for this layer.
        for (key in selected_filters){
            if ($.inArray(key, layer_filters) !== -1){
                cql_filters += key + '=' + selected_filters[key];
            }
        }

        // params = $.parseJSON($(this).data("params"));
        params = $.parseJSON(self.attr("data-params"));
        // Important: data() did not work here ^^^, attr() does!

        url = self.data("url");

        if(params && params.layers) {

            opts = {
                layers: params.layers,
                format: 'image/png',
                transparent: true,
                reuseTiles: true
            };
            
            if(cql_filters) {
                opts['cql_filter'] = cql_filters;
            }

            mapaLayers[self.attr('id')] = L.tileLayer.wms(url, opts);

            // Add the new layer
            mapa.addLayer(mapaLayers[self.attr('id')]);
        }
    }


    function reloadBLayers(self, key, value) {
        // Remove the layer
        mapb.removeLayer(mapbLayers[self.attr('id')]);

        var layer_filters = self.data("workspace-wms-cql-filters");
        var selected_filters = $('#map-b').data('wms-cql-filters');

        var cql_filters = '';

        // Add the filters that are selected and available for this layer.
        for (key in selected_filters){
            if ($.inArray(key, layer_filters) !== -1){
                cql_filters += key + '=' + selected_filters[key];
            }
        }

        // params = $.parseJSON($(this).data("params"));
        params = $.parseJSON(self.attr("data-params"));
        // Important: data() did not work here ^^^, attr() does!

        url = self.data("url");

        if(params && params.layers) {

            opts = {
                layers: params.layers,
                format: 'image/png',
                transparent: true,
                reuseTiles: true
            };
            
            if(cql_filters) {
                opts['cql_filter'] = cql_filters;
            }

            mapbLayers[self.attr('id')] = L.tileLayer.wms(url, opts);

            // Add the new layer
            mapb.addLayer(mapbLayers[self.attr('id')]);
        }
    }



    // MAP A CONTROL HANDLERS
    $('#mapa-controls #scenario-rust').click(function() {
        // Set the scenario to rust for map A
        updateCQLA("scenario", "'rust'");

        // For every checked workspace item
        $(".ws-a-item:checked").each(function(key, value) {
            reloadALayers($(this), key, value);
        });
      });


    $('#mapa-controls #scenario-druk').click(function() {
        // Set the scenario to druk for map A
        updateCQLA("scenario", "'druk'");

        // For every checked workspace item
        $(".ws-a-item:checked").each(function(key, value) {
            reloadALayers($(this), key, value);
        });
      });


    $('#mapa-controls #scenario-stoom').click(function() {
        // Set the scenario to stoom for map A
        updateCQLA("scenario", "'stoom'");

        // For every checked workspace item
        $(".ws-a-item:checked").each(function(key, value) {
            reloadALayers($(this), key, value);
        });
      });

    $('#mapa-controls #scenario-warm').click(function() {
        // Set the scenario to warm for map A
        updateCQLA("scenario", "'warm'");

        // For every checked workspace item
        $(".ws-a-item:checked").each(function(key, value) {
            reloadALayers($(this), key, value);
        });
      });

      $('#mapa-controls #year-2015').click(function() {
        // Set the year to 2015 for map A
        updateCQLA("year", "2015");

        // For every checked workspace item
        $(".ws-a-item:checked").each(function(key, value) {
            reloadALayers($(this), key, value);
        });
        
      });


      $('#mapa-controls #year-2100').click(function() {
        // Set the year to 2100 for map A
        updateCQLA("year", "2100");

        // For every checked workspace item
        $(".ws-a-item:checked").each(function(key, value) {
            reloadALayers($(this), key, value);
        });
        
      });

      $('#mapa-controls #year-2050').click(function() {
        // Set the year to 2050 for map A
        updateCQLA("year", "2050");

        // For every checked workspace item
        $(".ws-a-item:checked").each(function(key, value) {
            reloadALayers($(this), key, value);
        });
      });

    // MAP B CONTROL HANDLERS
    $('#mapb-controls #scenario-rust').click(function() {
        // Set the scenario to rust for map B

        updateCQLB("scenario", "'rust'");

        // For every checked workspace item
        $(".ws-b-item:checked").each(function(key, value) {
            reloadBLayers($(this), key, value);
        });
      });


    $('#mapb-controls #scenario-druk').click(function() {
        // Set the scenario to druk for map B

        updateCQLB("scenario", "'druk'");

        // For every checked workspace item
        $(".ws-b-item:checked").each(function(key, value) {
            reloadBLayers($(this), key, value);
        });
      });


    $('#mapb-controls #scenario-stoom').click(function() {
        // Set the scenario to stoom for map B

        updateCQLB("scenario", "'stoom'");

        // For every checked workspace item
        $(".ws-b-item:checked").each(function(key, value) {
            reloadBLayers($(this), key, value);
        });
      });


    $('#mapb-controls #scenario-warm').click(function() {
        // Set the scenario to warm for map B

        updateCQLB("scenario", "'warm'");

        // For every checked workspace item
        $(".ws-b-item:checked").each(function(key, value) {
            reloadBLayers($(this), key, value);
        });
      });


      $('#mapb-controls #year-2015').click(function() {
        // Set the year to 2015 for map B

        updateCQLB("year", "'2015'");

        // For every checked workspace item
        $(".ws-b-item:checked").each(function(key, value) {
            reloadBLayers($(this), key, value);
        });
      });


      $('#mapb-controls #year-2100').click(function() {
        // Set the year to 2100 for map B
        updateCQLB("year", "'2100'");

        // For every checked workspace item
        $(".ws-b-item:checked").each(function(key, value) {
            reloadBLayers($(this), key, value);
        });
      });

      $('#mapb-controls #year-2050').click(function() {
        // Set the year to 2050 for map B
        updateCQLB("year", "'2050'");

        // For every checked workspace item
        $(".ws-b-item:checked").each(function(key, value) {
            reloadBLayers($(this), key, value);
        });
      });


    
    $('.ws-a-item').click(function() {

        if($(this).prop("checked")) {

            var layer_filters = $(this).data("workspace-wms-cql-filters");
            var selected_filters = $('#map-a').data('wms-cql-filters');

            var cql_filters = '';

            // Add the filters that are selected and available for this layer.
            for (var key in selected_filters){
                if ($.inArray(key, layer_filters) !== -1){
                    cql_filters += key + '=' + selected_filters[key];
                }
            }

            params = $.parseJSON($(this).attr("data-params"));

            url = $(this).data("url");


            if(params && params.layers) {

                opts = {
                    layers: params.layers,
                    format: 'image/png',
                    transparent: true,
                    reuseTiles: true
                };
                
                if(cql_filters) {
                    opts['cql_filter'] = cql_filters;
                }

                mapaLayers[$(this).attr('id')] = L.tileLayer.wms(url, opts);
                
                mapa.addLayer(mapaLayers[$(this).attr('id')]);
            }
        } else {
            mapa.removeLayer(mapaLayers[$(this).attr('id')]);
        }
    });

    $('.ws-b-item').click(function() {
        if($(this).prop("checked")) {

            var layer_filters = $(this).data("workspace-wms-cql-filters");
            var selected_filters = $('#map-b').data('wms-cql-filters');
            
            var cql_filters = '';

            // Add the filters that are selected and available for this layer.
            for (var key in selected_filters){
                if ($.inArray(key, layer_filters) !== -1){
                    cql_filters += key + '=' + selected_filters[key];
                }
            }

            params = $.parseJSON($(this).attr("data-params"));

            url = $(this).data("url");


            if(params && params.layers) {

                opts = {
                    layers: params.layers,
                    format: 'image/png',
                    transparent: true,
                    reuseTiles: true
                };
                
                if(cql_filters) {
                    opts['cql_filter'] = cql_filters;
                }

                mapbLayers[$(this).attr('id')] = L.tileLayer.wms(url, opts);
                
                mapb.addLayer(mapbLayers[$(this).attr('id')]);
            }
        } else {
            mapb.removeLayer(mapbLayers[$(this).attr('id')]);
        }
    });
});