from django import template

from lizard_map.models import Workspace

register = template.Library()


@register.inclusion_tag("lizard_map/tag_workspace_debug.html",
                        takes_context=True)
def workspace_debug_info(context):
    """Display debug info on workspaces."""
    workspaces = Workspace.objects.all()
    return {'workspaces': workspaces}


@register.inclusion_tag("lizard_map/tag_workspace.html")
def workspace(workspace, show_new_workspace=True):
    """Display workspace."""
    return {
        'workspace': workspace,
        'show_new_workspace': show_new_workspace
        }


@register.inclusion_tag("lizard_map/tag_workspace_drag_and_drop.html")
def workspace_drag_and_drop(workspaces):
    """inserts javascript for workspaces"""
    return {'workspaces': workspaces}
