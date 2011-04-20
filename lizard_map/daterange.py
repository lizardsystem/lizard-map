"""Handle the date range setting and remembering"""
import datetime

from django import forms
from django.conf import settings
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

from datewidget import SelectDateWidget
from django.forms.widgets import RadioSelect


PERIOD_DAY = 1
PERIOD_TWO_DAYS = 2
PERIOD_WEEK = 3
PERIOD_MONTH = 4
PERIOD_YEAR = 5
PERIOD_OTHER = 6

PERIOD_DAYS = {
    PERIOD_DAY: (-1, 0),
    PERIOD_TWO_DAYS: (-2, 0),
    PERIOD_WEEK: (-7, 0),
    PERIOD_MONTH: (-30, 0),
    PERIOD_YEAR: (-365, 0)}

PERIOD_CHOICES = [[PERIOD_DAY, 'dg'],
                  [PERIOD_TWO_DAYS, '2dg'],
                  [PERIOD_WEEK, 'wk'],
                  [PERIOD_MONTH, 'mnd'],
                  [PERIOD_YEAR, 'jr'],
                  [PERIOD_OTHER, 'anders']]

SESSION_DATE_PERIOD = 'date_period'
SESSION_DATE_START = 'date_start'
SESSION_DATE_END = 'date_end'


default_start_days = getattr(settings, 'DEFAULT_START_DAYS', -1000)
default_end_days = getattr(settings, 'DEFAULT_END_DAYS', 10)

DEFAULT_START = datetime.date.today() + datetime.timedelta(
    days=default_start_days)
DEFAULT_END = datetime.date.today() + datetime.timedelta(
    days=default_end_days)

# Sorry, but these ^^^ need to be methods so that the default start
# date is not calculated from the start date.
def default_start():
    return datetime.date.today() + datetime.timedelta(
        days=default_start_days)

def default_end():
    return datetime.date.today() + datetime.timedelta(
        days=default_end_days)




DUTCH_DATE_FORMAT = '%d/%m/%Y'
# ^^^ This is what jquery ui with the Dutch locale does for Reinout.


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
    date_start = forms.DateField(
        label='Van',
        widget=SelectDateWidget(years=years_choices),
        required=False)
    date_end = forms.DateField(
        label='Tot',
        widget=SelectDateWidget(years=years_choices),
        required=False)

    def __init__(self, *args, **kwargs):
        super(DateRangeForm, self).__init__(*args, **kwargs)
        # Set initial date_start/end on disabled when not selected.
        if 'period' in args[0] and args[0]['period'] != PERIOD_OTHER:
            self.fields['date_start'].widget.attrs['disabled'] = True
            self.fields['date_end'].widget.attrs['disabled'] = True


def set_date_range(request, template='lizard_map/daterange.html'):
    """View: store the date range in the session and redirect."""
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():
            came_from = request.META.get('HTTP_REFERER', '/')
            data = form.cleaned_data
            today_dt = datetime.datetime.now()
            today = datetime.date(today_dt.year, today_dt.month, today_dt.day)
            period = int(data['period'])

            # Calculate start/end dates from given period.
            if period == PERIOD_OTHER:
                date_start = data.get('date_start', None)
                date_end = data.get('date_end', None)
                if date_start is None:
                    date_start = default_start()
                if date_end is None:
                    date_end = default_end()
            else:
                start_days, end_days = PERIOD_DAYS[period]
                date_start = today + datetime.timedelta(days=start_days)
                date_end = today + datetime.timedelta(days=end_days)

            # Store relative start/end dates.
            request.session[SESSION_DATE_START] = date_start - today
            request.session[SESSION_DATE_END] = date_end - today
            request.session[SESSION_DATE_PERIOD] = period
            return HttpResponseRedirect(came_from)
    else:
        form = DateRangeForm()
    # Form rendering just for debugging errors.
    return render_to_response(
        template,
        {'date_range_form': form},
        context_instance=RequestContext(request))


def current_start_end_dates(request, for_form=False):
    """Return the current start/end date strings, either default or from session.

    If for_form is True, return it as a dict so that we can pass it directly
    into a form class.  Otherwise return it as a tuple.

    """
    today = datetime.datetime.now()
    date_start = request.session.get(
        SESSION_DATE_START, default_start()) + today
    date_end = request.session.get(
        SESSION_DATE_END, default_end()) + today
    if for_form:
        #date_start = date_start.strftime(DUTCH_DATE_FORMAT)
        #date_end = date_end.strftime(DUTCH_DATE_FORMAT)
        return dict(date_start=date_start,
                    date_end=date_end)
    else:
        return (date_start, date_end)


def current_period(request):
    """
    Return the current period, either default or from session.

    TODO: mix together with current_start_end_dates (but is has a lot
    of impact)
    """
    return request.session.get(SESSION_DATE_PERIOD, PERIOD_DAY)
