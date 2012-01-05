"""Handle the date range setting and remembering
"""
import datetime
import logging

from django.conf import settings
#from django.http import HttpResponseRedirect
#from django.template import RequestContext
#from django.shortcuts import render_to_response

# from lizard_map.forms import DateRangeForm


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

# Session data postfixed with '_2' as the meaning changed between versions.
SESSION_DT_PERIOD = 'dt_period_2'
SESSION_DT_START = 'dt_start_2'
SESSION_DT_END = 'dt_end_2'

DUTCH_DATE_FORMAT = '%d/%m/%Y'
# ^^^ This is what jquery ui with the Dutch locale does for Reinout.

default_start_days = getattr(settings, 'DEFAULT_START_DAYS', -1000)
default_end_days = getattr(settings, 'DEFAULT_END_DAYS', 10)


def default_start(now):
    """Return default start date when period is PERIOD_OTHER."""
    return now + datetime.timedelta(days=default_start_days)


def default_end(now):
    """Return default end date when period is PERIOD_OTHER."""
    return now + datetime.timedelta(days=default_end_days)


def _compute_start_end(daterange, session, now=None):
    """Compute and return the (start, end) for the given date range.

    If the given date range does not specify a start (or end) date & time, this
    function returns a default start (or end) date & time.

    Parameters:
      *date_range*
        dictionary that may specify the 'dt_start' and 'dt_end' date & time(s)
      *now*
        datetime.datetime that specifies the current date & time

    """
    if now is None:
        now = datetime.datetime.now()

    try:
        dt_start = daterange['dt_start']
        if dt_start is None:
            dt_start = session[SESSION_DT_START]
    except (KeyError, TypeError):
        dt_start = default_start(now)

    try:
        dt_end = daterange['dt_end']
        if dt_end is None:
            dt_end = session[SESSION_DT_END]
    except (KeyError, TypeError):
        dt_end = default_end(now)

    if dt_start > dt_end:
        dt_end = dt_start + datetime.timedelta(days=1)

    return dt_start, dt_end


def compute_and_store_start_end(session, date_range, now=None):
    """Store the (start, end) of the given date range in the given session.

    Parameters:
      *session*
        dictionary to store the start and end datetime.datetime (can also be a
        HttpRequest.session)
      *date_range*
        dictionary that may specify the 'dt_start' and 'dt_end' date & time(s)
      *now*
        datetime.datetime to represent the current date and time

    """
    period = int(date_range['period'])
    session[SESSION_DT_PERIOD] = period

    if period == PERIOD_OTHER:
        start, end = _compute_start_end(date_range, session, now=now)
        session[SESSION_DT_START] = start
        session[SESSION_DT_END] = end


# def set_date_range(request, template='lizard_map/daterange.html',
#                    now=None):
#     """View: store the date range in the session and redirect.

#     POST must contain DateRangeForm fields.
#     now is a datetime field, used for testing.
#     """
#     if request.method == 'POST':
#         form = DateRangeForm(request.POST)
#         if form.is_valid():
#             came_from = request.META.get('HTTP_REFERER', '/')
#             date_range = form.cleaned_data
#             compute_and_store_start_end(request.session, date_range, now=now)

#             return HttpResponseRedirect(came_from)
#     else:
#         # Invalid, should never happen. You're probably surfing to the
#         # set_date_range url.
#         form = DateRangeForm()

#     # Form rendering just for debugging errors.
#     return render_to_response(
#         template,
#         {'date_range_form': form},
#         context_instance=RequestContext(request))


def current_period(request):
    """
    Return the current period, either default or from session.

    TODO: mix together with current_start_end_dates (but is has a lot
    of impact)
    """
    default_period = getattr(settings, 'DEFAULT_PERIOD', PERIOD_DAY)

    if request is None:
        return default_period
    else:
        return request.session.get(SESSION_DT_PERIOD, default_period)


def current_start_end_dates(request, for_form=False, today=None,
                            retrieve_period_function=current_period):
    """Return the current start datetime and end datetime.

    If for_form is True, this function returns the datetime's as a dictionary
    so the client can pass that directly into a form class. If for_form is not
    True, this functions returns them as a tuple.

    Other parameter:
      *today*
         datetime to initialize the current datetime (for testing purposes)
      *retrieve_period_function*
         function to retrieve the period type (for testing purposes)

    """
    if today is None:
        today = datetime.datetime.now()

    period = retrieve_period_function(request)

    if period == PERIOD_OTHER:
        session = request.session
        dt_start = session.get(SESSION_DT_START, default_start(today))
        dt_end = session.get(SESSION_DT_END, default_end(today))
    else:
        period_start, period_end = PERIOD_DAYS[period]
        dt_start = period_start + today
        dt_end = period_end + today

    if for_form:
        return dict(dt_start=dt_start, dt_end=dt_end)
    else:
        return (dt_start, dt_end)
