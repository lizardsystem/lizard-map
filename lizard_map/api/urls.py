from django.conf.urls import patterns
from django.conf.urls import url
from piston.resource import Resource

from lizard_map.api.handlers import MapPluginsHandler


map_plugins_handler = Resource(MapPluginsHandler)

urlpatterns = patterns(
    '',
    # url(r'^/(?P<plugin_name>[^/]+)/$',
    #     map_plugins_handler,
    #     name='api_map_plugin'),
    url(r'^$',
        map_plugins_handler,
        name='api_map_plugins'),
    )
