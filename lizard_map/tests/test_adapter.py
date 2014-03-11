import datetime

import pytz

from django.test import TestCase
from django.test.utils import override_settings

from lizard_map import adapter


def utc_datetime(*args, **kwargs):
    kwargs["tzinfo"] = pytz.timezone('UTC')
    return datetime.datetime(*args, **kwargs)


@override_settings(TIME_ZONE="Europe/Amsterdam")
class TestMkJsTimeStamp(TestCase):
    def test_epoch_datetime_returns_3600(self):
        dt = utc_datetime(
            year=1970,
            month=1,
            day=1,
            hour=0,
            minute=0)
        print dt

        # This is the start of the epoch. This time of the year,
        # Europe/Amsterdam is 1 hour ahead of UTC, so the function
        # should return "1970-01-01T01:00+00:00"
        self.assertEquals(
            adapter.mk_js_timestamp(dt),
            "1970-01-01T01:00:00+00:00")

    def test_june_1_returns_correctly(self):
        # This turns out to be a trick question -- in 1970 we didn't
        # have summertime yet!
        dt = utc_datetime(
            year=1970,
            month=6,
            day=1,
            hour=0,
            minute=0)

        self.assertEquals(
            adapter.mk_js_timestamp(dt),
            "1970-06-01T01:00:00+00:00")

    def test_2013_jan_1_correct(self):
        dt = utc_datetime(
            year=2013,
            month=1,
            day=1,
            hour=0,
            minute=0)
        self.assertEquals(
            adapter.mk_js_timestamp(dt),
            "2013-01-01T01:00:00+00:00")

    def test_2013_jun_1_correct(self):
        # summer 2013 IS summertime (+2 hours).
        dt = utc_datetime(
            year=2013,
            month=6,
            day=1,
            hour=0,
            minute=0)
        self.assertEquals(
            adapter.mk_js_timestamp(dt),
            "2013-06-01T02:00:00+00:00")


class TestMakePercentileLabel(TestCase):
    def test_make_percentile_label(self):
        with self.settings(LANGUAGE_CODE='nl'):
            orig_label = u"label"
            percentiles = (0.1, 0.2, 0.8, 0.9)

            label = adapter._make_percentile_label(orig_label, percentiles)

            self.assertEquals(
                label,
                u"label (met 10% - 90% percentiel, 20% - 80% percentiel)")
