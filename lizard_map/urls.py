from django.conf import settings
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.contrib import admin
from lizard_ui.urls import debugmode_urlpatterns

import lizard_map.views
admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^ui/', include('lizard_ui.urls')),
    (r'^api/', include('lizard_map.api.urls')),

    # Actions/services on/from my workspace and my collage
    url(r'^myworkspace/workspace_items/reorder/$',  # L3
        'lizard_map.views.workspace_item_reorder',
        name="lizard_map_workspace_item_reorder"),
    url(r'^myworkspace/workspace_items/toggle/$',  # L3
        'lizard_map.views.workspace_item_toggle',
        name="lizard_map_workspace_item_toggle"),
    url(r'^myworkspace/workspace_items/delete/$',  # L3
        'lizard_map.views.workspace_item_delete',
        name="lizard_map_workspace_item_delete"),
    url(r'^myworkspace/workspace_items/edit/$',  # L3
        'lizard_map.views.workspace_edit_item',
        name="lizard_map_workspace_edit_item"),
    url(r'^myworkspace/wms/$',  # L3
        'lizard_map.views.wms',
        name="lizard_map_workspace_edit_wms"),
    url(r'^myworkspace/empty/$',  # L3
        lizard_map.views.WorkspaceEmptyView.as_view(),
        name="lizard_map_workspace_empty"),
    url(r'^myworkspace/save/$',  # L3
        lizard_map.views.WorkspaceSaveView.as_view(),
        name="lizard_map_workspace_save"),
    url(r'^myworkspace/load/$',  # L3
        lizard_map.views.WorkspaceLoadView.as_view(),
        name="lizard_map_workspace_load"),

    # Partially the same actions as above,
    # you have to put workspace_id in GET parameter here...
    url(r'^workspaceitem/extent/$',
        'lizard_map.views.workspace_item_extent',
        name="lizard_map_workspace_item_extent"),
    # Same for workspace storages
    url(r'^workspacestorageitem/extent/$',
        'lizard_map.views.workspace_storage_item_extent',
        name="lizard_map_workspace_storage_item_extent"),

    url(r'^mycollage/$',  # L3
        lizard_map.views.CollageDetailView.as_view(),
        name="lizard_map_collage_edit_detail"),
    url(r'^mycollage/add_item_coordinates/$',  # L3 add collage item
        lizard_map.views.CollageView.as_view(),
        name="lizard_map_collage"),
    url(r'^mycollage/add_item/$',  # L3 add collage item
        lizard_map.views.CollageAddView.as_view(),
        name="lizard_map_collage_add"),
    url(r'^mycollage/empty/$',  # L3 empty collage
        lizard_map.views.CollageEmptyView.as_view(),
        name="lizard_map_collage_empty"),
    url(r'^mycollage/edit_item/$',  # L3 delete or update
        lizard_map.views.CollageItemEditView.as_view(),
        name="lizard_map_collage_item_edit"),
    url(r'^mycollage/item/(?P<collage_item_id>\d+)/edit/$',  # L3 Properties
        lizard_map.views.CollageItemEditorView.as_view(),
        name="lizard_map_collage_item_editor"),
    url(r'^mycollage/popup/$',  # L3 popup, works like the old one
        'lizard_map.views.collage_popup',
        name="lizard_map_collage_popup"),
    url(r'^mycollage/item/(?P<collage_item_id>\d+)/popup/$',  # L3 popup
        'lizard_map.views.collage_popup',
        name="lizard_map_collage_item_popup"),
    url(r'^mycollage/statistics/$',
        lizard_map.views.CollageStatisticsView.as_view(),
        name="lizard_map_statistics"),
    url(r'^mycollage/statistics/csv/$',
        'lizard_map.views.statistics_csv',
        name="lizard_map_statistics_csv"),

    # Search stuff for my workspace.
    url(r'^search_coordinates/',
        'lizard_map.views.search_coordinates',
        name="lizard_map.search_coordinates"),  # L3
    url(r'^search_name/',
        'lizard_map.views.search_coordinates',
        {'_format': 'name'},
        name="lizard_map.search_name"),  # L3

    # Workspace storage
    url(r'^workspace/$',
        lizard_map.views.WorkspaceStorageListView.as_view(),
        name="lizard_map_workspace_storage_list"),
    url(r'^workspace/(?P<workspace_id>\d+)/$',
        lizard_map.views.WorkspaceStorageView.as_view(),
        name="lizard_map_workspace_storage"),
    url(r'^workspace/(?P<workspace_storage_id>\d+)/wms/$',  # L3
        'lizard_map.views.wms',
        name="lizard_map_workspace_storage_wms"),
    url(r'^workspace/(?P<workspace_storage_id>\d+)/search_coordinates/',
        'lizard_map.views.search_coordinates',
        name="lizard_map.search_coordinates"),  # L3
    url(r'^workspace/(?P<workspace_storage_id>\d+)/search_name/',
        'lizard_map.views.search_coordinates',
        {'format': 'name'},
        name="lizard_map.search_name"),  # L3
    # Get to the workspace page by means of a slug
    url(r'^workspace/(?P<workspace_storage_slug>\w+)/$',
        lizard_map.views.WorkspaceStorageView.as_view(),
        name="lizard_map_workspace_slug_storage"),

    # Adapter
    url(r'^adapter/(?P<adapter_class>.*)/image/$',  # L3
        lizard_map.views.AdapterImageView.as_view(),
        name="lizard_map_adapter_image"),
    url(r'^adapter/(?P<adapter_class>.*)/values/(?P<output_type>.*)/$',  # L3
        lizard_map.views.AdapterValuesView.as_view(),
        name="lizard_map_adapter_values"),

    # Date range
    url(r'set_animation_date$',
     'lizard_map.animation.set_animation_date',
     {},
     name="lizard_map.set_animation_date"),
    url(r'^date_range/$',  # L3
        lizard_map.views.DateRangeView.as_view(),
        name="lizard_map_date_range"),

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

    url(r'^screen/(?P<slug>.*)/$',
        lizard_map.views.MapIconView.as_view(),
        name='lizard_ui.icons'),
    url(r'^$',
        lizard_map.views.MapIconView.as_view(),
        name='lizard_ui.icons'),
    )

urlpatterns += debugmode_urlpatterns()

if settings.DEBUG:  # Pragma: no cover
    urlpatterns += patterns(
        '',
        (r'^admin/', include(admin.site.urls)),
        # Demo map stuff.
        # (r'^$', 'django.views.generic.simple.direct_to_template',
        #  {'template': 'lizard_map/example_openlayers.html'}),
        # (r'^example_wms/$', 'django.views.generic.simple.direct_to_template',
        #  {'template': 'lizard_map/example_wms.html'}),

        # Homepage
        url(r'^$',  # L3
            lizard_map.views.HomepageView.as_view(),
            name="lizard_map_homepage"),
    )
