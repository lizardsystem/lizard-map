import os
import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from lizard_map.adapter import adapter_serialize
from lizard_map.models import ICON_ORIGINALS
from lizard_map.models import Color
from lizard_map.models import Legend
#from lizard_map.models import Workspace foo
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

    def __init__(self, workspace_item, layer_arguments=None,
                 adapter_class=None):
        self.workspace_mixin_item = workspace_item
        self.workspace_item = workspace_item  # For backwards compatibility

        if layer_arguments is not None:
            self.layer_arguments = layer_arguments
        else:
            self.layer_arguments = {}
        self.adapter_class = adapter_class

        # All arguments, for passing through
        self.layer_arguments = layer_arguments

    def layer(self, layer_ids=None, request=None):
        """Generates and returns layers, styles.

        Layers is a list of mapnik layers.

        Styles is a list of mapnik styles (which are used in the
        layers).
        """
        raise NotImplementedError

    # def extent(self, identifiers=None):
    #     """
    #     Returns extent {'west':.., 'north':.., 'east':.., 'south':..}
    #     in google projection. None for each key means unknown.

    #     Optional function. If available, there will be an magnifier
    #     in your workspace -> workspace-item.

    #     Optional: If identifiers is given, return extent for those
    #     identifiers only.
    #     """
    #     return {'north': None, 'south': None, 'east': None, 'west': None}

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
                         'editing': False,
                         'request': request}
        """
        return 'html output for this adapter is not implemented'

    def html_default(self, snippet_group=None, identifiers=None,
                     layout_options=None,
                     template=None, extra_render_kwargs=None):
        """
        Default implementation for html view ("popup"). It returns an
        html snippet with links in it.

        Not all kwargs are still used, but they exist for backwards
        compatibility.

        Use this function if html function behaviour is default:
        def html(self, identifiers):
            return super(WorkspaceItemAdapterKrw, self).html_default(
                identifiers)
        """
        if template is None:
            template = 'lizard_map/html_default.html'

        is_collage = False
        if layout_options is not None:
            if 'is_collage' in layout_options:
                is_collage = layout_options['is_collage']

        # Fetch name
        if identifiers:
            identifier_str = {}
            for k, v in identifiers[0].items():
                identifier_str[str(k)] = v
            location = self.location(**identifier_str)
            title = location['name']
            if len(identifiers) > 1:
                title += ' + ...'
        else:
            title = self.workspace_mixin_item.name

        # Build "adapter-image" url for current adapter and identifiers.
        img_url = self.workspace_mixin_item.url(
            "lizard_map_adapter_image", identifiers)

        # Makes it possible to create collage items from current
        # selected objects.
        collage_item_props = []
        # No export and selection for collages.
        if not is_collage:
            for identifier in identifiers:
                identifier_str = {}
                for k, v in identifier.items():
                    identifier_str[str(k)] = v
                location = self.location(**identifier_str)
                collage_item_props.append(
                    {'name': location['name'],
                     'adapter_class': self.workspace_mixin_item.adapter_class,
                     'adapter_layer_json':
                         self.workspace_mixin_item.adapter_layer_json,
                     'identifier': adapter_serialize(identifier),
                     'url': self.workspace_mixin_item.url(
                            "lizard_map_adapter_values", [identifier, ],
                            extra_kwargs={'output_type': 'csv'})})

        render_kwargs = {
            'title': title,
            'img_url': img_url,
            'symbol_url': self.symbol_url(),
            'collage_item_props': collage_item_props}
        if layout_options is not None:
            render_kwargs.update(layout_options)

        return render_to_string(
            template,
            render_kwargs)

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
                        "Now using fallback (red)." % legend_name)
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
