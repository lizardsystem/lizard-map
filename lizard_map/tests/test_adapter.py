import datetime

from django.test import TestCase
from django.test.utils import override_settings

from lizard_map import adapter


@override_settings(TIME_ZONE="Europe/Amsterdam")
class TestMkJsTimeStamp(TestCase):
    def test_epoch_datetime_returns_3600(self):
        dt = datetime.datetime(
            year=1970,
            month=1,
            day=1,
            hour=0,
            minute=0)

        # This is the start of the epoch. This time of the year,
        # Europe/Amsterdam is 1 hour ahead of UTC, so the function
        # should return 3600000.0 ms (1 hour).
        self.assertEquals(
            adapter.mk_js_timestamp(dt),
            3600000.0)

    def test_june_1_returns_correctly(self):
        # June 1 of 1970 is 31+28+31+30+31 days later,
        # or 151 * 3600 * 24 = 13046400 seconds later.

        # This turns out to be a trick question -- in 1970 we didn't
        # have summertime yet!
        dt = datetime.datetime(
            year=1970,
            month=6,
            day=1,
            hour=0,
            minute=0)

        self.assertEquals(
            adapter.mk_js_timestamp(dt),
            13046400 * 1000.0 + 3600000.0)

    def test_2013_jan_1_correct(self):
        # Apparently jan 1, 2013 is 1356998400 seconds since the epoch.
        dt = datetime.datetime(
            year=2013,
            month=1,
            day=1,
            hour=0,
            minute=0)
        self.assertEquals(
            adapter.mk_js_timestamp(dt),
            (1356998400 + 3600) * 1000.0)

    def test_2013_jun_1_correct(self):
        # Apparently jan 1, 2013 is 1356998400 seconds since the epoch.
        # jun 1 is 13046400 seconds later (see above),
        # and summer 2013 IS summertime (+2 hours).
        dt = datetime.datetime(
            year=2013,
            month=6,
            day=1,
            hour=0,
            minute=0)
        self.assertEquals(
            adapter.mk_js_timestamp(dt),
            (1356998400 + 13046400 + 7200) * 1000.0)


class TestMakePercentileLabel(TestCase):
    def test_make_percentile_label(self):
        with self.settings(LANGUAGE_CODE='nl'):
            orig_label = u"label"
            percentiles = (0.1, 0.2, 0.8, 0.9)

            label = adapter._make_percentile_label(orig_label, percentiles)

            self.assertEquals(
                label,
                u"label (met 10% - 90% percentiel, 20% - 80% percentiel)")
