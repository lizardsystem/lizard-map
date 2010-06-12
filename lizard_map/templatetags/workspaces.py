from django import template
from django.shortcuts import get_object_or_404

from lizard_map.models import Workspace
from lizard_map.models import WorkspaceItem
from lizard_map.models import WorkspaceCollage

register = template.Library()


@register.inclusion_tag("lizard_map/tag_workspace_debug.html",
                        takes_context=True)
def workspace_debug_info(context):
    """Display debug info on workspaces."""
    workspaces = Workspace.objects.all()
    return {'workspaces': workspaces}


@register.inclusion_tag("lizard_map/tag_workspace.html",
                        takes_context=True)
def workspace(context, workspace, show_new_workspace=False):
    """Display workspace."""
    return {
        'workspace': workspace,
        'date_range_form': context.get('date_range_form', None),
        'show_new_workspace': show_new_workspace,
        }


@register.inclusion_tag("lizard_map/tag_collage.html")
def collage(collage_id):
    """
    Displays a collage: for each workspace_item a graph is displayed
    with all corresponding snippets in it
    """
    collage = get_object_or_404(WorkspaceCollage, pk=collage_id)
    workspace_items = WorkspaceItem.objects.filter(
        workspacecollagesnippet__in=collage.snippets.all()).distinct()
    return {
        'collage': collage,
        'workspace_items': workspace_items,
        }


@register.inclusion_tag("lizard_map/tag_workspace_drag_and_drop.html")
def workspace_drag_and_drop(workspaces):
    """inserts javascript for workspaces"""
    return {'workspaces': workspaces}
