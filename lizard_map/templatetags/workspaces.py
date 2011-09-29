from django import template
from django.utils import simplejson as json

from lizard_map.daterange import current_start_end_dates
#from lizard_map.models import Workspace
from lizard_map.utility import float_to_string
from lizard_map.views import CUSTOM_LEGENDS

register = template.Library()


# @register.inclusion_tag("lizard_map/tag_workspace_debug.html",
#                         takes_context=True)
# def workspace_debug_info(context):
#     """Display debug info on workspaces."""
#     workspaces = Workspace.objects.all()
#     return {'workspaces': workspaces}


# @register.inclusion_tag("lizard_map/tag_workspace.html",
#                         takes_context=True)
# def workspace(context, workspace, show_new_workspace=False):
#     """Display workspace."""
#     if 'request' in context:
#         session = context['request'].session
#     else:
#         session = None
#     return {
#         'workspace': workspace,
#         'date_range_form': context.get('date_range_form', None),
#         'show_new_workspace': show_new_workspace,
#         'session': session}


# L3
@register.inclusion_tag("lizard_map/tag_workspace_edit.html",
                        takes_context=True)
def workspace_edit(context, workspace_edit):
    """Display workspace_edit"""
    if 'request' in context:
        session = context['request'].session
        user = context['user']
    else:
        session = None
        user = None
    return {
        'workspace_edit': workspace_edit,
        'session': session,
        'user': user}


# L3
@register.inclusion_tag("lizard_map/tag_collage_edit.html",
                        takes_context=True)
def collage_edit(context, collage_edit):
    """Display collage_edit"""
    return {
        'collage_edit': collage_edit}


# L3
@register.inclusion_tag("lizard_map/tag_statistics.html")
def collage_item_statistics(request, collage_items):
    if not collage_items:
        return {}
    start_date, end_date = current_start_end_dates(request)
    statistics = []
    for collage_item in collage_items:
        statistics.extend(collage_item.statistics(start_date, end_date))
    return {'statistics': statistics}


@register.simple_tag
def collage_items_html(collage_items, is_collage=False):
    """
    Generate single html for multiple collage items.
    """
    if not collage_items:
        return ""
    identifiers = [collage_item.identifier for collage_item in collage_items]
    return collage_items[0].html(identifiers, is_collage)


@register.inclusion_tag("lizard_map/tag_table.html")
def snippet_group_table(request, snippet_group):
    """
    Renders table for snippet_group.
    """
    start_date, end_date = current_start_end_dates(request)
    values_table = snippet_group.values_table(start_date, end_date)
    if len(values_table) > 1:
        table = values_table[1:]
    else:
        table = []
    head = [value.replace('_', ' ') for value in values_table[0]]

    return {'table': table, 'head': head}


@register.filter
def json_escaped(value):
    """converts an object to json and escape quotes
    """
    # TODO: just use one of the available url encoders!
    return json.dumps(value).replace('"', '%22').replace(' ', '%20')


@register.filter
def float_or_exp(value):
    """Show number with 2 decimals or with an exponent if too small."""
    return float_to_string(value)


@register.inclusion_tag("lizard_map/tag_legend.html")
def legend(name, adapter, session=None):
    """Shows legend. Optionally updates legend with
    session['custom_legends'], if it exists.

    session['custom_legends'][<name>] = <updates>

    where updates looks like:

    {'min_value': <min_value>,
     'max_value': <max_value>,
     ... (see Legend.update)
     }

    """

    updates = None
    if session:
        custom_legends = session.get(CUSTOM_LEGENDS, {})
        custom_legend = custom_legends.get(name, {})
        if custom_legend:
            updates = custom_legend
    return {
        'allow_custom_legend': adapter.allow_custom_legend,
        'legend': adapter.legend(updates=updates),
        'name': name,
        'idhash': hash(name),
        'custom_legend': updates}
