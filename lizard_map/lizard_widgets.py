"""Lizard Widgets"""

from django.utils.safestring import mark_safe
from django.template import Context, loader


class WorkspaceAcceptable(object):
    """Wrapper/Interface for WorkspaceAcceptable items and html generation.

    This is used for documentation, to define an interface and to generate
    the html.

    To change the html used to render a workspace acceptable, redefine
    ``template`` or lizard_map/workspace_acceptable.html.

    - **name**: name of the workspace acceptable.

    - **adapter_name**: name of the adapter.

    - **adapter_layer_json**: json for the adapter layer.

    - **description**: optional description for the workspace acceptable.

    """

    template = 'lizard_map/workspace_acceptable.html'

    def __init__(self, name, adapter_name, adapter_layer_json,
                 description=None):
        self.name = name
        self.adapter_name = adapter_name
        self.adapter_layer_json = adapter_layer_json
        self.description = description

    def to_html(self):
        template = loader.get_template(self.template)
        context = Context({'acceptable': self})
        return mark_safe(template.render(context))
