from django import template

from lizard_map.models import Workspace

register = template.Library()


@register.inclusion_tag("lizard_map/tag_workspace_debug.html",
                        takes_context=True)
def workspace_debug_info(context):
    """Display debug info on workspaces."""
    workspaces = Workspace.objects.all()
    return {'workspaces': workspaces}
