"""
Helper classes and functions for adapters
"""
import datetime
import locale
import math
import numpy
import pkg_resources

from dateutil.relativedelta import relativedelta
from dateutil.rrule import YEARLY, MONTHLY, DAILY, HOURLY, MINUTELY, SECONDLY
from django.http import HttpResponse
from django.utils import simplejson as json
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.dates import AutoDateFormatter
from matplotlib.dates import AutoDateLocator
from matplotlib.dates import DateFormatter
from matplotlib.dates import RRuleLocator
from matplotlib.dates import date2num
from matplotlib.dates import num2date
from matplotlib.dates import rrulewrapper
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import ScalarFormatter
from lizard_map.matplotlib_settings import FONT_SIZE
from lizard_map.matplotlib_settings import SCREEN_DPI

import logging
logger = logging.getLogger(__name__)

# Requires correct locale be generated on the server.
# On ubuntu: check with locale -a
# On ubuntu: sudo locale-gen nl_NL.utf8
try:
    locale.setlocale(locale.LC_TIME, 'nl_NL.UTF8')
except locale.Error:
    logger.debug('No locale nl_NL.UTF8 on this os. Using default locale.')


#Adapter stuff

ADAPTER_ENTRY_POINT = 'lizard_map.adapter_class'


# Graph stuff

LEGEND_WIDTH = 200
LEFT_LABEL_WIDTH = 100
BOTTOM_LINE_HEIGHT = FONT_SIZE * 2


def _inches_from_pixels(pixels):
    """Return size in inches for matplotlib's benefit"""
    return pixels / SCREEN_DPI


# Adapter helpers

def parse_identifier_json(identifier_json):
    """Return dict of parsed identifier_json.

    Converts keys to str.
    TODO: .replace('%22', '"') in a better way
    """

    identifier_json = identifier_json.replace('%22', '"').replace('%20', ' ')
    if not identifier_json:
        return {}
    result = {}
    for k, v in json.loads(identifier_json).items():
        result[str(k)] = v
    return result


class AdapterClassNotFoundError(Exception):
    pass


def adapter_serialize(o):
    return json.dumps(o).replace('"', '%22').replace(' ', '%20')


def adapter_class_names():
    """Return allowed layer method names (from entrypoints)

    in tuple of 2-tuples
    """
    entrypoints = [(entrypoint.name, entrypoint.name) for entrypoint in
                   pkg_resources.iter_entry_points(group=ADAPTER_ENTRY_POINT)]
    return tuple(entrypoints)


def adapter_layer_arguments(layer_json):
    """Return dict of parsed adapter_layer_json.

    Converts keys to str.
    """
    if not layer_json:
        return {}
    result = {}
    decoded_json = json.loads(layer_json)
    for k, v in decoded_json.items():
        result[str(k)] = v
    return result


def adapter_entrypoint(adapter_class, layer_arguments, workspace_item=None):
    """Return adapter instance for entrypoint

    Optionally give workspace_item, for legacy (must be factored out).
    """
    # TODO: this happens more often than needed! Cache it.
    for entrypoint in pkg_resources.iter_entry_points(
        group=ADAPTER_ENTRY_POINT):
        if entrypoint.name == adapter_class:
            try:
                real_adapter = entrypoint.load()
                real_adapter = real_adapter(
                    workspace_item,
                    layer_arguments=layer_arguments,
                    adapter_class=adapter_class)
            except ImportError, e:
                logger.critical("Invalid entry point: %s", e)
                raise
            return real_adapter
    raise AdapterClassNotFoundError(
        u'Entry point for %r not found' % adapter_class)


# Graph stuff

class LessTicksAutoDateLocator(AutoDateLocator):
    """Similar to matplotlib.date.AutoDateLocator, but with less ticks."""

    def __init__(self, tz=None, numticks=7):
        AutoDateLocator.__init__(self, tz)
        self.numticks = numticks

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
        # Difference to original AutoDateLocator: less ticks
        numticks = self.numticks

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


class MultilineAutoDateFormatter(AutoDateFormatter):
    """Multiline version of AutoDateFormatter.

    This class needs the axes to be able to initialize. When called, the
    ticks need to be known as well. For some scales, instead of showing a
    predetermined date label at any tick, the labels are chosen dependent of
    the tick position. Note that some labels are multiline, so make sure
    there is space for them in your figure."""

    def __init__(self, locator, axes, tz=None):
        self._locator = locator
        self._formatter = DateFormatter("%b %d %Y %H:%M:%S %Z", tz)
        self._tz = tz
        self.axes = axes
        self.tickinfo = None

    def __call__(self, x, pos=0):

        scale = float(self._locator._get_unit())
        if not self.tickinfo:
            self.tickinfo = self.Tickinfo(self.axes.get_xticks())

        if (scale == 365.0):
            self._formatter = DateFormatter("%Y", self._tz)
        elif (scale == 30.0):
            if self.tickinfo.show_year(x):
                self._formatter = DateFormatter("%b\n%Y", self._tz)
            else:
                self._formatter = DateFormatter("%b", self._tz)
        elif ((scale == 1.0) or (scale == 7.0)):
            if self.tickinfo.show_month(x):
                self._formatter = DateFormatter("%d\n%b %Y", self._tz)
            else:
                self._formatter = DateFormatter("%d", self._tz)
        elif (scale == (1.0 / 24.0)):
            if x == self.tickinfo.max:
                # don't show the full label of the first hour
                # of the next day
                self._formatter = DateFormatter("%H", self._tz)
            elif self.tickinfo.show_day(x):
                self._formatter = DateFormatter("%H\n%d %b %Y", self._tz)
            else:
                self._formatter = DateFormatter("%H", self._tz)
        elif (scale == (1.0 / (24 * 60))):
            self._formatter = DateFormatter("%H:%M:%S %Z", self._tz)
        elif (scale == (1.0 / (24 * 3600))):
            self._formatter = DateFormatter("%H:%M:%S %Z", self._tz)
        else:
            self._formatter = DateFormatter("%b %d %Y %H:%M:%S %Z", self._tz)

        return self._formatter(x, pos)

    class Tickinfo(object):
        """ Class with tick information.

        The methods are used to determine what kind of label to put at a
        particular tick."""

        def __init__(self, ticks):
            self.ticks = ticks
            self.min = ticks[0]
            self.max = ticks[-1]
            self.step = ticks[1] - ticks[0]
            self.span = ticks[-1] - ticks[0]
            self.mid = ticks[int((len(ticks) - 1) / 2)]

        def show_day(self, tick):
            """ Return true or false to show day at this tick."""

            # If there is only one day in the ticks, show it at the center
            if (num2date(self.min).day == num2date(self.max).day):
                if tick == self.mid:
                    return True
                else:
                    return False

            # If there are more days in the ticks, show a label for that
            # tick that is closest to the center of their day.
            else:
                middle_of_day = self.middle_of_day(tick)
                if ((abs(tick - middle_of_day) < self.step / 2) or
                    (middle_of_day < self.min and tick == self.min) or
                    (middle_of_day > self.max and tick == self.max)):
                    return True
                else:
                    return False

        def show_month(self, tick):
            """ Return true or false to show month at this tick."""

            # If there is only one month in the ticks, show it at the center
            if (num2date(self.min).month == num2date(self.max).month):
                if tick == self.mid:
                    return True
                else:
                    return False

            # If there are more months in the ticks, show a label for that
            # tick that is closest to the center of their month.
            else:
                middle_of_month = self.middle_of_month(tick)
                if ((abs(tick - middle_of_month) < self.step / 2) or
                    (middle_of_month < self.min and tick == self.min) or
                    (middle_of_month > self.max and tick == self.max)):
                    return True
                else:
                    return False

        def show_year(self, tick):
            """ Return true or false to show year at this tick."""

            # If there is only one year in the ticks, show it at the center
            if (num2date(self.min).year == num2date(self.max).year):
                if tick == self.mid:
                    return True
                else:
                    return False

            # If there are more years in the ticks, show a label for that
            # tick at the first month of that year.
            else:
                first_of_year = self.first_of_year(tick)
                if ((0 <= tick - first_of_year < self.step) or
                    (first_of_year < self.min and tick == self.min) or
                    (first_of_year > self.max and tick == self.max)):
                    return True
                else:
                    return False

        def middle_of_day(self, tick):
            """ Return the middle of the day as matplotlib number. """
            dt = num2date(tick)
            middle_of_day = datetime.datetime(dt.year, dt.month, dt.day, 12)
            return date2num(middle_of_day)

        def middle_of_month(self, tick):
            """ Return the middle of the month as matplotlib number. """
            dt = num2date(tick)
            middle_of_month = datetime.datetime(dt.year, dt.month, 16)
            return date2num(middle_of_month)

        def middle_of_year(self, tick):
            """ Return the middle of the year as matplotlib number. """
            dt = num2date(tick)
            middle_of_year = datetime.datetime(dt.year, 7, 1)
            return date2num(middle_of_year)

        def first_of_year(self, tick):
            """ Return the middle of the year as matplotlib number. """
            dt = num2date(tick)
            middle_of_year = datetime.datetime(dt.year, 1, 1)
            return date2num(middle_of_year)


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
                 today=datetime.datetime.now(),
                 restrict_to_month=None,
                 tz=None):
        self.start_date = start_date
        self.end_date = end_date
        self.today = today
        self.restrict_to_month = restrict_to_month
        self.tz = tz

        self.figure = Figure()
        if width is None or not width:
            width = 380.0
        if height is None or not height:
            height = 240.0
        self.width = float(width)
        self.height = float(height)
        self.figure.set_size_inches((_inches_from_pixels(self.width),
                                     _inches_from_pixels(self.height)))
        self.figure.set_dpi(SCREEN_DPI)
        # Figure color
        self.figure.set_facecolor('white')
        # Axes and legend location: full width is "1".
        self.legend_width = 0.08
        # ^^^ No legend by default, but we *do* allow a little space to the
        # right of the graph to prevent the rightmost label from being cut off
        # (at least, in a reasonable percentage of the cases).
        self.left_label_width = LEFT_LABEL_WIDTH / self.width
        self.bottom_axis_location = BOTTOM_LINE_HEIGHT / self.height
        self.x_label_height = 0.08
        self.legend_on_bottom_height = 0.0
        self.axes = self.figure.add_subplot(111)
        self.axes.grid(True)

        # We track whether y_lim has been set manually
        self._y_min_set_manually = False
        self._y_max_set_manually = False

        # Fixup_axes in init, so axes can be customised (for example set_ylim).
        self.fixup_axes()

        #deze kan je zelf zetten
        self.ax2 = None

    def set_ylim(self, y_min, y_max, min_manual=False, max_manual=False):
        logger.debug('set_ylim y_min = %f y_max = %f' % (y_min, y_max))
        self.axes.set_ylim(y_min, y_max)
        self._y_min_set_manually = min_manual
        self._y_max_set_manually = max_manual

    def add_today(self):
        # Show line for today.
        self.axes.axvline(self.today, color='orange', lw=1, ls='--')

    def set_ylim_margin(self, top=0.1, bottom=0.0):
        """Adjust y-margin of axes.

        The standard margin is sometimes zero. This method sets the margin
        based on already present data in the visible part of the plot, so
        call it after plotting and before http_png().

        Note that it is assumed here that the y-axis is not reversed.

        From matplotlib 1.0 on there is a set_ymargin method
        like this already."""

        lines = self.axes.lines
        arrays = [numpy.array(l.get_data()) for l in lines]

        # axhline and axvline give trouble - remove short lines from list
        big_arrays = [a for a in arrays if a.size > 4]
        if len(big_arrays) > 0:
            data = numpy.concatenate(big_arrays, axis=1)
            if len(data[0]) > 0:
                # Datatimes from database may have timezone information.
                # In that case, start_date and end_date cannot be naive.
                # Assume all datetimes do have the same timezone, so we
                # can do the comparison.
                start_date_tz =\
                    self.start_date.replace(tzinfo=data[0][0].tzinfo)
                end_date_tz =\
                    self.end_date.replace(tzinfo=data[0][0].tzinfo)
            index_in_daterange = ((data[0] < end_date_tz) &
                                  (data[0] > start_date_tz))

            # Calculate correct y_min and y_max, but use old if they have
            # already been set manually
            if index_in_daterange.any():
                data_low = numpy.min(data[1, index_in_daterange])
                data_high = numpy.max(data[1, index_in_daterange])
                data_span = data_high - data_low

                view_low = data_low - data_span * bottom
                view_high = data_high + data_span * top

                # Don't zoom in too much if values are essentially the same
                # and differ only in noise. Values shown at the Y-axis should
                # only have 2 decimals.
                view_low = math.floor(view_low * 40) / 40
                view_high = math.ceil(view_high * 40) / 40
                while (view_high - view_low) < 0.03:
                    # Difference is only 0.025 (or 0!), differences of
                    # smaller than 0.01 show up at the y-axis.
                    view_low -= 1.0 / 80
                    view_high += 1.0 / 80

                if self._y_min_set_manually:
                    view_low, _ = self.axes.get_ylim()
                if self._y_max_set_manually:
                    _, view_high = self.axes.get_ylim()

                self.axes.set_ylim(view_low, view_high)
        return None

    def suptitle(self, title):
        self.figure.suptitle(title,
                             x=self.left_label_width,
                             horizontalalignment='left')

    def set_xlabel(self, xlabel):
        self.axes.set_xlabel(xlabel)
        self.x_label_height = BOTTOM_LINE_HEIGHT / self.height

    def fixup_axes(self, second=False):
        """Fix up the axes by limiting the amount of items."""

        axes_to_change = self.axes
        if second:
            if self.ax2 is None:
                return
            else:
                axes_to_change = self.ax2

#        available_width = self.width - LEFT_LABEL_WIDTH - LEGEND_WIDTH
#        approximate_characters = int(available_width / (FONT_SIZE / 2))
#        max_number_of_ticks = approximate_characters // 20
#        if max_number_of_ticks < 2:
#            max_number_of_ticks = 2
        if not self.restrict_to_month:
            major_locator = LessTicksAutoDateLocator()
            axes_to_change.xaxis.set_major_locator(major_locator)

            major_formatter = MultilineAutoDateFormatter(
                major_locator, axes_to_change, tz=self.tz)
            axes_to_change.xaxis.set_major_formatter(major_formatter)

        available_height = (self.height -
                            BOTTOM_LINE_HEIGHT -
                            self.x_label_height -
                            self.legend_on_bottom_height)
        approximate_lines = int(available_height / (FONT_SIZE * 2.5))
        logger.info("#lines: %s", approximate_lines)
        max_number_of_ticks = approximate_lines
        if max_number_of_ticks < 2:
            max_number_of_ticks = 2
        locator = MaxNLocator(nbins=max_number_of_ticks - 1)
        if not second:
            axes_to_change.yaxis.set_major_locator(locator)
            # ^^^ [Arjan:] Turns out default amount of ticks wasn't that bad.
            # [Reinout:] I keep hearing complaints so I've re-enabled it.
            axes_to_change.yaxis.set_major_formatter(
                ScalarFormatter(useOffset=False))
        self.axes.set_ylabel(self.axes.get_ylabel(), size='x-large')

    def legend_space(self):
        """reserve space for legend (on the right side). even when
        there is no legend displayed"""
        self.legend_width = LEGEND_WIDTH / self.width

    def legend(self,
               handles=None,
               labels=None,
               ncol=1,
               force_legend_below=False):
        """
        Displays legend. Default is right side, but if the width is
        too small, it will display under the graph.

        handles is list of matplotlib objects (e.g. matplotlib.lines.Line2D)
        labels is list of strings
        """
        # experimental update: do not reserve space for legend by
        # default, just place over graph. use legend_space to manually
        # add space

        if handles is None and labels is None:
            handles, labels = self.axes.get_legend_handles_labels()
        if handles and labels:
            # Determine 'small' or 'large'
            # if self.width < 500 or force_legend_below:
            if force_legend_below:
                # TODO: Maybe remove this feature? Needs tweaking. The
                # legend is still on top of the graph, while the graph
                # reserves room for the legend below.
                legend_loc = 4  # lower right
                # approximation of legend height
                self.legend_on_bottom_height = min(
                    (len(labels) / ncol + 2) * BOTTOM_LINE_HEIGHT /
                    self.height,
                    0.5)
            else:
                legend_loc = 1  # Upper right'

            # For width 464 (empty space 150px assumed), we have:
            # <= 40 = medium
            # > 40 = small
            # > 50 = x-small
            # > 65 = xx-small
            # Fixes #3095
            font_len = max([len(label) for label in labels])
            font_size = 'medium'  # 'medium'
            if font_len > 40 * ((self.width - 150) / 314.0):
                font_size = 'small'
            if font_len > 50 * ((self.width - 150) / 314.0):
                font_size = 'x-small'
            if font_len > 65 * ((self.width - 150) / 314.0):
                font_size = 'xx-small'
            prop = {'size': font_size}

            return self.axes.legend(
                handles,
                labels,
                bbox_to_anchor=(1 - self.legend_width,
                                0,  # self.bottom_axis_location
                                self.legend_width,
                                # 1 = Upper right of above bbox. Use 0 for
                                # 'best'
                                1),
                prop=prop,
                loc=legend_loc,
                ncol=ncol,
                fancybox=True,
                shadow=True,)
         #legend.set_size('medium')
         # TODO: get rid of the border around the legend.
         # to get rid of the border: graph.axes.legend_.draw_frame(False)

    def init_second_axes(self):
        """ init second axes """
        self.ax2 = self.axes.twinx()
        self.fixup_axes(second=True)

    def http_png(self):
        """Output plot to png. Also calculates size of plot and put 'now'
        line."""

        axes_left = self.left_label_width
        axes_bottom = (self.bottom_axis_location + self.x_label_height +
                       self.legend_on_bottom_height)
        axes_width = 1 - self.legend_width - self.left_label_width
        axes_height = (1 - 2 * self.bottom_axis_location -
                       self.x_label_height - self.legend_on_bottom_height)

        self.axes.set_position((axes_left, axes_bottom,
                                axes_width, axes_height))

        if self.ax2 is not None:
            self.ax2.set_position((axes_left, axes_bottom,
                                axes_width, axes_height))

        # Set date range
        # Somehow, the range cannot be set in __init__
        if not self.restrict_to_month:
            self.axes.set_xlim(date2num((self.start_date, self.end_date)))
            try:
                self.set_ylim_margin(top=0.1, bottom=0.0)
            except:
                pass

        # Because of the use of setlocale to nl_NL, dutch monthnames can no
        # Longer be top-aligned.
        if locale.getlocale(locale.LC_TIME) == ('nl_NL', 'UTF8'):
            for l in self.axes.get_xticklabels():
                l.set_verticalalignment('baseline')
                l.set_position((0, -0.05))

        canvas = FigureCanvas(self.figure)
        response = HttpResponse(content_type='image/png')
        canvas.print_png(response)
        return response
