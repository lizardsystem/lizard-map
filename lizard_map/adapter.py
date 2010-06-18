"""
Helper classes and functions for adapters
"""
import datetime

from matplotlib.figure import Figure

from lizard_map.views import _inches_from_pixels
from lizard_map.views import SCREEN_DPI

class Graph(object):
    """
    Class for matplotlib graphs, i.e. for popups, krw graphs

    - calculates correct size
    - horizontal axis = dates
    - vertical axis = user defined
    - outputs httpresponse for png
    """

    def __init__(self, start_date, end_date, width, height, today=datetime.datetime.now()):
        self.start_date = start_date 
        self.end_date = end_date
        self.today = today

        self.figure = Figure()
        width = float(width)
        height = float(height)
        self.figure.set_size_inches((_inches_from_pixels(width),
                                     _inches_from_pixels(height)))
        self.figure.set_dpi(SCREEN_DPI)
        # Figure color
        self.figure.set_facecolor('white')
        # Axes and legend location: full width is "1".
        self.legend_width = LEGEND_WIDTH / width
        self.left_label_width = LEFT_LABEL_WIDTH / width
        self.bottom_axis_location = FONT_SIZE / height
        #top_axis_location = 1 - FONT_SIZE / height

        self.axes = self.figure.add_subplot(111)

        self.axes.set_position((self.left_label_width, 
                                self.bottom_axis_location,
                                1 - self.legend_width - self.left_label_width,
                                1 - 2 * self.bottom_axis_location))
        # Date range
        # self.axes.set_xlim(date2num((self.start_date, self.end_date)))

    def add_today(self):
        # Show line for today.
        self.axes.axvline(self.today, color='blue', lw=1, ls='--')

    def suptitle(self, title):
        self.figure.suptitle(title,
                             x=self.left_label_width,
                             horizontalalignment='left')

    def legend(self, handles=None, labels=None):
        """
        handles is list of matplotlib objects (e.g. matplotlib.lines.Line2D)
        labels is list of strings
        """
        if handles is None and labels is None:
            handles, labels = self.axes.get_legend_handles_labels()
        if labels:
            return self.figure.legend(
                handles,
                labels,
                bbox_to_anchor=(1 - self.legend_width,
                                self.bottom_axis_location,
                                self.legend_width,
                                1),
                # loc=3,  # Lower left of above bbox.
                loc=4,  # Lower right of above bbox.
                fancybox=True,
                shadow=True,
                )
         #legend.set_size('medium')
         # TODO: get rid of the border around the legend.

    def http_png(self):
        # Somehow, the range cannot be set in __init__
        self.axes.set_xlim(date2num((self.start_date, self.end_date)))

        canvas = FigureCanvas(self.figure)
        response = HttpResponse(content_type='image/png')
        canvas.print_png(response)
        return response
