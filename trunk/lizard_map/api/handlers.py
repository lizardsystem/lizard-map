# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
import pkg_resources
from django.core.urlresolvers import reverse
from piston.handler import BaseHandler
from piston.doc import generate_doc

from lizard_map.models import ADAPTER_ENTRY_POINT


def documentation(handler):
    """Return dict with documentation on handler.

    Intended for injection into the handler's answer.
    """
    result = {}
    doc = generate_doc(handler)
    result['name'] = doc.name
    result['description'] = doc.doc
    return result


class MapPluginsHandler(BaseHandler):
    """List of available lizard-map plugins."""
    allowed_methods = ('GET', )
    # model = Blogpost

    def read(self, request):
        """Return list of available REST-api capable lizard-map plugins.

        REST-api capability is detected by looking for an
        ``plugin_api_url_name`` attribute on the adapter.  If
        available, it should point at a named url that provides
        information on the plugin's api capabilities.

        """
        result = {}
        result['info'] = documentation(self.__class__)

        entrypoints = pkg_resources.iter_entry_points(
            group=ADAPTER_ENTRY_POINT)
        data = []
        for entrypoint in entrypoints:
            adapter = entrypoint.load()
            if not hasattr(adapter, 'plugin_api_url_name'):
                continue
            url = request.build_absolute_uri(
                reverse(adapter.plugin_api_url_name))
            plugin_info = {'name': entrypoint.name,
                           'url': url}
            data.append(plugin_info)
        result['data'] = data
        return result
