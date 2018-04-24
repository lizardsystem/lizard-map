from django.conf.urls.defaults import patterns

urlpatterns = patterns(
    '',

    # Load and save map location
    (r'^map_location_save$',
     'lizard_map.views.map_location_save',
     {},
     'lizard_map.map_location_save'),
    (r'^map_location_load_default$',
     'lizard_map.views.map_location_load_default',
     {},
     'lizard_map.map_location_load_default'),

)
