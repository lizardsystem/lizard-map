from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns(
    '',

    # Actions/services on/from workspaces
    url(r'^workspace/(?P<workspace_id>\d+)/wms/',
        'lizard_map.views.wms',
        name="lizard_map_wms"),
    url(r'^workspace/(?P<workspace_id>\d+)/clickinfo/',
        'lizard_map.views.clickinfo',
        name="lizard_map_clickinfo"),
    url(r'^workspace/(?P<workspace_id>\d+)/workspace_items/reorder/',
        'lizard_map.views.workspace_item_reorder',
        name="lizard_map_workspace_item_reorder"),
    url(r'^workspace/(?P<workspace_id>\d+)/workspace_items/add/',
        'lizard_map.views.workspace_item_add',
        name="lizard_map_workspace_item_add"),
    url(r'^workspace/(?P<workspace_id>\d+)/',
        'lizard_map.views.workspace',
        name="lizard_map_workspace"),


    # Partially the same actions as above,
    # you have to put workspace_id in GET parameter here...
    url(r'^workspaceitemreorder/',
        'lizard_map.views.workspace_item_reorder',
        name="lizard_map_workspace_item_reorder"),
    url(r'^workspaceitemadd/',
        'lizard_map.views.workspace_item_add',
        name="lizard_map_workspace_item_add"),

    # Actions on your session workspace - the system looks for the right workspace
    url(r'^session_workspace/',
        'lizard_map.views.session_workspace_edit_item',
        {'workspace_category': 'temp'},
        name="lizard_map_session_workspace_add_item_temp"),

    # Actions/services on session collages
    url(r'^session_collage/',
        'lizard_map.views.session_collage_snippet_add',
        name="lizard_map_session_collage_snippet_add"),

    # Actions on workspace items
    url(r'^workspaceitem/(?P<workspace_item_id>\d+)/delete/',
        'lizard_map.views.workspace_item_delete',
        name="lizard_map_workspace_item_delete"),
    url(r'^workspaceitem/delete/',
        'lizard_map.views.workspace_item_delete',
        name="lizard_map_workspace_item_delete"),
    url(r'^workspaceitem/edit/',
        'lizard_map.views.workspace_item_edit',
        name="lizard_map_workspace_item_edit"),
    )


if settings.DEBUG:
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
