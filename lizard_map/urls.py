from django.conf import settings
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.contrib import admin
from lizard_ui.urls import debugmode_urlpatterns

import lizard_map.views

urlpatterns = patterns(
    '',
    (r'^api/', include('lizard_map.api.urls')),

    # Adapter
    url(r'^adapter/(?P<adapter_class>.*)/image/$',
        lizard_map.views.AdapterImageView.as_view(),
        name="lizard_map_adapter_image"),
    url(r'^adapter/(?P<adapter_class>.*)/flot_graph_data/$',
        lizard_map.views.AdapterFlotGraphDataView.as_view(),
        name="lizard_map_adapter_flot_graph_data"),
    url(r'^adapter/(?P<adapter_class>.*)/values/(?P<output_type>.*)/$',
        lizard_map.views.AdapterValuesView.as_view(),
        name="lizard_map_adapter_values"),

    # Date range
    url(r'^view_state_service/$',
        lizard_map.views.ViewStateService.as_view(),
        name="lizard_map_view_state_service"),

    url(r'^location_list_service/$',
        lizard_map.views.LocationListService.as_view(),
        name="lizard_map_location_list_service"),

    # Load and save map location
    (r'^map_location_save$',
     'lizard_map.views.map_location_save',
     {},
     'lizard_map.map_location_save'),
    (r'^map_location_load_default$',
     'lizard_map.views.map_location_load_default',
     {},
     'lizard_map.map_location_load_default'),

    # Download map as image
    (r'^download-map/',
     'lizard_map.views.save_map_as_image',
     {},
     'lizard_map.views.save_map_as_image'),

    # Actions on legends.
    url(r'^legend/edit/',
        'lizard_map.views.legend_edit',
        name='lizard_map_legend_edit'),

    # # Export.
    # url(r'^snippet_group/(?P<snippet_group_id>\d+)/statistics/csv/',
    #     'lizard_map.views.export_snippet_group_statistics_csv',
    #     name="lizard_map.export_snippet_group_statistics_csv"),

    # Override these here from lizard-ui, so the application screen
    # shows the map as well.
    url(r'^screen/(?P<slug>.*)/$',
        lizard_map.views.MapIconView.as_view(),
        name='lizard_ui.icons'),

    url(r'^$',
        lizard_map.views.MapIconView.as_view(),
        name='lizard_ui.icons'),
    )


if getattr(settings, 'LIZARD_MAP_STANDALONE', False):
    admin.autodiscover()
    urlpatterns += patterns(
        '',
        (r'^ui/', include('lizard_ui.urls')),
        (r'^admin/', include(admin.site.urls)),
        # Demo map stuff.
        # (r'^$', 'django.views.generic.simple.direct_to_template',
        #  {'template': 'lizard_map/example_openlayers.html'}),
        # (r'^example_wms/$', 'django.views.generic.simple.direct_to_template',
        #  {'template': 'lizard_map/example_wms.html'}),

        # Homepage
        url(r'^$',
            lizard_map.views.HomepageView.as_view(),
            name="lizard_map_homepage"),
    )
    urlpatterns += debugmode_urlpatterns()
