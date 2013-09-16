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

    template_name = 'lizard_map/workspace_acceptable.html'

    def __init__(self,
                 name=None,
                 adapter_name=None,
                 adapter_layer_json=None,
                 description=None,
                 enabled=True):
        self.name = name
        self.adapter_name = adapter_name
        self.adapter_layer_json = adapter_layer_json
        self.description = description
        self.enabled = enabled

    def classes(self):
        """Return applicable css classes. Saves some if/else in the template.
        """
        result = ['padded-sidebar-item']
        if self.enabled:
            result.append('workspace-acceptable')
        else:
            result.append('nonworking-workspace-acceptable')
        if self.description:
            result.append('with_description')
        return ' '.join(result)

    def to_html(self):
        template = loader.get_template(self.template_name)
        context = Context({'acceptable': self,
                           'classes': self.classes()})
        return mark_safe(template.render(context))

    def html_tag(self):
        """Return tag name. 'a' when enabled, 'div' when not."""
        if self.enabled:
            return 'a'
        return 'div'

    def is_animatable(self):
        """Obsolete method which previously indicated whether a layer
        was animatable"""
        return False


class Legend(object):
    """Wrapper/interface for legends.

    This is used for documentation, to define an interface and to generate
    the html.

    To change the html used to render a workspace acceptable, redefine
    ``template`` or lizard_map/workspace_acceptable.html.

    - **name**: name of the legend.

    - **image_url**: url of the legend image.


    """

    template_name = 'lizard_map/legend_item.html'
    name = None
    subitems = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError("Argument %s cannot be set." % key)

    def to_html(self):
        template = loader.get_template(self.template_name)
        context = Context({'legend': self})
        return mark_safe(template.render(context))
