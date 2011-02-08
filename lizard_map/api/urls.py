from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from lizard_map.api.handlers import MapPluginsHandler


auth = HttpBasicAuthentication(realm="Fews jdbc")
ad = { 'authentication': auth }

map_plugins_handler = Resource(MapPluginsHandler, **ad)

urlpatterns = patterns(
    '',
    # url(r'^/(?P<plugin_name>[^/]+)/$', 
    #     map_plugins_handler, 
    #     name='api_map_plugin'),
    url(r'^$', 
        map_plugins_handler, 
        name='api_map_plugins'),
    )

