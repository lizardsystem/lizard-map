"""
Helper classes and functions for adapters
"""
import datetime

from django.http import HttpResponse
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.dates import date2num
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from lizard_map.matplotlib_settings import FONT_SIZE

SCREEN_DPI = 72.0
LEGEND_WIDTH = 200
LEFT_LABEL_WIDTH = 100
BOTTOM_LINE_HEIGHT = FONT_SIZE * 1.5

def _inches_from_pixels(pixels):
    """Return size in inches for matplotlib's benefit"""
    return pixels / SCREEN_DPI


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
                 width=380.0, height=280.0,
                 today=datetime.datetime.now()):
        self.start_date = start_date
        self.end_date = end_date
        self.today = today

        self.figure = Figure()
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
        self.axes = self.figure.add_subplot(111)
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

    def fixup_axes(self):
        """Fix up the axes by limiting the amount of items."""
        available_width = self.width - LEFT_LABEL_WIDTH - LEGEND_WIDTH
        print "available", available_width
        approximate_characters = int(available_width / (FONT_SIZE / 3))
        print "approx chars", approximate_characters
        max_number_of_labels = approximate_characters // 20
        print "max labels", max_number_of_labels
        max_number_of_intervals = max_number_of_labels - 1
        if max_number_of_intervals < 2:
            max_number_of_intervals = 2
        print "max intervals", max_number_of_intervals
        self.axes.xaxis.set_major_locator(MaxNLocator(
                max_number_of_intervals))
        # TODO: set a proper date formatter

    def legend(self, handles=None, labels=None):
        """
        handles is list of matplotlib objects (e.g. matplotlib.lines.Line2D)
        labels is list of strings
        """
        self.legend_width = LEGEND_WIDTH / self.width
        if handles is None and labels is None:
            handles, labels = self.axes.get_legend_handles_labels()
        if labels:
            return self.figure.legend(
                handles,
                labels,
                bbox_to_anchor=(1 - self.legend_width,
                                0, # self.bottom_axis_location
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
                                self.bottom_axis_location,
                                1 - self.legend_width - self.left_label_width,
                                1 - 2 * self.bottom_axis_location))

        # Set date range
        # Somehow, the range cannot be set in __init__
        self.axes.set_xlim(date2num((self.start_date, self.end_date)))

        canvas = FigureCanvas(self.figure)
        response = HttpResponse(content_type='image/png')
        canvas.print_png(response)
        return response
