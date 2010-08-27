"""Animation scrollbar handling."""
import datetime

from django.http import Http404
from django.http import HttpResponse
from django.utils import simplejson as json

from lizard_map.daterange import current_start_end_dates
from lizard_map.daterange import DUTCH_DATE_FORMAT
from lizard_map.workspace import WorkspaceManager

ANIMATION_SETTINGS = 'animation_settings'


def slider_layout_extra(request):
    """
    Calculates layout_extra (used when drawing graphs) for current
    animation slider.

    Requires request.
    """

    layout_extra = {}

    workspace_manager = WorkspaceManager(request)
    workspace_groups = workspace_manager.load_or_create()

    for workspaces in workspace_groups.values():
        for workspace in workspaces:
            for workspace_item in workspace.workspace_items.filter(
                visible=True):
                if workspace_item.adapter.is_animatable:
                    animation_info = AnimationSettings(request).info()
                    if not 'vertical_lines' in layout_extra:
                        layout_extra['vertical_lines'] = []
                    vertical_line = {'name': 'Positie animatie slider',
                                     'value': animation_info['selected_date'],
                                     'style': {'linewidth': 3,
                                               'linestyle': '--',
                                               'color': 'green'}}
                    layout_extra['vertical_lines'].append(vertical_line)
    return layout_extra


def set_animation_date(request):
    """Sets the animation date in the session"""
    if request.is_ajax():
        animation_settings = AnimationSettings(request)
        animation_settings.slider_position = int(request.POST['slider_value'])
        selected_date = animation_settings.info()['selected_date']
        return_date = selected_date.strftime(DUTCH_DATE_FORMAT)
        return HttpResponse(json.dumps(return_date))
    else:
        raise Http404


class AnimationSettings(object):
    """Handle animation settings in the session."""

    def __init__(self, request):
        self.request = request

        if ANIMATION_SETTINGS not in self.request.session:
            self.request.session[ANIMATION_SETTINGS] = {}
        self.start_date, self.end_date = current_start_end_dates(self.request)
        period = self.end_date - self.start_date
        self.period_in_days = period.days

    def info(self):
        """Return info for creating the slider.

        http://jqueryui.com/demos/slider needs a couple of settings for the
        slider.  min/max for the start/end value.  We start at 0 and the max
        is the number of days in the current date range.

        The step is hardcoded to 1 (day) for now.

        The value is the current position of the slider (in days, just like
        the step).

        For visualisation, we also pass the current value as a datetime.

        """
        result = {}
        selected_date = self.start_date + datetime.timedelta(
            days=self.slider_position)
        # Convert the date to datetime as we'll want that later on.
        selected_date = datetime.datetime.combine(selected_date,
                                                  datetime.time(0))
        result['min'] = 0
        result['max'] = self.period_in_days
        result['step'] = 1
        result['value'] = self.slider_position
        result['selected_date'] = selected_date
        return result

    def _set_slider_position(self, value):
        """Store value in the session."""
        if value < 0:
            value = 0
        if value > self.period_in_days:
            value = self.period_in_days
        self.request.session[ANIMATION_SETTINGS]['slider_position'] = value
        self.request.session.modified = True

    def _get_slider_position(self):
        """Return value stored in the session."""
        return self.request.session[ANIMATION_SETTINGS].get(
            'slider_position', 0)

    slider_position = property(_get_slider_position, _set_slider_position)
