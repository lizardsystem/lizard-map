import datetime

from django.utils.translation import ugettext as _
import pytz

ALL = 1
YEAR = 2
QUARTER = 3
MONTH = 4
WEEK = 5
DAY = 6

QUARTERS = {
    0: _("Quarter 1"),
    1: _("Quarter 2"),
    2: _("Quarter 3"),
    3: _("Quarter 4"),
    }

MONTHS = {
    1: _("January"),
    2: _("February"),
    3: _("March"),
    4: _("April"),
    5: _("May"),
    6: _("June"),
    7: _("July"),
    8: _("August"),
    9: _("September"),
    10: _("October"),
    11: _("November"),
    12: _("December"),
    }


def next_all(dt):
    """
    Return period that is in the future for sure.
    """
    return (datetime.datetime(2100, 1, 1, tzinfo=pytz.UTC),
            datetime.datetime(2200, 1, 1, tzinfo=pytz.UTC))


def next_year(dt):
    """
    Return 2-tuple of next year: start/end date.
    """
    dttuple = dt.timetuple()
    year = dttuple[0] + 1
    return (datetime.datetime(year, 1, 1, tzinfo=pytz.UTC),
            datetime.datetime(year + 1, 1, 1, tzinfo=pytz.UTC))


def next_quarter(dt):
    """
    Return 2-tuple of next quarter: start/end date.
    """
    dttuple = dt.timetuple()
    year = dttuple[0]
    month = ((dttuple[1] - 1) / 3 + 1) * 3
    if month > 11:
        month %= 12
        year += 1
    next_quarter_month = month + 3
    next_quarter_year = year
    if next_quarter_month > 11:
        next_quarter_month %= 12
        next_quarter_year += 1
    return (
        datetime.datetime(year, month + 1, 1, tzinfo=pytz.UTC),
        datetime.datetime(next_quarter_year,
                          next_quarter_month + 1,
                          1,
                          tzinfo=pytz.UTC))


def next_month(dt):
    """
    Return 2-tuple of next month: start/end date.
    """
    dttuple = dt.timetuple()
    year = dttuple[0]
    month = dttuple[1]  # - 1 + 1
    if month > 11:
        month %= 12
        year += 1
    next_month_month = month + 1
    next_month_year = year
    if next_month_month > 11:
        next_month_month %= 12
        next_month_year += 1
    return (
        datetime.datetime(year, month + 1, 1, tzinfo=pytz.UTC),
        datetime.datetime(next_month_year,
                          next_month_month + 1,
                          1,
                          tzinfo=pytz.UTC))


def next_week(dt):
    """
    Return 2-tuple of next week: start/end date. Week starts on monday.
    """
    day = datetime.datetime(*dt.timetuple()[:3], tzinfo=pytz.UTC)
    days_to_next_week = 7 - day.weekday()
    day += datetime.timedelta(days=days_to_next_week)
    return day, day + datetime.timedelta(weeks=1)


def next_day(dt):
    """
    Return 2-tuple of next week: start/end date.
    """
    day = datetime.datetime(*dt.timetuple()[:3], tzinfo=pytz.UTC)
    day += datetime.timedelta(days=1)
    return day, day + datetime.timedelta(days=1)


def calc_aggregation_periods(start_date, end_date, aggregation_period):
    """
    Return list of 2-tuples with startdate/enddates.

    TODO: explain what it does. A 'list of tuples' doesn't say a thing about
    what the list really is. I surmise some sort of list of weeks (first and
    last partial) or someting like that?

    """
    periods = []
    next_period_functions = {
        ALL: next_all,
        YEAR: next_year,
        QUARTER: next_quarter,
        MONTH: next_month,
        WEEK: next_week,
        DAY: next_day}
    next_period = next_period_functions[int(aggregation_period)]

    next_period_start, next_period_end = next_period(start_date)
    periods.append((start_date, min(next_period_start, end_date)))
    while next_period_start < end_date:
        periods.append((next_period_start,
                        min(next_period_end, end_date)))
        (next_period_start,
         next_period_end) = next_period(next_period_start)
    return periods


def fancy_period(start_date, end_date, aggregation_period):
    """Return fancy string of (start_date, end_date).

    The format is determined by aggregation_period.
    """

    period_formats = {
        ALL: lambda a, b: _("Whole period"),
        YEAR: lambda a, b: a.strftime("%Y"),
        QUARTER: lambda a, b: "%s %s" % (
            QUARTERS[(a.month - 1) / 3], a.strftime("%Y")),
        MONTH: lambda a, b: "%s %s" % (MONTHS[a.month], a.strftime("%Y")),
        WEEK: lambda a, b: a.strftime("%Y %m %d"),
        DAY: lambda a, b: a.strftime("%Y %m %d"),
        }
    return period_formats[aggregation_period](start_date, end_date)
