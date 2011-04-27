"""Handle the date range setting and remembering
"""
import datetime
import logging

from django import forms
from django.conf import settings
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

from datewidget import SelectDateWidget
from django.forms.widgets import RadioSelect


logger = logging.getLogger(__name__)

PERIOD_DAY = 1
PERIOD_TWO_DAYS = 2
PERIOD_WEEK = 3
PERIOD_MONTH = 4
PERIOD_YEAR = 5
PERIOD_OTHER = 6

PERIOD_DAYS = {
    PERIOD_DAY: (datetime.timedelta(-1), datetime.timedelta(0)),
    PERIOD_TWO_DAYS: (datetime.timedelta(-2), datetime.timedelta(0)),
    PERIOD_WEEK: (datetime.timedelta(-7), datetime.timedelta(0)),
    PERIOD_MONTH: (datetime.timedelta(-30), datetime.timedelta(0)),
    PERIOD_YEAR: (datetime.timedelta(-365), datetime.timedelta(0))}

PERIOD_CHOICES = [[PERIOD_DAY, 'dg'],
                  [PERIOD_TWO_DAYS, '2dg'],
                  [PERIOD_WEEK, 'wk'],
                  [PERIOD_MONTH, 'mnd'],
                  [PERIOD_YEAR, 'jr'],
                  [PERIOD_OTHER, 'anders']]

SESSION_DT_PERIOD = 'dt_period'
SESSION_DT_START = 'dt_start'
SESSION_DT_END = 'dt_end'

DUTCH_DATE_FORMAT = '%d/%m/%Y'
# ^^^ This is what jquery ui with the Dutch locale does for Reinout.

default_start_days = getattr(settings, 'DEFAULT_START_DAYS', -1000)
default_end_days = getattr(settings, 'DEFAULT_END_DAYS', 10)


def default_start():
    """Default period when period is PERIOD_OTHER"""
    return datetime.timedelta(days=default_start_days)


def default_end():
    """Default period when period is PERIOD_OTHER"""
    return datetime.timedelta(days=default_end_days)


class HorizontalRadioRenderer(forms.RadioSelect.renderer):
    """ this overrides widget method to put radio buttons horizontally
        instead of vertically.
    """
    def render(self):
        """Outputs radios"""
        return (u'\n'.join([u'%s\n' % widget for widget in self]))


class DateRangeForm(forms.Form):
    """
    Date range form.
    """
    # Settings
    start_year = getattr(settings,
                         'START_YEAR',
                          datetime.date.today().year - 7)
    end_year = getattr(settings,
                       'END_YEAR',
                        datetime.date.today().year + 3)
    years_choices = range(start_year, end_year + 1)

    # Form fields
    period = forms.ChoiceField(
        required=True,
        widget=RadioSelect(renderer=HorizontalRadioRenderer),
        choices=PERIOD_CHOICES,
        label='',)
    # TODO: NL date format.  Also hardcoded in the js.
    dt_start = forms.DateTimeField(
        label='van',
        widget=SelectDateWidget(years=years_choices),
        required=False)
    dt_end = forms.DateTimeField(
        label='t/m',
        widget=SelectDateWidget(years=years_choices),
        required=False)

    def __init__(self, *args, **kwargs):
        # # Add argument period, if not available.
        # if 'period' not in args[0]:
        #     args[0]['period'] = PERIOD_DAY
        super(DateRangeForm, self).__init__(*args, **kwargs)

        # Set initial dt_start/end on disabled when not selected.
        if args and 'period' in args[0] and args[0]['period'] != PERIOD_OTHER:
            self.fields['dt_start'].widget.attrs['disabled'] = True
            self.fields['dt_end'].widget.attrs['disabled'] = True


def deltatime_range(daterange, now=None):
    """
    Put daterange into session, revert to defaults.

    daterange is {'dt_start': xx, 'dt_end': xx, 'period': int}
    """
    if now is None:
        now = datetime.datetime.now()

    period = int(daterange['period'])

    # Calculate relative start/end dates from given period.
    if period == PERIOD_OTHER:
        almost_one_day = datetime.timedelta(
            hours=23, minutes=59, seconds=59)
        try:
            dt_start = daterange.get('dt_start', None)
            timedelta_start = dt_start - now
        except TypeError:
            timedelta_start = default_start()

        try:
            # Since we select on day basis, we want to include
            # the end day.
            dt_end = daterange.get('dt_end', None)
            timedelta_end = (dt_end + almost_one_day - now)
        except TypeError:
            timedelta_end = default_end()

        # Make sure start is before end
        if timedelta_start > timedelta_end:
            timedelta_start = timedelta_end - almost_one_day
    else:
        timedelta_start, timedelta_end = PERIOD_DAYS[period]

    return period, timedelta_start, timedelta_end


def store_timedelta_range(request, period, timedelta_start, timedelta_end):
    """Store relative start/end dates in session."""
    request.session[SESSION_DT_PERIOD] = period
    request.session[SESSION_DT_START] = timedelta_start
    request.session[SESSION_DT_END] = timedelta_end


def set_date_range(request, template='lizard_map/daterange.html',
                   now=None):
    """View: store the date range in the session and redirect.

    POST must contain DateRangeForm fields.
    now is a datetime field, used for testing.
    """
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():
            came_from = request.META.get('HTTP_REFERER', '/')
            date_range = form.cleaned_data

            period, timedelta_start, timedelta_end = deltatime_range(
                date_range, now=now)
            store_timedelta_range(
                request, period, timedelta_start, timedelta_end)

            return HttpResponseRedirect(came_from)
    else:
        # Invalid, should never happen. You're probably surfing to the
        # set_date_range url.
        form = DateRangeForm()

    # Form rendering just for debugging errors.
    return render_to_response(
        template,
        {'date_range_form': form},
        context_instance=RequestContext(request))


def current_period(request):
    """
    Return the current period, either default or from session.

    TODO: mix together with current_start_end_dates (but is has a lot
    of impact)
    """
    default_period = getattr(settings, 'DEFAULT_PERIOD', PERIOD_DAY)

    return request.session.get(SESSION_DT_PERIOD, default_period)


def current_start_end_dates(request, for_form=False, today=None):
    """Return the current start/end dates.

    If for_form is True, return it as a dict so that we can pass it directly
    into a form class.  Otherwise return it as a tuple.

    today is a datetime field, used for testing.
    """
    if today is None:
        today = datetime.datetime.now()

    period = current_period(request)
    if period == PERIOD_OTHER:
        period_start, period_end = default_start(), default_end()
    else:
        period_start, period_end = PERIOD_DAYS[period]

    dt_start = request.session.get(
        SESSION_DT_START, period_start) + today
    dt_end = request.session.get(
        SESSION_DT_END, period_end) + today
    if for_form:
        return dict(dt_start=dt_start,
                    dt_end=dt_end)
    else:
        return (dt_start, dt_end)
