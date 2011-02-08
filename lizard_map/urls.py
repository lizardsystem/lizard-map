from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^api/', include('lizard_map.api.urls')),
    # Actions/services on/from workspaces
    url(r'^workspace/(?P<workspace_id>\d+)/wms/',
        'lizard_map.views.wms',
        name="lizard_map_wms"),
    url(r'^workspace/(?P<workspace_id>\d+)/workspace_items/reorder/',
        'lizard_map.views.workspace_item_reorder',
        name="lizard_map_workspace_item_reorder"),
    url(r'^workspace/(?P<workspace_id>\d+)/workspace_items/add/',
        'lizard_map.views.workspace_item_add',
        name="lizard_map_workspace_item_add"),
    url(r'^workspace/(?P<workspace_id>\d+)/workspace_items/empty/',
        'lizard_map.views.workspace_item_empty',
        name="lizard_map_workspace_item_empty"),
    url(r'^workspace/(?P<workspace_id>\d+)/',
        'lizard_map.views.workspace',
        name="lizard_map_workspace"),

    # Date range
    (r'^set_date_range$',
     'lizard_map.daterange.set_date_range',
     {},
     'lizard_map.set_date_range'),
    url(r'set_animation_date$',
     'lizard_map.animation.set_animation_date',
     {},
     name="lizard_map.set_animation_date"),

    # Load and save map location
    (r'^map_location_save$',
     'lizard_map.views.map_location_save',
     {},
     'lizard_map.map_location_save'),
    (r'^map_location_load_default$',
     'lizard_map.views.map_location_load_default',
     {},
     'lizard_map.map_location_load_default'),

    # Collages and snippets
    url(r'^collage/(?P<collage_id>\d+)/$',
        'lizard_map.views.collage',
        name="lizard_map.collage"),
    # url(r'^collage/(?P<collage_id>\d+)/edit/$',
    #     'lizard_map.views.collage',
    #     {'editable': True,
    #      'template': 'lizard_map/collage_edit.html'},
    #     name="lizard_map.collage_edit"),
    url(r'^collage/(?P<collage_id>\d+)/popup/$',
        'lizard_map.views.collage_popup',
        name="lizard_map.collage_popup"),
    url(r'^collage_popup/$',
        'lizard_map.views.collage_popup',
        name="lizard_map.collage_popup"),
    url(r'^snippet/(?P<snippet_id>\d+)/popup$',
        'lizard_map.views.snippet_popup',
        name="lizard_map.snippet_popup"),
    url(r'^snippet/(?P<snippet_id>\d+)/edit/$',
        'lizard_map.views.snippet_edit',
        name="lizard_map.snippet_edit"),
    url(r'^snippet_popup/',
        'lizard_map.views.snippet_popup',
        name="lizard_map.snippet_popup"),
    url(r'^snippet_group/(?P<snippet_group_id>\d+)/image_edit/',
        'lizard_map.views.snippet_group_graph_edit',
        name="lizard_map.snippet_group_graph_edit"),
    url(r'^snippet_group/(?P<snippet_group_id>\d+)/image/',
        'lizard_map.views.snippet_group_image',
        name="lizard_map.snippet_group_image"),

    # Partially the same actions as above,
    # you have to put workspace_id in GET parameter here...
    url(r'^workspaceitemreorder/$',
        'lizard_map.views.workspace_item_reorder',
        name="lizard_map_workspace_item_reorder"),
    url(r'^workspaceitemadd/$',
        'lizard_map.views.workspace_item_add',
        name="lizard_map_workspace_item_add"),
    url(r'^workspaceitem/extent/$',
        'lizard_map.views.workspace_item_extent',
        name="lizard_map_workspace_item_extent"),

    # Actions on your session workspace - the system looks for the right
    # workspace.
    url(r'^session_workspace/$',
        'lizard_map.views.session_workspace_edit_item',
        {'workspace_category': 'temp'},
        name="lizard_map_session_workspace_add_item_temp"),
    url(r'^session_workspace/temp/extent/$',
        'lizard_map.views.session_workspace_extent',
        {'workspace_category': 'temp'},
        name="lizard_map_session_workspace_extent_temp"),

    # Actions/services on session collages
    url(r'^session_collage/add/',
        'lizard_map.views.session_collage_snippet_add',
        name="lizard_map_session_collage_snippet_add"),
    url(r'^session_collage/add_session_graph_options/',
        'lizard_map.views.session_collage_snippet_add',
        {'session_graph_options': True},
        name="lizard_map_session_collage_snippet_add_session_graph_options"),
    url(r'^session_collage/delete/',
        'lizard_map.views.session_collage_snippet_delete',
        name="lizard_map_session_collage_snippet_delete"),

    # Actions on workspace items
    url(r'^workspaceitem/(?P<workspace_item_id>\d+)/delete/',
        'lizard_map.views.workspace_item_delete',
        name="lizard_map_workspace_item_delete"),
    url(r'^workspace_item/(?P<workspace_item_id>\d+)/image/',
        'lizard_map.views.workspace_item_image',
        name="lizard_map.workspace_item_image"),
    url(r'^workspace_item/(?P<workspace_item_id>\d+)/' +
        'image_session_graph_options/',
        'lizard_map.views.workspace_item_image',
        {'session_graph_options': True},
        name="lizard_map.workspace_item_image_session_graph_options"),
    url(r'^workspaceitem/delete/',
        'lizard_map.views.workspace_item_delete',
        name="lizard_map_workspace_item_delete"),
    url(r'^workspaceitem/edit/',
        'lizard_map.views.workspace_item_edit',
        name="lizard_map_workspace_item_edit"),

    # Actions on legends.
    url(r'^legend/edit/',
        'lizard_map.views.legend_edit',
        name='lizard_map_legend_edit'),

    # Search stuff.
    url(r'^search_coordinates/',
        'lizard_map.views.search_coordinates',
        name="lizard_map.search_coordinates"),
    url(r'^search_name/',
        'lizard_map.views.search_name',
        name="lizard_map.search_name"),

    # Export.
    url(r'^adapter/export/csv/',
        'lizard_map.views.export_identifier_csv',
        name="lizard_map.export_identifier_csv"),
    url(r'^snippet_group/(?P<snippet_group_id>\d+)/statistics/csv/',
        'lizard_map.views.export_snippet_group_statistics_csv',
        name="lizard_map.export_snippet_group_statistics_csv"),
    url(r'^snippet_group/(?P<snippet_group_id>\d+)/csv/',
        'lizard_map.views.export_snippet_group_csv',
        name="lizard_map.export_snippet_group_csv"),
    )


if settings.DEBUG:  # Pragma: no cover
    urlpatterns += patterns(
        '',
        (r'^admin/', include(admin.site.urls)),
        (r'', include('staticfiles.urls')),
        # Demo map stuff.
        (r'^$', 'django.views.generic.simple.direct_to_template',
         {'template': 'lizard_map/example_openlayers.html'}),
        (r'^example_wms/$', 'django.views.generic.simple.direct_to_template',
         {'template': 'lizard_map/example_wms.html'}),
    )
