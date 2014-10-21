import os
import json
import logging

from django.conf import settings
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from lizard_map.adapter import adapter_serialize
from lizard_map.fields import Color
from lizard_map.models import ICON_ORIGINALS
from lizard_map.models import Legend
from lizard_map.symbol_manager import SymbolManager

logger = logging.getLogger(__name__)

# The colors that are used in graphs
COLORS_DEFAULT = [
    {'mapnik': 'blue', 'display_name': _('blue')},
    {'mapnik': 'darkred', 'display_name': _('darkred')},
    {'mapnik': 'green', 'display_name': _('green')},
    {'mapnik': 'black', 'display_name': _('black')},
    {'mapnik': 'cyan', 'display_name': _('cyan')},
    #{'mapnik': 'yellow', 'display_name': _('yellow')},
    {'mapnik': 'orangered', 'display_name': _('orangered')},
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
    support_flot_graph = False
    # ^^^ Set this once flot graphs are supported by the adapter.

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

    @property
    def adapter_layer_json(self):
        """Returns the adapter's layer_arguments as a JSON string.

        This JSON string should be similar to the string that was
        used to make the layer_arguments in the first place."""

        return json.dumps(self.layer_arguments)

    def layer(self, layer_ids=None, request=None):
        """Generates and returns layers, styles.

        Layers is a list of mapnik layers.

        Styles is a list of mapnik styles (which are used in the
        layers).
        """
        raise NotImplementedError

    @classmethod
    def identifiers(self):
        """
        New in L3. Retrieve a list of all possible identifiers.

        This function is optional. It is used with REST APIs.

        Identifiers are dictionaries with for each adapter its custom
        keys and values. The meaning is only useful within a single
        adapter.
        """
        raise NotImplementedError

    def extent(self, identifiers=None):
        """
        Returns extent {'west':.., 'north':.., 'east':.., 'south':..}
        in google projection. None for each key means unknown.
        Optional function. If available, there will be an magnifier in
        your workspace -> workspace-item.

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
        'object': <object>,
       ['grouping_hint': ... ] (optional)
        } of closest fews point that matches x, y, radius.

        Required: distance, name, workspace_item, google_coords
        Highly recommended (else some functions will not work):
        identifier (for popups)

        If 'grouping_hint' is given, that is used to group items,
        otherwise the workspace_item.id. This way a single workspace
        item can have things show up in different tabs. Don't use
        grouping_hints that can possibly come from other workspace
        items (use the workspace item id as part of the
        grouping_hint), unless you know what you are doing.
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

    def location(self, layout=None, **identifier):
        """
        Returns information about an object in this layer. The name is
        historical; if the layer we are working with comes from FEWS,
        then the layer is defined by a filter and a parameter, while
        the objects within that layer are known as locations.

        The object's identifier dict will be used as **argument to
        this function, so if your layer's identifiers are dicts with
        keys 'A' and 'B', your layer's location() function will get
        passed keyword arguments A and B. Change the function's
        signature in your own layer to reflect that, or use a
        '**identifier' argument as above.

        The argument 'layout' is sometimes passed; it is a hack to
        pass some layout options to places where the result of this
        function is used, and it should be factored out (see below).

        The result of this function should be a dict with some of the
        following elements that are used to describe the object (only
        'name' is definitely used):

        'google_coords': an (x, y) tuple with this identifier's Google
                         coordinates (optional? possibly unused)

        'name': A descriptive name for the object. Definitely used.

        'shortname': A descriptive name for the object (optional? is
                     this used?)

        'workspace_item': self.workspace_item. Superfluous, it is
                          possible that this is still used but in that
                          case it should be factored out.

        'identifier': An identifier in the exact same format as was
                      used to call this function, except for two
                      optional extra keys:

                      - if a 'layout' argument was given to this
                        function, identifier['layout'] should be set
                        to that argument's value. Also superfluous,
                        also unknown whether it is still used.

                      - 'grouping_hint': Optional. Normally objects
                        with the same workspace_item are shown in the
                        same tab on the collage page. If you want to
                        split objects into several different pages,
                        give them different
                        identifier['grouping_hint'] s.

        'object': The object referred to by the identifier. Probably
                  unused.

        One of the things that definitely uses this is the javascript
        hover popup function.
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

        The 'snippet_group' kwarg is not used anymore, but exists for
        backward compatibility. If settings.DEBUG is True, using this
        causes a warning.

        Use this function if html function behaviour is default:
        def html(self, identifiers):
            return super(WorkspaceItemAdapterKrw, self).html_default(
                identifiers)
        """
        if snippet_group is not None and settings.DEBUG:
            logger.warn('kwarg "snippet_group" supplied to html_default ' +
                        'even though it is not used anymore.')

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
        else:
            title = self.workspace_mixin_item.name

        # Build "adapter-image" url for current adapter and identifiers.
        image_graph_url = self.workspace_mixin_item.url(
            "lizard_map_adapter_image", identifiers)
        flot_graph_data_url = self.workspace_mixin_item.url(
            "lizard_map_adapter_flot_graph_data", identifiers)

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
            'image_graph_url': image_graph_url,
            'flot_graph_data_url': flot_graph_data_url,
            'symbol_url': self.symbol_url(),
            'collage_item_props': collage_item_props,
            'adapter': self,
            }

        if layout_options is not None:
            render_kwargs.update(layout_options)

        if extra_render_kwargs is not None:
            render_kwargs.update(extra_render_kwargs)

        # request context is needed for accessing request related tags and
        # context variables when rendering the template. Get request instance
        # from layout_options, otherwise set context_instance to None.
        context_instance = None
        if layout_options:
            request = layout_options.get('request')
            if request:
                context_instance = RequestContext(request)

        return render_to_string(
            template,
            render_kwargs,
            context_instance=context_instance
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
                        "Now using fallback (red).", legend_name)
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

    def metadata(self):
        """Return key/value metadata.

        The goal: return metadata like "Created in: 1972" and "Copyright:
        Reinout". The metadata is returned as a list (or tuple) of two-item
        tuples, so ``[['Created in', '1972'], [...]]``.

        """
        pass

    def collage_detail_data_description(self, identifier, *args, **kwargs):
        """Return the title to show over this bit of data on the
        collage detail page."""

        return 'Grafiek'

    def collage_detail_edit_action(self, identifier, *args, **kwargs):
        """On the collage detail page, we can show edit options below
        a graph. Return 'graph' if this item does. Override to return
        "None" if it doesn't."""

        return 'graph'

    def collage_detail_show_edit_block(self, identifier, *args, **kwargs):
        return True

    def collage_detail_show_statistics_block(self, identifier,
                                             *args, **kwargs):
        return True
