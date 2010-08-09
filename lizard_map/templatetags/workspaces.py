from django import template
import simplejson as json

from lizard_map.models import Workspace

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
def snippet_group(snippet_group, add_snippet=None, editing=None, detailed=None):
    """
    Renders snippet_group.  All snippets MUST be using the same
    workspace_item, or output is undefined.

    add_snippet and editing are strings that are 'True' or 'False'

    TODO: make snippets of the same adapter compatible (instead of
    workspace_item)
    """
    snippets = snippet_group.snippets.all()
    identifiers = [snippet.identifier for snippet in snippets]
    if snippets:
        workspace_item = snippets[0].workspace_item
        return workspace_item.adapter.html(
            identifiers,
            layout_options={'add_snippet': add_snippet=='True',
                            'editing': editing=='True',
                            'detailed': detailed=='True'}
            )
    else:
        return 'empty snippet_group (should never happen)'


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
