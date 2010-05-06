from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^workspace/(?P<workspace_id>\d+)/wms/',
        'lizard_map.views.wms',
        name="lizard_map_wms"),
    url(r'^workspace/(?P<workspace_id>\d+)/',
        'lizard_map.views.workspace',
        name="lizard_map_workspace"),
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
