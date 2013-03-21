/*
Support for animations

*/

STATUS_STOP = 0;
STATUS_PLAY = 1;

// For each .workspace-wms-layer that is an animation,
// there is an AnimatedLayer object.
max_timesteps = 0;
wms_ani_layers = {};


function formatNumberLength(num, length) {
    var r = "" + num;
    while (r.length < length) {
        r = "0" + r;
    }
    return r;
}


/*
Animated layer: keep track of an animated wms.

We use a Backbone model because of its more object-oriented nature and the
possibility to sync all kinds of info with the server later on.
*/
var AnimatedLayer = Backbone.Model.extend({
  defaults: {
    current_timestep: 0,  // to be altered from outside
    current_in_map: {},  // indices if layers that are in OL.map
    current_visible: 0
  },
  constructor: function(options) {
    Backbone.Model.prototype.constructor.call(this, options);
    this.params = options.params;
    this.url = options.url;
    this.name = options.name;
    this.options = options.options;
    this.max_timesteps = 288;
    this.current_timestep = 0;  // to be altered from outside
    this.current_in_map = {};  // indices if layers that are in OL.map
    this.current_visible = null;
    this.readyForNext = null;

    this.layers = [];
    var me = this;
    for (var i=0; i < this.max_timesteps; i++) {
      this.params.time = i;
      this.layers[i] = new OpenLayers.Layer.WMS(
        this.name + ' (' + i + ')', 
        this.url, this.params, this.options);

      // make new layer appear after completed loading.
      this.layers[i].events.register("loadend", this.layers[i], function() {
          console.log('layer started loading: ', this.params.TIME);
      });
      this.layers[i].events.register("loadend", this.layers[i], function() {
              console.log('layer finished loading: ', this.params.TIME);
              this.setOpacity(1);
              // make the old layer disappear
              for (var ts in me.current_in_map) {
                  //console.log('ts', ts, this.params.TIME);
                  if (parseInt(ts) !== parseInt(me.current_timestep)) {
                      //console.log('removing from map... ts ', ts);
                      //console.log('me.layers[ts] ', me.layers[ts]);
                      //map.removeLayer(me.layers[ts]); 
                      // strangely enough, the id sometimes change -> then we'll remove by name
                      var remove_layers = map.getLayersByName(me.layers[ts].name);
                      for (var c=0; c<remove_layers.length; c++) {
                        map.removeLayer(remove_layers[c]);
                      }
                      delete me.current_in_map[ts];
                  }
              }
              var nextTimestep = me.readyForNext;
              me.readyForNext = null;
              if ((nextTimestep !== null) && (parseInt(nextTimestep) !== parseInt(this.params.TIME))) {
                  // console.log('nextTimestep: ', nextTimestep);
                  me.setTimestep(nextTimestep);
              } 
          });

    }
  },
  initialize: function() {
  },
  updateMap: function() {
    // update visible layer
    // add/remove layers
    console.log('updating map');
  },
  setTimestep: function(timestep) {
      // 5 seconds timeout
      if ((this.readyForNext !== null) && (Date.now() < this.startedLoading + 5000)) {
          // console.log('not ready for next timestep... still busy ', timestep);
          // is the first next thing
          // Can be overwritten, which is ok.
          this.readyForNext = timestep;  
          return;
      }

      if (timestep < 0) { timestep = 0; }
      if (timestep >= this.max_timesteps) { timestep = this.max_timesteps-1; }
      this.current_timestep = timestep;
      //console.log('timestep is now ', this.current_timestep);
      //var to_delete_from_map = {};
      //for (ts in this.current_in_map) {to_delete_from_map[ts] = ts;}  // start with all layers
      // console.log('initial to delete ', to_delete_from_map);
      for (var ts=timestep; ts<this.max_timesteps && ts<timestep+1; ts++) {
        //console.log('we want timestep ', ts);
        if (this.current_in_map[ts] === undefined) {
          // new
          //console.log('adding to map ', ts);
          map.addLayer(this.layers[ts]);
          this.current_in_map[ts] = ts;
          this.readyForNext = ts;
          this.startedLoading = Date.now();
        }
     }
     // // now delete all layers from to_delete_from_map
     // for (var ts in to_delete_from_map) {
     //   //console.log('removing from map... ts ', ts);
     //   map.removeLayer(this.layers[ts]);
     //   delete this.current_in_map[ts];
     // }
     // // change current_visible
     // if (this.current_visible !== this.current_timestep) {
     //     var old_visible = this.current_visible;
     //     //first make new layer visible
     //     this.current_visible = this.current_timestep;
     //     //console.log('current_visible', this.current_visible);
     //     this.layers[this.current_visible].setOpacity(1);  // TODO: make opacity configurable
     //     if (old_visible !== null) {
     //         this.layers[old_visible].setOpacity(0);
     //     }
     // }
  },
  shutdown: function() {
    // make sure to remove all objects that are in memory/OL
    for (ts in this.current_in_map) {
      map.removeLayer(this.layers[ts]);
    }
    this.current_in_map = {};
    this.current_visible = null;
  }
});


var ControlPanelView = Backbone.View.extend({
/*
.btn-start-stop -> start/stop animation
.btn-reset -> reset animation (time=0)
*/
  updateTime: function() {
      //this.$el.find("#time").text(this.current_timestep);
      var time_string = Math.floor((this.current_timestep * 10) / 60) + ' uur, ' + formatNumberLength((this.current_timestep * 10) % 60, 2) + ' minuten';
      this.$el.find("#time").text(time_string);
  },
  slide: function(me) {
    // wrapper around the real function, but this function has 'me'.
    //var me = obj;
    sliderFun = function (event, ui){
      //console.log(this);
      //console.log(me);
      //console.log(ui.value);
      me.current_timestep = ui.value;
      me.updateTime();  // updates the DOM
      me.updateLayers(me.current_timestep);
    };
    return sliderFun;
  },
  initialize: function(){
    this.status = STATUS_STOP;
    this.current_timestep = 0;
    this.$el.find("#slider").slider({
      min: 0,
      max: 287,
      slide: this.slide(this),
      value: this.current_timestep
    });
    this.updateTime();
  },
  events: {
    "click .btn-start-stop": "doStartStop",
    "click .btn-reset": "reset"
    },
  doStartStop: function() {
    if (this.status == STATUS_STOP) {
      console.log('play');
      this.status = STATUS_PLAY;
      this.$el.find("a.btn-start-stop i").removeClass("icon-play");
      this.$el.find("a.btn-start-stop i").addClass("icon-pause");
      this.$el.find("#html-start-stop").html("Pause");
      this.animation_loop(this)();  // run it!!
    } else {
      console.log('stop');
      this.$el.find("a.btn-start-stop i").addClass("icon-play");
      this.$el.find("a.btn-start-stop i").removeClass("icon-pause");
      this.$el.find("#html-start-stop").html("Start");
      this.status = STATUS_STOP;
    }
  },
  reset: function() {
    this.status = STATUS_STOP;
    this.current_timestep = 0;

    this.updateTime();
    this.$el.find("#slider").slider("value", this.current_timestep);
    this.updateLayers(this.current_timestep);
  },
  animation_loop: function (me) {
    // Because we use callbacks, it is important to use 'me'.
    fun = function() {
      if (me.status == STATUS_PLAY) {
        //console.log('ready for next: ' + this.readyForNext);
        // increase animation with one step
        me.current_timestep += 1;
        console.log('current_timestep: ' + me.current_timestep);
        me.updateTime();
        // set slider position
        me.$el.find("#slider").slider("value", me.current_timestep);

        // most important part: interact with OpenLayers.
        me.updateLayers(me.current_timestep);
      } else {
        return;  // Animation has stopped
      }
      setTimeout(me.animation_loop(me), 500); // Setting next step. animation speed in ms
    };
    return fun;
  },
  updateLayers: function(timestep) {
    // Update AnimationLayer objects so openlayers gets updated
    // This part is global and not bound to the control.
    $(".workspace-wms-layer").each(function () {
        if ($(this).attr("data-workspace-wms-animatable") === 'true') {
            var id = $(this).attr("data-workspace-wms-id");
            //console.log('current timestep in updateLayers', timestep);
            wms_ani_layers[id].setTimestep(timestep);
        }
    });
  }
});


// Place all animation layers in animation_layers, run prepare on animation
//  * (?). Parts taken from lizard_map.
function init_animation() {
  // Update wms_ani_layers
  // Assume for now that all .workspace-wms-layers are animations
  var to_delete_ani_layers = {};
  max_timesteps = 0;

  for (key in wms_ani_layers) {
    // first mark everything for deleting
    to_delete_ani_layers[key] = key;
  }

  $(".workspace-wms-layer").each(function () {
        var name, url, params, options, id, index, animation_layer, animatable;
        // WMS id, different than workspace ids.
        animatable = $(this).attr("data-workspace-wms-animatable");
        if (animatable !== 'true') { return; }
        id = $(this).attr("data-workspace-wms-id");
        //ids_found.push(id);
        name = $(this).attr("data-workspace-wms-name");
        url = $(this).attr("data-workspace-wms-url");
        params = $(this).attr("data-workspace-wms-params");
        params = $.parseJSON(params);
        // Fix for partial images on tiles
        params['tilesorigin'] = [map.maxExtent.left, map.maxExtent.bottom];
        options = $(this).attr("data-workspace-wms-options");
        options = $.parseJSON(options);
        options.opacity = 0;

        var anim_info_params = '';
        anim_info_params += '?dataset=' + params.dataset;
        anim_info_params += '&srs=epsg:3857';
        anim_info_params += '&request=getinfo';
        // this does not work because it is cross domain. possible solution:
        // https://gist.github.com/barrabinfc/426829
        // $.getJSON(url + anim_info_params, function(data) {
        //   console.log(data);
        // });
    /*
    http://localhost:5000/wms?request=getinfo&dataset=/home/user/git/nens/threedi-server/threedi_server/../var/data/subgrid_map.nc&srs=epsg:3857 */

        index = parseInt($(this).attr("data-workspace-wms-index"));
        if (wms_ani_layers[id] === undefined) {
          console.log('Initializing ani layer', id);
          wms_ani_layers[id] = new AnimatedLayer({
            name: name,
            url: url,
            params: params,
            options: options
            });
          wms_ani_layers[id].setTimestep(0);
          // this layer is not marked for deletion.
        }
        delete to_delete_ani_layers[id];
  });

  for (key in to_delete_ani_layers) {
    console.log('De-initializing wms ani layer ', key);
    wms_ani_layers[key].shutdown();
    delete wms_ani_layers[key];
  }
}


function init_control_panel() {
  //$('#controlpanel').off('click', '.btn-start-stop');
  //#('#controlpanel').off('click', '.btn-reset');
  
  // Bind the control panel to the view.
  control_panel_view = new ControlPanelView({el: $('#controlpanel')});
  //console.log('control panel view ', control_panel_view);
  //control_panel_view = new ControlPanelView({el: $('#controlpanel2')});
}

$(document).ready(function() {
  //init_animation();
  init_control_panel();

  // special for the demo march 2013
  //$("a.popup-date-range").parent().css("display", "none");
  //$("a.map-multiple-selection").parent().css("display", "none");
});
