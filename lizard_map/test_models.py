import datetime

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase
from django.test.client import Client


from lizard_map.models import ExtentMixin
from lizard_map.models import PeriodMixin
from lizard_map.models import WorkspaceEdit


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


class Extent(ExtentMixin):
    pass


class ExtentMixinTest(TestCase):
    def setUp(self):
        pass

    def test_smoke(self):
        e = Extent(xmin=1, ymin=1.5, xmax=2, ymax=3)
        e.save()

    def test_extent(self):
        e = Extent(xmin=1, ymin=1.5, xmax=2, ymax=3)
        e.save()
        result = e.extent()
        expected = (1.0, 1.5, 2.0, 3.0)
        self.assertEquals(result, expected)


class WorkspaceEditTest(TestCase):
    def setUp(self):
        self.client = Client()
        session_store = SessionStore(session_key='session_key')
        session_store.save()
        self.session = Session.objects.get(pk='session_key')

    def test_get_or_create(self):
        """Edit-workspace get_or_create with only a session"""
        ws = WorkspaceEdit.get_or_create(self.session)
        self.assertTrue(ws.id)

    def test_get_or_create2(self):
        """Edit-workspace get_or_create with user and session"""
        user = User(username='pony', password='pink')
        user.save()
        ws = WorkspaceEdit.get_or_create(
            self.session, user=user)
        self.assertTrue(ws.id)

    def test_get_or_create5(self):
        """Edit-workspace get_or_create gets same workspace based on session"""
        ws = WorkspaceEdit.get_or_create(self.session)
        self.assertTrue(ws.id)
        ws2 = WorkspaceEdit.get_or_create(self.session)
        self.assertEquals(ws.id, ws2.id)

    def test_get_or_create6(self):
        """Edit-workspace get_or_create based on session or user"""
        user = User(username='pony', password='pink')
        user.save()

        ws = WorkspaceEdit.get_or_create(
            self.session, user=user)
        self.assertTrue(ws.id)

        ws_user = WorkspaceEdit.get_or_create(
            self.session,
            user=user)
        self.assertEquals(ws.id, ws_user.id)

        ws_session = WorkspaceEdit.get_or_create(
            self.session)
        self.assertEquals(ws.id, ws_session.id)

    def test_get_or_create7(self):
        """Edit-workspace get_or_create workspace cornercase.

        Defined user has preference over defined session."""
        user = User(username='pony', password='pink')
        user.save()
        user2 = User(username='reinout', password='annie')
        user2.save()
        session_store = SessionStore(session_key='other_session')
        session_store.save()
        other_session = Session.objects.get(pk='other_session')

        ws = WorkspaceEdit.get_or_create(
            other_session, user=user)
        self.assertTrue(ws.id)

        ws_user = WorkspaceEdit.get_or_create(
            self.session, user=user)
        self.assertEquals(ws.id, ws_user.id)

        # Don't find anything: create new workspace
        ws_other = WorkspaceEdit.get_or_create(
            other_session, user=user2)
        self.assertNotEquals(ws.id, ws_other.id)
