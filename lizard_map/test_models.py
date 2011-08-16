import datetime

from django.test import TestCase


from lizard_map.models import PeriodMixin


class Period(PeriodMixin):
    """Test class to instantiate PeriodMixin"""
    pass


class PeriodMixinTest(TestCase):
    def setUp(self):
        pass

    def test_smoke(self):
        p = Period()
        p.save()

    def test_period_absolute(self):
        """
        Using absolute period.
        """
        now = datetime.datetime(2011, 8, 15)
        p = Period(
            dt_start=datetime.datetime(2011, 8, 5),
            dt_end=datetime.datetime(2011, 8, 15),
            absolute=True)

        # Testing period.
        dt_start, dt_end = p.period(now=now)
        self.assertEquals(dt_start, datetime.datetime(2011, 8, 5))
        self.assertEquals(dt_end, datetime.datetime(2011, 8, 15))

        # By default, the time is dt, unless otherwise specified.
        dt = p.time(now=now)
        self.assertEquals(dt, datetime.datetime(2011, 8, 15))

    def test_period_absolute(self):
        """
        Using absolute period with custom time.
        """
        now = datetime.datetime(2011, 8, 15)
        p = Period(
            dt_start=datetime.datetime(2011, 8, 5),
            dt_end=datetime.datetime(2011, 8, 15),
            dt=datetime.datetime(2011, 8, 16),
            absolute=True,
            custom_time=True)

        # By default, the time is dt, unless otherwise specified.
        dt = p.time(now=now)
        self.assertEquals(dt, datetime.datetime(2011, 8, 16))

    def test_period_relative(self):
        """
        Using relative period.
        """
        now = datetime.datetime(2011, 8, 15)
        p = Period(
            td_start=-10.0,
            td_end=0.0)

        # Testing period.
        dt_start, dt_end = p.period(now=now)
        self.assertEquals(dt_start, datetime.datetime(2011, 8, 5))
        self.assertEquals(dt_end, datetime.datetime(2011, 8, 15))

        # By default, the time is dt, unless otherwise specified.
        dt = p.time(now=now)
        self.assertEquals(dt, datetime.datetime(2011, 8, 15))

    def test_period_relative_custom(self):
        """
        Using relative period, custom time.
        """
        now = datetime.datetime(2011, 8, 15)
        p = Period(
            td_start=-10.0,
            td_end=0.0,
            td=1.0,
            custom_time=True)

        # By default, the time is dt, unless otherwise specified.
        dt = p.time(now=now)
        self.assertEquals(dt, datetime.datetime(2011, 8, 16))

    def test_period_not_specified(self):
        """
        If period is not fully specified, return None(s).

        Depending on fields absolute and custom_time, some of the
        fields dt_start.. td must be specified.
        """
        now = datetime.datetime(2011, 8, 15)
        p = Period()

        dt_start, dt_end = p.period(now=now)
        self.assertEquals(dt_start, None)
        self.assertEquals(dt_end, None)

        dt = p.time(now=now)
        self.assertEquals(dt, None)

    def test_period_not_specified_fallback(self):
        """
        Return fallback values.
        """
        now = datetime.datetime(2011, 8, 15)
        expected_dt_start = datetime.datetime(2011, 8, 5)
        expected_dt_end = datetime.datetime(2011, 8, 16)
        p = Period()

        dt_start, dt_end = p.period(now=now, fallback=True)
        self.assertEquals(dt_start, expected_dt_start)
        self.assertEquals(dt_end, expected_dt_end)

        dt = p.time(now=now, fallback=True)
        self.assertEquals(dt, now)

