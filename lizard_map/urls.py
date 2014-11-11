from django.conf import settings
from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib import admin
from lizard_ui.urls import debugmode_urlpatterns

import lizard_map.views

urlpatterns = patterns(
    '',
    (r'^api/', include('lizard_map.api.urls')),

    # Actions/services on/from my workspace and my dashboard
    url(r'^myworkspace/workspace_items/reorder/$',
        'lizard_map.views.workspace_item_reorder',
        name="lizard_map_workspace_item_reorder"),
    url(r'^myworkspace/workspace_items/toggle/$',
        'lizard_map.views.workspace_item_toggle',
        name="lizard_map_workspace_item_toggle"),
    url(r'^myworkspace/workspace_items/delete/$',
        'lizard_map.views.workspace_item_delete',
        name="lizard_map_workspace_item_delete"),
    url(r'^myworkspace/workspace_items/edit/$',
        'lizard_map.views.workspace_edit_item',
        name="lizard_map_workspace_edit_item"),
    url(r'^myworkspace/wms/(?P<workspace_item_id>\d+)/$',
        'lizard_map.views.wms',
        name="lizard_map_workspace_edit_wms"),
    url(r'^myworkspace/empty/$',
        lizard_map.views.WorkspaceEmptyView.as_view(),
        name="lizard_map_workspace_empty"),
    url(r'^myworkspace/save/$',
        lizard_map.views.WorkspaceSaveView.as_view(),
        name="lizard_map_workspace_save"),
    url(r'^myworkspace/load/$',
        lizard_map.views.WorkspaceLoadView.as_view(),
        name="lizard_map_workspace_load"),

    # Partially the same actions as above,
    # you have to put workspace_id in GET parameter here...
    url(r'^workspaceitem/extent/$',
        'lizard_map.views.workspace_item_extent',
        name="lizard_map_workspace_item_extent"),
    # Same for workspace storages
    url(r'^workspacestorageitem/extent/$',
        'lizard_map.views.saved_workspace_item_extent',
        name="lizard_map_workspace_storage_item_extent"),

    url(r'^mydashboard/$',
        lizard_map.views.CollageDetailView.as_view(),
        name="lizard_map_collage_edit_detail"),
    url(r'^mydashboard/add_item_coordinates/$',
        lizard_map.views.CollageView.as_view(),
        name="lizard_map_collage"),
    url(r'^mydashboard/add_item/$',
        lizard_map.views.CollageAddView.as_view(),
        name="lizard_map_collage_add"),
    url(r'^mydashboard/empty/$',
        lizard_map.views.CollageEmptyView.as_view(),
        name="lizard_map_collage_empty"),
    url(r'^mydashboard/edit_item/$',
        lizard_map.views.CollageItemEditView.as_view(),
        name="lizard_map_collage_item_edit"),
    url(r'^mydashboard/item/(?P<collage_item_id>\d+)/edit/$',
        lizard_map.views.CollageItemEditorView.as_view(),
        name="lizard_map_collage_item_editor"),
    url(r'^mydashboard/popup/$',
        'lizard_map.views.collage_popup',
        name="lizard_map_collage_popup"),
    url(r'^mydashboard/item/(?P<collage_item_id>\d+)/popup/$',
        'lizard_map.views.collage_popup',
        name="lizard_map_collage_item_popup"),
    url(r'^mydashboard/statistics/$',
        lizard_map.views.CollageStatisticsView.as_view(),
        name="lizard_map_statistics"),
    url(r'^mydashboard/statistics/csv/$',
        'lizard_map.views.statistics_csv',
        name="lizard_map_statistics_csv"),

    url(r'^mydashboard/save/$',
        lizard_map.views.CollageSaveView.as_view(),
        name="lizard_map_collage_save"),
    url(r'^dashboard/(?P<collage_id>\d+)/$',
        lizard_map.views.CollageStorageView.as_view(),
        name="lizard_map_collage_storage"),
    url(r'^dashboard/(?P<collage_storage_slug>\w+)/$',
        lizard_map.views.CollageStorageView.as_view(),
        name="lizard_map_collage_slug_storage"),

    # Search stuff for my workspace.
    url(r'^search_coordinates/',
        'lizard_map.views.search_coordinates',
        name="lizard_map.search_coordinates"),
    url(r'^search_name/',
        'lizard_map.views.search_coordinates',
        {'_format': 'name'},
        name="lizard_map.search_name"),

    # Workspace storage
    url(r'^workspace/$',
        lizard_map.views.WorkspaceStorageListView.as_view(),
        name="lizard_map_workspace_storage_list"),
    url(r'^workspace/(?P<workspace_id>\d+)/$',
        lizard_map.views.WorkspaceStorageView.as_view(),
        name="lizard_map_workspace_storage"),
    url(r'^workspace/(?P<workspace_storage_id>\d+)/(?P<workspace_item_id>\d+)/wms/$',
        'lizard_map.views.wms',
        name="lizard_map_workspace_storage_wms"),
    url(r'^workspace/(?P<workspace_storage_id>\d+)/search_coordinates/',
        'lizard_map.views.search_coordinates',
        name="lizard_map.search_coordinates"),
    url(r'^workspace/(?P<workspace_storage_id>\d+)/search_name/',
        'lizard_map.views.search_coordinates',
        {'_format': 'name'},
        name="lizard_map.search_name"),
    # Get to the workspace page by means of a slug
    url(r'^workspace/(?P<workspace_storage_slug>\w+)/$',
        lizard_map.views.WorkspaceStorageView.as_view(),
        name="lizard_map_workspace_slug_storage"),

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

    url(r'^geocoder/$',
        lizard_map.views.GeocoderService.as_view(),
        name="lizard_map_geocoder"),

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
