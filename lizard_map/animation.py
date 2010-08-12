"""Animation scrollbar handling."""
import datetime

from lizard_map.daterange import current_start_end_dates

ANIMATION_SETTINGS = 'animation_settings'


class AnimationSettings(object):
    """Handle animation settings in the session."""

    def __init__(self, request):
        self.request = request
        self.session = self.request.session
        if ANIMATION_SETTINGS not in self.session:
            self.session[ANIMATION_SETTINGS] = {}
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
        self.session[ANIMATION_SETTINGS]['slider_position'] = value

    def _get_slider_position(self):
        """Return value stored in the session."""
        return self.session[ANIMATION_SETTINGS].get('slider_position', 0)

    slider_position = property(_get_slider_position, _set_slider_position)


