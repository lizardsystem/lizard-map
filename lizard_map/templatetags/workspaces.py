from django import template
from django.shortcuts import get_object_or_404
import simplejson as json

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


@register.simple_tag
def collage_workspace_item(collage, workspace_item):
    """
    Renders a collage/workspace_item combination.
    """
    snippets = collage.snippets.filter(workspace_item=workspace_item)
    identifiers = [snippet.identifier for snippet in snippets]
    return workspace_item.adapter.html(identifiers)


@register.filter
def json_escaped(value):
    """converts an object to json and escape quotes
    """
    return json.dumps(value).replace('"', '%22')


@register.inclusion_tag("lizard_map/tag_date_popup.html",
                        takes_context=True)
def date_popup(context):
    """Displays date popup"""
    return {
        'date_range_form': context.get('date_range_form', None),
        }
