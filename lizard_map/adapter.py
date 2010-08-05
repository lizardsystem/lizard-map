"""
Helper classes and functions for adapters
"""
import datetime

from dateutil.relativedelta import relativedelta
from dateutil.rrule import YEARLY, MONTHLY, DAILY, HOURLY, MINUTELY, SECONDLY
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.dates import AutoDateFormatter
from matplotlib.dates import AutoDateLocator
from matplotlib.dates import RRuleLocator
from matplotlib.dates import date2num
from matplotlib.dates import rrulewrapper
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from django.core.urlresolvers import reverse
from django.http import HttpResponse
import simplejson as json

from lizard_map.matplotlib_settings import FONT_SIZE
from lizard_map.matplotlib_settings import SCREEN_DPI

LEGEND_WIDTH = 200
LEFT_LABEL_WIDTH = 100
BOTTOM_LINE_HEIGHT = FONT_SIZE * 1.5


def _inches_from_pixels(pixels):
    """Return size in inches for matplotlib's benefit"""
    return pixels / SCREEN_DPI


def workspace_item_image_url(workspace_item_id, identifiers,
                             strip_layout=False, session_graph_options=False):
    """
    Returns image url

    Identifiers is a list of dicts
    """
    identifiers_copy = identifiers[:]
    if strip_layout:
        for identifier in identifiers_copy:
            if 'layout' in identifier:
                del identifier['layout']
    identifier_json_list = [json.dumps(identifier).replace('"', '%22') for \
                                identifier in identifiers_copy]
    if session_graph_options:
        img_url = reverse(
            "lizard_map.workspace_item_image_session_graph_options",
            kwargs={'workspace_item_id': workspace_item_id, })
    else:
        img_url = reverse(
            "lizard_map.workspace_item_image",
            kwargs={'workspace_item_id': workspace_item_id, })
    img_url = img_url + '?' + '&'.join(['identifier=%s' % i for i in
                                        identifier_json_list])
    return img_url


class GraphProps(object):
    """Keep track of graph properties in a dict.

    Can be used to load and safe in session

    properties = {'<hash of workspace_item and identifier>': {graph
    properties}, ...}

    """
    def __init__(self, properties=None):
        if properties is None:
            self.properties = {}
        else:
            self.properties = properties

    def hash_string(self, workspace_item_id, identifier):
        """make unique string of workspace_item and identifier
        ignores layout properties
        """
        identifier_copy = identifier.copy()
        if 'layout' in identifier_copy:
            del identifier_copy['layout']
        return '%s::%s' % (workspace_item_id, json.dumps(identifier_copy))

    def set(self, workspace_item, identifier, graph_props):
        """sets graph properties for given workspace_item and identifier
        """
        hash_string = self.hash_string(workspace_item, identifier)
        self.properties[hash_string] = graph_props

    def delete(self, workspace_item, identifier):
        """delete graph properties for given workspace_item and identifier
        """
        hash_string = self.hash_string(workspace_item, identifier)
        if hash_string in self.properties:
            del self.properties[hash_string]

    def get(self, workspace_item, identifier):
        """gets graph properties for given workspace_item and identifier
        return {} if not available
        """
        hash_string = self.hash_string(workspace_item, identifier)
        return self.properties.get(hash_string, {})


class LessTicksAutoDateLocator(AutoDateLocator):
    """Similar to matplotlib.date.AutoDateLocator, but with less ticks."""

    def __init__(self, tz=None, max_ticks=5):
        AutoDateLocator.__init__(self, tz)
        self.max_ticks = max_ticks

    def get_locator(self, dmin, dmax):
        'Pick the best locator based on a distance.'

        delta = relativedelta(dmax, dmin)

        numYears = (delta.years * 1.0)
        numMonths = (numYears * 12.0) + delta.months
        numDays = (numMonths * 31.0) + delta.days
        numHours = (numDays * 24.0) + delta.hours
        numMinutes = (numHours * 60.0) + delta.minutes
        numSeconds = (numMinutes * 60.0) + delta.seconds

        # numticks = 5
        # Only difference to original AutoDateLocator: less ticks
        numticks = self.max_ticks

        # self._freq = YEARLY
        interval = 1
        bymonth = 1
        bymonthday = 1
        byhour = 0
        byminute = 0
        bysecond = 0
        if (numYears >= numticks):
            self._freq = YEARLY
            interval = int(numYears // numticks)
        elif (numMonths >= numticks):
            self._freq = MONTHLY
            bymonth = range(1, 13)
            interval = int(numMonths // numticks)
        elif (numDays >= numticks):
            self._freq = DAILY
            bymonth = None
            bymonthday = range(1, 32)
            interval = int(numDays // numticks)
        elif (numHours >= numticks):
            self._freq = HOURLY
            bymonth = None
            bymonthday = None
            byhour = range(0, 24)      # show every hour
            interval = int(numHours // numticks)
        elif (numMinutes >= numticks):
            self._freq = MINUTELY
            bymonth = None
            bymonthday = None
            byhour = None
            byminute = range(0, 60)
            interval = int(numMinutes // numticks)
            # end if
        elif (numSeconds >= numticks):
            self._freq = SECONDLY
            bymonth = None
            bymonthday = None
            byhour = None
            byminute = None
            bysecond = range(0, 60)
            interval = int(numSeconds // numticks)
            # end if
        else:
            # do what?
            #   microseconds as floats, but floats from what reference point?
            pass

        rrule = rrulewrapper(self._freq, interval=interval,
                             dtstart=dmin, until=dmax,
                             bymonth=bymonth, bymonthday=bymonthday,
                             byhour=byhour, byminute=byminute,
                             bysecond=bysecond)

        locator = RRuleLocator(rrule, self.tz)
        locator.set_axis(self.axis)

        locator.set_view_interval(*self.axis.get_view_interval())
        locator.set_data_interval(*self.axis.get_data_interval())
        return locator


class Graph(object):
    """
    Class for matplotlib graphs, i.e. for popups, krw graphs

    - calculates correct size
    - horizontal axis = dates
    - vertical axis = user defined
    - outputs httpresponse for png
    """

    def __init__(self,
                 start_date, end_date,
                 width=None, height=None,
                 today=datetime.datetime.now()):
        self.start_date = start_date
        self.end_date = end_date
        self.today = today

        self.figure = Figure()
        if width is None or not width:
            width = 380.0
        if height is None or not height:
            height = 250.0
        self.width = float(width)
        self.height = float(height)
        self.figure.set_size_inches((_inches_from_pixels(self.width),
                                     _inches_from_pixels(self.height)))
        self.figure.set_dpi(SCREEN_DPI)
        # Figure color
        self.figure.set_facecolor('white')
        # Axes and legend location: full width is "1".
        self.legend_width = 0.01  # no legend by default
        self.left_label_width = LEFT_LABEL_WIDTH / self.width
        self.bottom_axis_location = BOTTOM_LINE_HEIGHT / self.height
        self.x_label_height = 0
        self.axes = self.figure.add_subplot(111)
        self.axes.grid(True)
        self.fixup_axes()
        # Date range
        # self.axes.set_xlim(date2num((self.start_date, self.end_date)))

    def add_today(self):
        # Show line for today.
        self.axes.axvline(self.today, color='blue', lw=1, ls='--')

    def suptitle(self, title):
        self.figure.suptitle(title,
                             x=self.left_label_width,
                             horizontalalignment='left')

    def set_xlabel(self, xlabel):
        self.axes.set_xlabel(xlabel)
        self.x_label_height = BOTTOM_LINE_HEIGHT / self.height

    def fixup_axes(self):
        """Fix up the axes by limiting the amount of items."""
        available_width = self.width - LEFT_LABEL_WIDTH - LEGEND_WIDTH
        approximate_characters = int(available_width / (FONT_SIZE / 2))
        max_number_of_ticks = approximate_characters // 20
        if max_number_of_ticks < 2:
            max_number_of_ticks = 2
        locator = LessTicksAutoDateLocator(max_ticks=max_number_of_ticks)
        self.axes.xaxis.set_major_locator(locator)
        self.axes.xaxis.set_major_formatter(AutoDateFormatter(locator))

        available_height = self.height - BOTTOM_LINE_HEIGHT
        approximate_lines = int(available_height / (FONT_SIZE * 1.5))
        max_number_of_ticks = approximate_lines
        if max_number_of_ticks < 2:
            max_number_of_ticks = 2
        locator = MaxNLocator(nbins=max_number_of_ticks - 1)
        self.axes.yaxis.set_major_locator(locator)

    def legend(self, handles=None, labels=None):
        """
        handles is list of matplotlib objects (e.g. matplotlib.lines.Line2D)
        labels is list of strings
        """

        # reserve space for legend. even when there is no legend displayed
        self.legend_width = LEGEND_WIDTH / self.width

        if handles is None and labels is None:
            handles, labels = self.axes.get_legend_handles_labels()
        if handles and labels:
            return self.figure.legend(
                handles,
                labels,
                bbox_to_anchor=(1 - self.legend_width,
                                0,  # self.bottom_axis_location
                                self.legend_width,
                                1),
                loc=4,  # Lower right of above bbox.
                fancybox=True,
                shadow=True,
               )
         #legend.set_size('medium')
         # TODO: get rid of the border around the legend.

    def http_png(self):
        self.axes.set_position((self.left_label_width,
                                self.bottom_axis_location + self.x_label_height,
                                1 - self.legend_width - self.left_label_width,
                                1 - 2 * self.bottom_axis_location - self.x_label_height))

        # Set date range
        # Somehow, the range cannot be set in __init__
        self.axes.set_xlim(date2num((self.start_date, self.end_date)))

        canvas = FigureCanvas(self.figure)
        response = HttpResponse(content_type='image/png')
        canvas.print_png(response)
        return response
