import datetime
from lizard_map.models import ALL, YEAR, QUARTER, MONTH, WEEK, DAY


def next_all(dt):
    """
    Return period that is in the future for sure
    """
    return datetime.date(2100, 1, 1), datetime.date(2200, 1, 1)


def next_year(dt):
    """
    Returns 2-tuple of next year: start/end date
    """
    dttuple = dt.timetuple()
    year = dttuple[0] + 1
    return datetime.date(year, 1, 1), datetime.date(year + 1, 1, 1)


def next_quarter(dt):
    """
    Returns 2-tuple of next quarter: start/end date
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
        datetime.date(year, month + 1, 1),
        datetime.date(next_quarter_year, next_quarter_month + 1, 1))


def next_month(dt):
    """
    Returns 2-tuple of next month: start/end date
    """
    dttuple = dt.timetuple()
    year = dttuple[0]
    month = dttuple[1]  # - 1 + 1
    if month > 11:
        month %= 12
        year += 1
    next_quarter_month = month + 1
    next_quarter_year = year
    if next_quarter_month > 11:
        next_quarter_month %= 12
        next_quarter_year += 1
    return (
        datetime.date(year, month + 1, 1),
        datetime.date(next_quarter_year, next_quarter_month + 1, 1))


def next_week(dt):
    """
    Returns 2-tuple of next week: start/end date
    """
    day = datetime.date(*dt.timetuple()[:3])
    days_to_next_week = 6 - day.weekday()
    if days_to_next_week == 0:
        days_to_next_week = 7
    day += datetime.timedelta(days=days_to_next_week)
    return day, day + datetime.timedelta(weeks=1)


def next_day(dt):
    """
    Returns 2-tuple of next week: start/end date
    """
    day = datetime.date(*dt.timetuple()[:3])
    day += datetime.timedelta(days=1)
    return day, day + datetime.timedelta(days=1)


def calc_aggregation_periods(start_date, end_date, aggregation_period):
    """Returns list of 2-tuples with startdate/enddates.
    """
    periods = []
    next_period_functions = {
        ALL: next_all,
        YEAR: next_year,
        QUARTER: next_quarter,
        MONTH: next_month,
        WEEK: next_week,
        DAY: next_day}
    next_period = next_period_functions[aggregation_period]

    next_period_start, next_period_end = next_period(start_date)
    periods.append((start_date, min(next_period_start, end_date)))
    while next_period_start < end_date:
        periods.append((next_period_start,
                        min(next_period_end, end_date)))
        (next_period_start,
         next_period_end) = next_period(next_period_start)
    return periods
