import os
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils import simplejson as json
from django.utils.translation import ugettext as _

from lizard_map.models import DEFAULT_WORKSPACES
from lizard_map.models import ICON_ORIGINALS
from lizard_map.models import TEMP_WORKSPACES
from lizard_map.models import USER_WORKSPACES
from lizard_map.models import Color
from lizard_map.models import Legend
from lizard_map.models import Workspace
from lizard_map.symbol_manager import SymbolManager

logger = logging.getLogger('lizard_map.workspace')

# The colors that are used in graphs
COLORS_DEFAULT = [
    {'mapnik': 'blue', 'display_name': _('blue')},
    {'mapnik': 'magenta', 'display_name': _('magenta')},
    {'mapnik': 'yellow', 'display_name': _('yellow')},
    {'mapnik': 'black', 'display_name': _('black')},
    {'mapnik': 'cyan', 'display_name': _('cyan')},
    {'mapnik': 'red', 'display_name': _('red')},
    {'mapnik': 'lightblue', 'display_name': _('lightblue')},
    {'mapnik': 'grey', 'display_name': _('grey')},
    ]


class WorkspaceManager:

    def __init__(self, request):
        self.request = request
        self.workspaces = {}

    def save_workspaces(self):
        """save workspaces to session"""
        workspace_group_ids = {}
        for group, workspace_list in self.workspaces.items():
            workspace_group_ids[group] = [workspace.id for workspace in
                                          workspace_list]
        self.request.session['workspaces'] = workspace_group_ids
        logger.debug('WorkspaceManager.save_workspaces: saved '
                     'workspace_group_ids in session.')

    def load_workspaces(self, workspace_group_ids=None):
        """load workspaces from session

        note: request.session['workspaces'] must be filled before
        using this function

        returns number of workspaces that could not be loaded"""
        errors = 0
        if workspace_group_ids is None:
            if 'workspaces' in self.request.session:
                workspace_group_ids = self.request.session['workspaces']
            else:
                logger.warn(('WorkspaceManager.load_workspaces: no workspaces'
                             ' in kwargs or in session.'))
                return 1
        # Workspaces are grouped by key TEMP_WORKSPACES, USER_WORKSPACES, etc.
        for group, workspace_ids in workspace_group_ids.items():
            self.workspaces[group] = []
            for workspace_id in workspace_ids:
                try:
                    new_workspace = Workspace.objects.get(pk=workspace_id)
                    self.workspaces[group].append(new_workspace)
                except Workspace.DoesNotExist:
                    errors += 1
        return errors

    def empty(self, category=TEMP_WORKSPACES):
        #clear all items in workspace category
        for workspace in self.workspaces[category]:
            workspace.workspace_items.all().delete()

    def load_or_create(self, new_workspace=False):
        """load workspaces references by session['workspaces'] or
        create new workspace (saves in case of changes to workspaces)

        workspaces are returned in a dictionary:
        {
        'default': [...default layers],
        'temp': workspace_temp,
        'user': [...user workspaces]
        }

        they are stored in the session as a dictionary of ids:
        {
        'default': [id1, id2, ...],
        'temp': [id, ],
        'user': [id3, id4, ...],
        }
        """

        self.workspaces = {}
        changes = False
        if 'workspaces' in self.request.session:
            changes = self.load_workspaces()

        #check if components exist, else create them
        if not DEFAULT_WORKSPACES in self.workspaces:
            try:
                self.workspaces[DEFAULT_WORKSPACES] = [
                    Workspace.objects.get(name='achtergrond')]
                # ^^^ TODO: use non-Dutch name.
            except Workspace.DoesNotExist:
                pass
            changes = True

        if (not TEMP_WORKSPACES in self.workspaces or
            not self.workspaces[TEMP_WORKSPACES]):
            workspace_temp = Workspace(name=TEMP_WORKSPACES)
            workspace_temp.save()
            self.workspaces[TEMP_WORKSPACES] = [workspace_temp]
            changes = True

        if (new_workspace or
            not USER_WORKSPACES in self.workspaces or
            not len(self.workspaces[USER_WORKSPACES])):
            workspace_user = Workspace()
            workspace_user.save()
            self.workspaces[USER_WORKSPACES] = [workspace_user]
            changes = True

        #create collage if necessary, it is stored in the workspace
        if len(self.workspaces[USER_WORKSPACES][0].collages.all()) == 0:
            self.workspaces[USER_WORKSPACES][0].collages.create()

        if changes:
            self.save_workspaces()
        return self.workspaces


class WorkspaceItemAdapter(object):
    """Base class for workspace_item adapters.

    Lizard-map needs to display workspace items.  Search in them according to
    clicks on the map.  And so on.  But workspace items can be anything.  An
    *adapter* adapts a workspace item to what lizard-map needs.

    So for every new kind of workspace item, you'll need a fresh adapter that
    subclasses this base adapter.  And you'll need to implement the
    NotImplementedError'ed methods.

    """

    layer_arguments = {}
    is_animatable = False
    allow_custom_legend = False

    def __init__(self, workspace_item, layer_arguments=None):
        self.workspace_item = workspace_item
        if layer_arguments is not None:
            self.layer_arguments = layer_arguments
        else:
            self.layer_arguments = {}

    def layer(self, layer_ids=None, request=None):
        """Generates and returns layers, styles.

        Layers is a list of mapnik layers.

        Styles is a list of mapnik styles (which are used in the
        layers).
        """
        raise NotImplementedError

    def extent(self, identifiers=None):
        """
        Returns extent {'west':.., 'north':.., 'east':.., 'south':..}
        in google projection. None for each key means unknown.

        Optional: If identifiers is given, return extent for those
        identifiers only.
        """
        return {'north': None, 'south': None, 'east': None, 'west': None}

    def search(self, x, y, radius=None):
        """Search by coordinates. Return list of dicts for matching
        items.

        {'distance': <float>,
        'name': <name>,
        'shortname': <short name>,
        'workspace_item': <...>,
        'identifier': {...},
        'google_coords': (x, y) coordinate in google,
        'object': <object>} of closest fews point that matches x, y, radius.

        Required: distance, name, workspace_item, google_coords
        Highly recommended (else some functions will not work):
        identifier (for popups)
        """
        raise NotImplementedError

    def value_aggregate(self, identifier, aggregate_functions,
                        start_date=None, end_date=None):
        """
        Calculates aggregated values of identifier. Returns dict with
        aggregation function as key and value as value. {'avg': 3.5,
        'min': 1, 'max': 6}.

        The given functions in aggregate_functions will be calculated:

        aggregate_functions = {
        'avg': None,
        'min': None,
        'max': None,
        'count_lt': <boundary value>,
        'count_gte': <boundary value>,
        'percentile': <percentile>     # returns value of given percentile
        <custom function>: <custom input>  # for special aggregates,
                                           # such as average in part
                                           # of a grid
        }

        all functions are optional.

        """
        return {}

    def values(self, identifier, start_date, end_date):
        """Return values in list of dictionaries (datetime, value, unit)
        """
        raise NotImplementedError

    def value_aggregate_default(self, identifier, aggregate_functions,
                                start_date, end_date):
        """
        Default implementation for value_aggregate.
        """

        result = {}
        values = self.values(identifier, start_date, end_date)
        values_only = [value['value'] for value in values]
        values_only.sort()  # for percentile function
        for key, value in aggregate_functions.items():
            try:
                # Values are not always numbers - in case of strings
                # this will result in a TypeError
                # the sequence can be empty
                if key == 'min':
                    result_value = min(values_only)
                elif key == 'max':
                    result_value = max(values_only)
                elif key == 'avg':
                    result_value = float(sum(values_only)) / len(values_only)
                elif key == 'count_lt':
                    if value is None:
                        result_value = None
                    else:
                        result_value = 0
                        for v in values_only:
                            if v < value:  # value is boundary value
                                result_value += 1
                elif key == 'count_gte':
                    if value is None:
                        result_value = None
                    else:
                        result_value = 0
                        for v in values_only:
                            if v >= value:  # value is boundary value
                                result_value += 1
                elif key == 'percentile':
                    if value is None:
                        result_value = None
                    else:
                        rank = int(value * len(values_only) / 100.0 + 0.5)
                        result_value = values_only[rank]
                else:
                    result_value = None
            except (ValueError, IndexError, TypeError, ZeroDivisionError):
                result_value = None
            result[key] = result_value
        return result

    def location(self, identifier=None, layout=None):
        """Return fews point representation corresponding to filter_id,
        location_id and parameter_id in same format as search function

        layout is a dict with extra optional layout parameters:
        y_min, y_max, y_label, x_label, line_avg, line_max, line_min

        {'object': <...>,
        'google_x': x coordinate in google,
        'google_y': y coordinate in google,
        'workspace_item': <...>,
        'identifier': {...},
        'grouping_hint': optional unique group identifier, i.e. unit m3/s}

        """
        raise NotImplementedError

    def line_styles(self, identifiers):
        """
        Get line styles for given identifiers. For each set of
        identifiers, the line styles are calculated deterministic.

        EXPERIMENTAL: this function can be used to generate a legend
        function, seperately of the image function.

        Keys are str(identifiers). Values are dicts with properties
        'color', 'linestyle', 'linewidth', 'max_linestyle',
        'max_linewidth', 'min_linestyle', 'min_linewidth', ...
        """
        styles = {}
        for index, identifier in enumerate(identifiers):
            key = str(identifier)
            color = COLORS_DEFAULT[index % len(COLORS_DEFAULT)]
            style = {'linestyle': '-',
                     'linewidth': 3,
                     'color': color['mapnik'],
                     'max_linestyle': '--',
                     'max_linewidth': 2,
                     'min_linestyle': '--',
                     'min_linewidth': 2,
                     'avg_linestyle': '--',
                     'avg_linewidth': 2,
                     }  # default
            if 'layout' in identifier:
                layout = identifier['layout']
                if "color" in layout:
                    style['color'] = layout['color']
            styles[key] = style
        return styles

    def image(self, identifiers=None, start_date=None, end_date=None,
              width=None, height=None, layout_extra=None):
        """Return image of given parameters.

        layout_extra can have the following parameters (all are optional):

        'y_label' = value y_label
        'x_label' = value x_label
        'y_min' = value y_min
        'y_max' = value self.layout_y_max
        'title' = title
        'horizontal_lines' = [{
          'name': <line name>,
          'value': <value>,
          'style': {'linewidth': 3,
                    'linestyle': '--',
                    'color': 'green'}, }]
        'vertical_lines' = [{
          'name': <line name>,
          'value': <value (datetime)>,
          'style': {'linewidth': 3,
                    'linestyle': '--',
                    'color': 'green'}, }]
        """

        raise NotImplementedError

    def symbol_url(self, identifier=None, start_date=None, end_date=None,
                   icon_style=None):
        """Return symbol for identifier.

        Implementation: respect the fact when icon_style is already
        given. If it's empty, generate own icon if applicable.
        """
        sm = SymbolManager(ICON_ORIGINALS, os.path.join(
                settings.MEDIA_ROOT,
                'generated_icons'))
        if icon_style is None:
            icon_style = {'icon': 'empty.png'}
        output_filename = sm.get_symbol_transformed(icon_style['icon'],
                                                    **icon_style)
        return settings.MEDIA_URL + 'generated_icons/' + output_filename

    def html(self, snippet_group=None, identifiers=None, layout_options=None):
        """
        Html output for given identifiers. Optionally layout_options
        can be provided. Default layout_options:

        layout_options = {'add_snippet': False,
                         'editing': False}
        """
        return 'html output for this adapter is not implemented'

    def html_default(self, snippet_group=None, identifiers=None,
                     layout_options=None):
        """
        Returns html representation of given snippet_group OR
        identifiers (snippet_group has priority). If a snippet_group
        is provided, more options are available.

        This particular view always renders a list of items, then 1
        image

        Use this function if html function behaviour is default:
        def html(self, identifiers):
            return super(WorkspaceItemAdapterKrw, self).html_default(
                identifiers)
        """

        if layout_options is None:
            layout_options = {}
        add_snippet = layout_options.get('add_snippet', False)
        editing = layout_options.get('editing', False)
        legend = layout_options.get('legend', False)

        if snippet_group is not None:
            snippets = snippet_group.snippets.all()
            identifiers = [snippet.identifier for snippet in snippets]
            title = str(snippet_group)
        else:
            title = self.workspace_item.name

        # Image url: for snippet_group there is a special (dynamic) url.
        if snippet_group:
            # Image url for snippet_group: can change if snippet_group
            # properties are altered.
            img_url = reverse(
                "lizard_map.snippet_group_image",
                kwargs={'snippet_group_id': snippet_group.id},
                )
        else:
            # Image url: static url composed with all options and layout tweaks
            img_url = reverse(
                "lizard_map.workspace_item_image",
                kwargs={'workspace_item_id': self.workspace_item.id},
                )
            # If legend option: add legend to layout of identifiers
            if legend:
                for identifier in identifiers:
                    if not 'layout' in identifier:
                        identifier['layout'] = {}
                    identifier['layout']['legend'] = True

            identifiers_escaped = [json.dumps(identifier).replace('"', '%22')
                                   for identifier in identifiers]
            img_url = img_url + '?' + '&'.join(['identifier=%s' % i for i in
                                                identifiers_escaped])

        # Make 'display_group'
        display_group = [self.location(**identifier) for identifier in
                         identifiers]

        return render_to_string(
            'lizard_map/popup.html',
            {
                'title': title,
                'display_group': display_group,
                'img_url': img_url,
                'symbol_url': self.symbol_url(),
                'add_snippet': add_snippet,
                'editing': editing,
                'snippet_group': snippet_group,
                'colors': COLORS_DEFAULT,
                },
            )

    def legend(self, updates=None):
        """
        Returns legend in a list of dictionaries. If this method
        returns a list, then the legend icon will appear in your
        workspace.

        Dictionary = {'img_url': <url>, 'description': <description>}

        updates: ...

        """
        return []

    def legend_object_default(self, legend_name):
        """
        Get legend object. If no appropriate legend was found, a
        legend object will be created and returned.
        """
        found_legend = Legend.objects.find(legend_name)
        if found_legend is None:
            # Fallback if no legend found (should not happen)
            logger.warn("Could not find legend for key '%s', "
                        "please configure the legend. "
                        "Now using fallback (red).")
            color = Color('ff0000')
            found_legend = Legend(descriptor="", min_color=color,
                                  max_color=color, too_low_color=color,
                                  too_high_color=color)

        return found_legend

    def legend_default(self, legend_object):
        """Default implementation for legend. A legend is displayed
        when the method "legend" is implemented in the adapter.

        Use a fixed formula to calculate legend descriptor, and
        img_url. Generates image if needed."""

        icon_style_template = {'icon': 'empty.png',
                               'mask': ('empty_mask.png', ),
                               'color': (1, 1, 1, 1)}
        if legend_object is not None:
            float_format = legend_object.float_format
            legend_result = []

            # Add < min
            icon_style = icon_style_template.copy()
            icon_style.update({
                    'color': legend_object.too_low_color.to_tuple()})
            img_url = self.symbol_url(icon_style=icon_style)
            legend_result.append({'img_url': img_url,
                                  'description': (('< %s' % float_format) %
                                                  (legend_object.min_value))})

            # Add range
            for legend_item in legend_object.legend_values():
                color = legend_item['color']
                icon_style = icon_style_template.copy()
                icon_style.update({'color': color.to_tuple()})
                img_url = self.symbol_url(icon_style=icon_style)
                legend_row = {'img_url': img_url,
                              'description': (
                        ('%s - %s' % (float_format, float_format)) %
                        (legend_item['low_value'],
                         legend_item['high_value']))}

                legend_result.append(legend_row)

            # Add > max
            icon_style = icon_style_template.copy()
            icon_style.update({
                    'color': legend_object.too_high_color.to_tuple()})
            img_url = self.symbol_url(icon_style=icon_style)
            legend_result.append({'img_url': img_url,
                                  'description': (('> %s' % float_format) %
                                                  (legend_object.max_value))})

        else:
            legend_result = [{'img_url': self.symbol_url(),
                              'description': 'description'}]
        return legend_result
