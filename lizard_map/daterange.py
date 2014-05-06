"""Handle the date range setting and remembering
"""
import datetime
import logging

from django.conf import settings

import pytz

# NOTE: this module is obsolete as date ranges are entirely handled in
# javascript and should be passed as request parameter


logger = logging.getLogger(__name__)

# Session data postfixed with '_3' as the meaning changed between versions.
SESSION_DT_RANGETYPE = 'dt_rangetype_3'
SESSION_DT_START = 'dt_start_3'
SESSION_DT_END = 'dt_end_3'

default_start_days = getattr(settings, 'DEFAULT_START_DAYS', -2)
default_end_days = getattr(settings, 'DEFAULT_END_DAYS', 0)


def default_start(now):
    """Return default start date when period is PERIOD_OTHER."""
    return now + datetime.timedelta(days=default_start_days)


def default_end(now):
    """Return default end date when period is PERIOD_OTHER."""
    return now + datetime.timedelta(days=default_end_days)


def current_period(request):
    """
    Return the current period, either default or from session.

    TODO: mix together with current_start_end_dates (but is has a lot
    of impact)
    """
    default_period = getattr(settings, 'DEFAULT_RANGE_TYPE', 'week_plus_one')

    if request is None:
        return default_period
    else:
        return request.session.get(SESSION_DT_RANGETYPE, default_period)


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
    today = datetime.datetime.now(tz=pytz.UTC)

    session = request.session
    dt_start = session.get(SESSION_DT_START, default_start(today))
    dt_end = session.get(SESSION_DT_END, default_end(today))

    if for_form:
        return dict(dt_start=dt_start, dt_end=dt_end)
    else:
        return (dt_start, dt_end)
