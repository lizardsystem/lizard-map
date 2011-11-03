"""Animation scrollbar handling."""
import datetime

from django.http import Http404
from django.http import HttpResponse
from django.utils import simplejson as json

from lizard_map.daterange import current_start_end_dates
from lizard_map.daterange import DUTCH_DATE_FORMAT
#from lizard_map.workspace import WorkspaceManager
from lizard_map.models import WorkspaceEdit
from lizard_map.models import WorkspaceStorage

ANIMATION_SETTINGS = 'animation_settings'


# TODO: L3 test
def slider_layout_extra(request, workspace_storage_id=None):
    """
    Calculates layout_extra (used when drawing graphs) for current
    animation slider.

    Requires request for session data.
    """

    layout_extra = {}

    if workspace_storage_id is None:
        workspace = WorkspaceEdit.get_or_create(request.session.session_key,
                                                request.user)
    else:
        workspace = WorkspaceStorage.objects.get(pk=workspace_storage_id)

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
    """Handle animation settings in the session.

    animation_slider has the value of [days from day_one], where
    day_one is defined as year 1979, 25th of May (negative values are
    allowed).
    """

    def __init__(self, request, today=None):
        self.request = request

        if ANIMATION_SETTINGS not in self.request.session:
            self.request.session[ANIMATION_SETTINGS] = {}
        start_date, end_date = current_start_end_dates(
            self.request, today=today)

        self.day_one = datetime.datetime(1979, 5, 25)
        self.start_date_days = (start_date - self.day_one).days
        self.end_date_days = (end_date - self.day_one).days

    def info(self):
        """Return info for creating the slider.

        http://jqueryui.com/demos/slider needs a couple of settings for the
        slider.  min/max for the start/end value.  We start at 0 and the max
        is the number of days in the current date range.

        The step is hardcoded to 1 (day) for now.

        The value is the current position of the slider (in days from
        day_one, just like the step size).

        For visualisation, we also pass the current value as a datetime.

        """
        result = {}
        selected_date = self.day_one + datetime.timedelta(
            self.slider_position)
        # Convert the date to datetime as we'll want that later on.
        selected_date = datetime.datetime.combine(selected_date,
                                                  datetime.time(0))
        result['min'] = self.start_date_days
        result['max'] = self.end_date_days
        result['step'] = 1
        result['value'] = self.slider_position
        result['selected_date'] = selected_date
        return result

    def _set_slider_position(self, value):
        """Store value in the session."""
        #value = min(max(self.start_date_days, value), self.end_date_days)
        value = min(max(self.start_date_days, value), self.end_date_days)
        self.request.session[ANIMATION_SETTINGS]['slider_position'] = value
        self.request.session.modified = True
        # ^^^ .modified is only used in tests.

    def _get_slider_position(self):
        """Return value stored in the session."""
        return min(max(self.request.session[ANIMATION_SETTINGS].get(
            'slider_position', self.end_date_days), self.start_date_days),
                   self.end_date_days)

    slider_position = property(_get_slider_position, _set_slider_position)
