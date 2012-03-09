import datetime
import unittest

from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.utils import simplejson as json

from lizard_map.adapter import Graph
from lizard_map.adapter import parse_identifier_json
from lizard_map.animation import AnimationSettings
from lizard_map.daterange import default_start
from lizard_map.daterange import default_end
from lizard_map.daterange import PERIOD_DAY
from lizard_map.daterange import PERIOD_OTHER
from lizard_map.daterange import PERIOD_DAYS
from lizard_map.daterange import SESSION_DT_PERIOD
from lizard_map.daterange import SESSION_DT_END
from lizard_map.daterange import SESSION_DT_START
from lizard_map.daterange import compute_and_store_start_end
from lizard_map.daterange import current_start_end_dates
from lizard_map.daterange import current_period
from lizard_map.dateperiods import ALL
from lizard_map.dateperiods import YEAR
from lizard_map.dateperiods import QUARTER
from lizard_map.dateperiods import MONTH
from lizard_map.dateperiods import WEEK
from lizard_map.dateperiods import DAY
from lizard_map.dateperiods import calc_aggregation_periods
from lizard_map.dateperiods import fancy_period
from lizard_map.fields import Color
from lizard_map.mapnik_helper import database_settings
from lizard_map.models import Legend
from lizard_map.models import WorkspaceEdit
from lizard_map.models import WorkspaceEditItem
#from lizard_map.models import WorkspaceCollage
#from lizard_map.models import WorkspaceCollageSnippetGroup
from lizard_map.operations import AnchestorRegistration
from lizard_map.operations import CycleError
from lizard_map.operations import named_list
from lizard_map.operations import tree_from_list
from lizard_map.operations import unique_list
from lizard_map.utility import float_to_string
from lizard_map.utility import short_string
from lizard_map.workspace import WorkspaceItemAdapter
#from lizard_map.workspace import WorkspaceManager
from lizard_map.templatetags import workspaces
import lizard_map.admin
import lizard_map.coordinates
import lizard_map.daterange
import lizard_map.layers
import lizard_map.models
import lizard_map.urls
import lizard_map.views


class ViewsTest(TestCase):
    fixtures = ('lizard_map', )

    def setUp(self):
        self.client = Client()
        self.workspace = WorkspaceEdit(session_key='mock')
        self.workspace.save()
        # self.collage = WorkspaceCollage(workspace=self.workspace)
        # self.collage.save()

    # def test_homepage(self):
    #     url = reverse('lizard_map_workspace',
    #                   kwargs={'workspace_id': self.workspace.id})
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)

    def test_workspace_edit_wms(self):
        url = reverse('lizard_map_workspace_edit_wms')
        url += ('?LAYERS=basic&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&'
                'STYLES=&EXCEPTIONS=application%2Fvnd.ogc.se_inimage&'
                'FORMAT=image%2Fjpeg&SRS=EPSG%3A900913&'
                'BBOX=430987.5469813,6803449.8497827,'
                '669012.4530187,6896550.1502173&'
                'WIDTH=1557&HEIGHT=609')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # def test_collage(self):
    #     url = reverse('lizard_map.collage',
    #                   kwargs={'collage_id': self.collage.id})
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)

    # def test_collage_popup(self):
    #     url = reverse('lizard_map.collage_popup',
    #                   kwargs={'collage_id': self.collage.id})
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)

    def test_search_coordinates(self):
        url = reverse('lizard_map.search_coordinates')
        url += ('?x=430987.5469813&y=6817896.448126&radius=100&'
                'user_workspace_id=%d' % self.workspace.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_search_name(self):
        url = reverse('lizard_map.search_name')
        url += ('?x=430987.5469813&y=6817896.448126&radius=100&'
                'user_workspace_id=%d' % self.workspace.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_map_location_save(self):
        """Save map location, see if it doesn't crash
        """
        client = Client()
        url = reverse('lizard_map.map_location_save')
        response = client.post(url, {'left': 100, 'top': 100,
                                     'right': 150, 'bottom': 150,
                                     'base_layer_name': 'Google standard'})
        self.assertEqual(response.status_code, 200)

    def test_map_location_load_default(self):
        """Save map location, then load it back.
        """
        url_load = reverse('lizard_map.map_location_load_default')
        response_load = self.client.get(url_load)
        self.assertEqual(response_load.status_code, 200)
        result = json.loads(response_load.content)
        self.assertEqual(
            result['extent'],
            {'top': '6964942', 'right': '1254790',
             'left': '-14675', 'bottom': '6668977'})

    def test_mixins(self):
        view = lizard_map.views.AppView()

        gtc = view.google_tracking_code()
        if gtc is not None:
            self.assertIsInstance(gtc, str)

        self.assertIsNone(gtc)


class TestDateRange(TestCase):
    """Test daterange.py"""

    def setUp(self):

        class Mock(dict):
            pass

        self.request = Mock()
        self.request.session = Mock()
        self.today = datetime.datetime(2011, 4, 21)
        self.almost_one_day = datetime.timedelta(
            hours=23, minutes=59, seconds=59)

    def _test_set_date_range(self, request):

        #set_date_range(self.request, now=self.today)
        data = {'period': request.POST.get('period', None),
                'dt_start': request.POST.get('dt_start', None),
                'dt_end': request.POST.get('dt_end', None)}
        form = lizard_map.forms.DateRangeForm(data)  # Fill in daterange
        form.is_valid()  # it must succeed

        view = lizard_map.views.DateRangeView()
        view.request = request  # Manually put request in view
        view.form_valid_action(form)  # Actually setting date range.

        # Get current period, dt_start, dt_end
        period = current_period(self.request)
        dt_start, dt_end = current_start_end_dates(
            self.request, today=self.today)

        return period, dt_start, dt_end

    def test_current_start_end_dates(self):
        dt_start, dt_end = current_start_end_dates(
            self.request, today=self.today)
        dt_start_expected = self.today + PERIOD_DAYS[PERIOD_DAY][0]
        dt_end_expected = self.today + PERIOD_DAYS[PERIOD_DAY][1]

        self.assertEquals(dt_start, dt_start_expected)
        self.assertEquals(dt_end, dt_end_expected)

    def test_current_period(self):
        """Test default period."""
        period = current_period(self.request)
        self.assertEquals(period, PERIOD_DAY)

    def test_set_date_range(self):
        """Set date range to period_day, then retrieve it back"""
        # Fake Post
        self.request.method = 'POST'
        self.request.POST = {
            'period': str(PERIOD_DAY)}
        self.request.META = {}

        period, dt_start, dt_end = self._test_set_date_range(self.request)

        self.assertEquals(period, PERIOD_DAY)
        self.assertEquals(dt_start, self.today + PERIOD_DAYS[PERIOD_DAY][0])
        self.assertEquals(dt_end, self.today + PERIOD_DAYS[PERIOD_DAY][1])

    def test_set_date_range2(self):
        """Set custom date range, then retrieve it back"""
        # Fake Post
        self.request.method = 'POST'
        dt_start_expected = datetime.datetime(2011, 5, 25)
        dt_end_expected = datetime.datetime(2011, 5, 25, 23, 59, 59)
        self.request.POST = {
            'period': str(PERIOD_OTHER),
            'dt_start': dt_start_expected,
            'dt_end': dt_end_expected}
        self.request.META = {}

    #     period, dt_start, dt_end = self._test_set_date_range(self.request)
    #     self.assertEquals(period, PERIOD_OTHER)
    #     self.assertEquals(dt_start, dt_start_expected)
    #     self.assertEquals(dt_end, dt_end_expected)
    def test_set_date_range3(self):
        """Set start date after end date: result must have dt_start<dt_end"""
        timedelta_start = datetime.timedelta(days=20)
        timedelta_end = datetime.timedelta(days=-15)

        # Fake Post
        self.request.method = 'POST'
        self.request.POST = {
            'period': str(PERIOD_OTHER),
            'dt_start': self.today + timedelta_start,
            'dt_end': self.today + timedelta_end}
        self.request.META = {}

        period, dt_start, dt_end = self._test_set_date_range(self.request)

        self.assertEquals(period, PERIOD_OTHER)
        self.assertTrue(dt_start < dt_end)

    # # TODO: Check met Pieter
    # def do_deltatime(
    #     self, period_expected,
    #     timedelta_start_expected, timedelta_end_expected):
    #     """Easy testing deltatime_range."""

    #     daterange = {'dt_start': self.today + timedelta_start_expected,
    #                  'dt_end': self.today + timedelta_end_expected,
    #                  'period': period_expected}
    #     period, timedelta_start, timedelta_end = deltatime_range(
    #         daterange, now=self.today)

    #     # Test on day accuracy, because "almost_one_day" is added to end.
    #     self.assertEquals(period, period_expected)
    #     self.assertEquals(timedelta_start.days,
    #                 timedelta_start_expected.days)
    #     self.assertEquals(timedelta_end.days, timedelta_end_expected.days)

    # def test_deltatime_range(self):
    #     """Deltatime_range"""
    #     timedelta_start_expected = datetime.timedelta(-1000)
    #     timedelta_end_expected = datetime.timedelta(20)
    #     period_expected = PERIOD_OTHER
    #     self.do_deltatime(
    #         period_expected,
    #         timedelta_start_expected, timedelta_end_expected)

    # def test_deltatime_range2(self):
    #     """Deltatime_range"""
    #     timedelta_start_expected = datetime.timedelta(-1)
    #     timedelta_end_expected = datetime.timedelta(0)
    #     period_expected = PERIOD_DAY
    #     self.do_deltatime(
    #         period_expected,
    #         timedelta_start_expected, timedelta_end_expected)

    # def test_deltatime_range3(self):
    #     """Deltatime_range"""
    #     timedelta_start_expected = datetime.timedelta(-365)
    #     timedelta_end_expected = datetime.timedelta(0)
    #     period_expected = PERIOD_YEAR
    #     self.do_deltatime(
    #         period_expected,
    #         timedelta_start_expected, timedelta_end_expected)


class TestAnimationSettings(TestCase):
    """Tests for animation.py."""

    def _fill_date_range(self):
        """Helper method: fill session with date range info.

        date_start is 730119 days from day_one
        date_end is 731215 days from day_one
        """
        twothousand = datetime.datetime(year=2000, month=1, day=1)
        twothousandthree = datetime.datetime(year=2003, month=1, day=1)
        self.request.session[SESSION_DT_PERIOD] = PERIOD_OTHER
        self.request.session[SESSION_DT_START] = twothousand
        self.request.session[SESSION_DT_END] = twothousandthree
        day_one = datetime.datetime(1979, 5, 25)
        self.date_start_days = (twothousand - day_one).days
        self.date_end_days = (twothousandthree - day_one).days

    def _date_range_helper(self, today):
        """Make sure _fill_date_range() works."""
        self._fill_date_range()
        start, end = current_start_end_dates(self.request, today=today)
        self.assertEquals(start.year, 2000)
        self.assertEquals(end.year, 2003)

    def setUp(self):

        class Mock(dict):
            pass

        self.request = Mock()
        self.request.session = Mock()
        self.today = datetime.datetime(2011, 4, 21)
        self._date_range_helper(today=self.today)  # Set the request datetimes

    def test_smoke(self):
        animation_settings = AnimationSettings(
            request=self.request, today=self.today)
        self.assertTrue(animation_settings)  # It exists.

    def test_session_initialisation(self):
        self.assertFalse('animation_settings' in self.request.session)
        AnimationSettings(self.request, today=self.today)
        self.assertTrue('animation_settings' in self.request.session)

    def test_slider_position(self):
        """Are the getters/setters working?"""
        animation_settings = AnimationSettings(
            self.request, today=self.today)
        animation_settings.slider_position = self.date_start_days + 100
        # print current_start_end_dates(self.request)
        self.assertTrue(self.request.session.modified)
        self.assertEquals(
            animation_settings.slider_position, self.date_start_days + 100)
        self.assertEquals(
            self.request.session['animation_settings']['slider_position'],
            self.date_start_days + 100)

    def test_initial_slider_position(self):
        """Slider position should be [max] if not initialised.
        In any case, it should not return a keyerror."""
        animation_settings = AnimationSettings(
            self.request, today=self.today)
        self.assertEquals(animation_settings.slider_position,
                          self.date_end_days)

    def test_initial_info_gathering(self):
        """Do we return the correct date range and position?"""
        self._fill_date_range()
        animation_settings = AnimationSettings(
            self.request, today=self.today)
        result = animation_settings.info()
        self.assertEquals(result['min'], self.date_start_days)
        self.assertEquals(result['max'], self.date_end_days)
        self.assertEquals(result['step'], 1)
        self.assertEquals(result['value'], self.date_end_days)
        self.assertEquals(result['selected_date'].year, 2003)

    def test_info_gathering(self):
        """Do we return the correct date range and position?"""
        self._fill_date_range()
        animation_settings = AnimationSettings(
            self.request, today=self.today)
        animation_settings.slider_position = self.date_start_days + 375
        result = animation_settings.info()
        self.assertEquals(result['min'], self.date_start_days)
        self.assertEquals(result['max'], self.date_end_days)
        self.assertEquals(result['step'], 1)
        self.assertEquals(result['value'], self.date_start_days + 375)
        self.assertEquals(result['selected_date'].year, 2001)

    def test_impossible_negative_corner_case(self):
        """Negative dates."""
        self._fill_date_range()
        animation_settings = AnimationSettings(
            self.request, today=self.today)
        animation_settings.slider_position = -400
        result = animation_settings.info()
        self.assertEquals(result['value'], self.date_start_days)

    def test_impossible_beyond_max_corner_case(self):
        """Value beyond the max possible."""
        self._fill_date_range()
        animation_settings = AnimationSettings(
            self.request, today=self.today)
        animation_settings.slider_position = 1000000
        result = animation_settings.info()
        # Max available.
        self.assertEquals(result['value'], self.date_end_days)

    def test_change_period_after(self):
        """
        Change period after setting animationsettings.
        """
        self._fill_date_range()
        animation_settings = AnimationSettings(
            self.request, today=self.today)
        animation_settings.slider_position = self.date_start_days + 10
        self.assertEquals(animation_settings.slider_position,
                          self.date_start_days + 10)

        # Now change "current date".
        self.request.session[SESSION_DT_END] = self.request.session[
            SESSION_DT_START] + datetime.timedelta(days=5)

        # Because the current date is changed, the slider position
        # should automatically change too.
        animation_settings = AnimationSettings(
            self.request, today=self.today)
        self.assertEquals(animation_settings.slider_position,
                          self.date_start_days + 5)


class UtilityTest(TestCase):
    """
    Tests utility.py, adapter.py, mapnik_helper.py
    """

    class MockSettings(object):
        pass

    def test_short_string(self):
        input_names = [
            'Loosdrechtse Plassen',
            'wie niet waagt, wie niet wint',
            'Reinout is een developer bij Nelen & Schuurmans',
            'Dit is nog een langere zin, deze moet ook goed werken',
            ]
        for name in input_names:
            short = short_string(name, 17)
            self.assertTrue(len(short) <= 17)
            self.assertEquals(short[:5], name[:5])

    def test_float_to_string(self):
        """Let's input some nice floats."""
        st = float_to_string(1.2345678)
        self.assertTrue(len(st) <= 10)
        self.assertEquals(st[:4], '1.23')

    def test_float_to_string2(self):
        """Let's input some nice floats."""
        st = float_to_string(12345.678)
        self.assertTrue(len(st) <= 10)
        self.assertEquals(st[:4], '1234')

    def test_float_to_string3(self):
        """Let's input some nice floats."""
        st = float_to_string(0.00000000012345)
        self.assertTrue(len(st) <= 10)
        self.assertEquals(st[:4], '1.23')
        self.assertTrue('e' in st)

    def test_float_to_string5(self):
        """Let's input some nice floats."""
        st = float_to_string(123456789012345)
        self.assertTrue(len(st) <= 10)
        self.assertEquals(st[:4], '1.23')
        self.assertTrue('e' in st)

    def test_float_to_string6(self):
        """Let's input some nice floats."""
        st = float_to_string(999999999.99)
        self.assertTrue(len(st) <= 10)
        self.assertEquals(st[:4], '1000')

    def test_float_to_string7(self):
        """Let's input a string."""
        self.assertEquals(float_to_string('string'), 'string')

    def test_float_to_string8(self):
        """Let's input a string."""
        st = float_to_string('1000')
        self.assertEquals(st, '1000.00')

    def test_parse_identifier_json(self):
        self.assertTrue(parse_identifier_json(
                '{%22testkey%22:%20%22testvalue%22}'))

    def test_graph(self):
        start_date = datetime.datetime(2010, 7, 1)
        end_date = datetime.datetime(2010, 10, 1)
        today = datetime.datetime(2010, 9, 8)
        graph = Graph(start_date, end_date, today=today)
        graph.add_today()
        graph.suptitle('hallo')
        graph.legend()
        self.assertTrue(graph.http_png())

    def test_database_settings(self):
        """
        See if correct database settings are fetched when using new
        style config.
        """
        settings = self.MockSettings()
        settings.DATABASES = {
            'default': {
                'ENGINE': 'postgresql_psycopg2',
                'HOST': 'database_host',
                'USER': 'database_user',
                'PASSWORD': 'database_password',
                'NAME': 'database_name',
                },
            }
        datasource, options = database_settings(user_settings=settings)
        self.assertEqual(options,
                         {'host': 'database_host',
                          'user': 'database_user',
                          'password': 'database_password',
                          'dbname': 'database_name'})
        self.assertTrue('PostGIS' in str(datasource))

    def test_database_settings2(self):
        """
        See if correct database settings are fetched when using old
        style config.
        """
        settings = self.MockSettings()
        settings.DATABASE_ENGINE = 'postgresql_psycopg2'
        settings.DATABASE_NAME = 'database_name'
        settings.DATABASE_HOST = 'database_host'
        settings.DATABASE_USER = 'database_user'
        settings.DATABASE_PASSWORD = 'database_password'

        datasource, options = database_settings(user_settings=settings)
        self.assertEqual(options,
                         {'host': 'database_host',
                          'user': 'database_user',
                          'password': 'database_password',
                          'dbname': 'database_name'})
        self.assertTrue('PostGIS' in str(datasource))

    def test_database_settings3(self):
        """
        Take new style config if both setting styles are present.
        """
        settings = self.MockSettings()
        settings.DATABASE_ENGINE = 'postgresql_psycopg2'
        settings.DATABASE_NAME = 'database_name_old'
        settings.DATABASE_HOST = 'database_host_old'
        settings.DATABASE_USER = 'database_user_old'
        settings.DATABASE_PASSWORD = 'database_password_old'
        settings.DATABASES = {
            'default': {
                'ENGINE': 'postgresql_psycopg2',
                'HOST': 'database_host',
                'USER': 'database_user',
                'PASSWORD': 'database_password',
                'NAME': 'database_name',
                },
            }

        datasource, options = database_settings(user_settings=settings)
        self.assertEqual(options,
                         {'host': 'database_host',
                          'user': 'database_user',
                          'password': 'database_password',
                          'dbname': 'database_name'})
        self.assertTrue('PostGIS' in str(datasource))

    # def test_create_layer_from_query(self):
    #     """Difficult to test, just see if it crashes or not. Currently
    #     crashes when db does not exist
    #     """
    #     settings = self.MockSettings()
    #     settings.DATABASES = {
    #         'default': {
    #             'ENGINE': 'postgresql_psycopg2',
    #             'HOST': 'database_host',
    #             'USER': 'database_user',
    #             'PASSWORD': 'database_password',
    #             'NAME': 'database_name',
    #             },
    #         }

    #     q = "select * from dummy;"
    #     projection = lizard_map.coordinates.RD
    #     layer = create_layer_from_query(q, projection,
    #                 user_settings=settings)


class WorkspaceItemAdapterTest(TestCase):

    def setUp(self):
        self.workspace = WorkspaceEdit()
        self.workspace.save()
        workspace_item = WorkspaceEditItem(workspace=self.workspace)
        workspace_item.save()
        layer_arguments = {}
        self.adapter = WorkspaceItemAdapter(workspace_item, layer_arguments)

    def test_smoke(self):
        self.assertTrue(self.adapter)

    def test_line_styles(self):
        identifiers = [{str(i): 'b'} for i in range(10)]
        line_styles = self.adapter.line_styles(identifiers)
        self.assertTrue(line_styles)
        self.assertEquals(len(line_styles.keys()), 10)

    def test_value_aggregate_default(self):
        # First, implement values function
        start_date = datetime.datetime(2010, 5, 25)
        end_date = datetime.datetime(2010, 6, 25)
        self.adapter.values = (
            lambda
            identifier, start_date, end_date:
                [{'datetime': start_date, 'value': 5.0, 'unit': 'none'},
                 {'datetime': end_date, 'value': 6.0, 'unit': 'none'}])
        aggregated_values = self.adapter.value_aggregate_default(
            {},
            {'min': None, 'max': None, 'avg': None, 'count_lt': 6,
             'count_gte': 6, 'percentile': 50},
            start_date,
            end_date)
        self.assertEqual(aggregated_values['min'], 5.0)
        self.assertEqual(aggregated_values['max'], 6.0)
        self.assertEqual(aggregated_values['avg'], 5.5)
        self.assertEqual(aggregated_values['count_lt'], 1)
        self.assertEqual(aggregated_values['count_gte'], 1)
        # Percentile value depends on definition...
        self.assertTrue(aggregated_values['percentile'] >= 5.0)
        self.assertTrue(aggregated_values['percentile'] <= 6.0)

    def test_symbol_url(self):
        self.assertTrue(self.adapter.symbol_url())

    def test_html_default_identifiers(self):
        identifiers = {}
        self.assertTrue(self.adapter.html_default(identifiers=identifiers))

    def test_legend_object_default(self):
        self.adapter.legend_object_default('no_name')

    def test_legend_default(self):
        legend_object = self.adapter.legend_object_default('no_name')
        self.adapter.legend_default(legend_object)


class DatePeriodsTest(TestCase):

    def test_calc_aggregation_periods_all(self):
        start_date = datetime.datetime(1979, 5, 25)
        end_date = datetime.datetime(1980, 4, 15)
        periods = calc_aggregation_periods(start_date, end_date, ALL)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], end_date)

    def test_calc_aggregation_periods_year(self):
        start_date = datetime.datetime(1979, 5, 25)
        end_date = datetime.datetime(1980, 4, 15)
        periods = calc_aggregation_periods(start_date, end_date, YEAR)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], datetime.datetime(1980, 1, 1))
        self.assertEqual(periods[1][0], datetime.datetime(1980, 1, 1))
        self.assertEqual(periods[1][1], end_date)

    def test_calc_aggregation_periods_quarter(self):
        start_date = datetime.datetime(1979, 5, 25)
        end_date = datetime.datetime(1980, 4, 15)
        periods = calc_aggregation_periods(start_date, end_date, QUARTER)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], datetime.datetime(1979, 7, 1))
        self.assertEqual(periods[-1][0], datetime.datetime(1980, 4, 1))
        self.assertEqual(periods[-1][1], end_date)

    def test_calc_aggregation_periods_month(self):
        start_date = datetime.datetime(1979, 5, 25)
        end_date = datetime.datetime(1980, 4, 15)
        periods = calc_aggregation_periods(start_date, end_date, MONTH)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], datetime.datetime(1979, 6, 1))
        self.assertEqual(periods[-1][0], datetime.datetime(1980, 4, 1))
        self.assertEqual(periods[-1][1], end_date)

    def test_calc_aggregation_periods_week(self):
        start_date = datetime.datetime(1979, 5, 25)  # It's a friday.
        end_date = datetime.datetime(1979, 7, 15)  # It's a sunday.
        periods = calc_aggregation_periods(start_date, end_date, WEEK)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], datetime.datetime(1979, 5, 28))
        self.assertEqual(periods[-1][0], datetime.datetime(1979, 7, 9))
        self.assertEqual(periods[-1][1], end_date)

    def test_calc_aggregation_periods_day(self):
        start_date = datetime.datetime(1979, 5, 25)
        end_date = datetime.datetime(1979, 7, 15)
        periods = calc_aggregation_periods(start_date, end_date, DAY)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], datetime.datetime(1979, 5, 26))
        self.assertEqual(periods[-1][0], datetime.datetime(1979, 7, 14))
        self.assertEqual(periods[-1][1], end_date)

    def test_fancy_period(self):
        start_date = datetime.datetime(1979, 5, 25)
        end_date = datetime.datetime(1979, 7, 15)
        self.assertTrue(fancy_period(start_date, end_date, ALL))
        self.assertTrue(fancy_period(start_date, end_date, YEAR))
        self.assertTrue(fancy_period(start_date, end_date, QUARTER))
        self.assertTrue(fancy_period(start_date, end_date, MONTH))
        self.assertTrue(fancy_period(start_date, end_date, WEEK))
        self.assertTrue(fancy_period(start_date, end_date, DAY))


class TestTemplateTags(TestCase):

    def test_float_or_exp(self):
        in_out = {0: '0.00',
                  0.0: '0.00',
                  123456: '123456.00',
                  -123456: '-123456.00',
                  123456.7891234: '123456.79',
                  0.01: '0.01',
                  0.001: '1.00e-03',
                  None: None,
                  'Reinout': 'Reinout',
                  }
        for value, expected in in_out.items():
            self.assertEquals(workspaces.float_or_exp(value), expected)


class ModelLegendTest(TestCase):

    def test_make_legend(self):
        legend = Legend(
            descriptor='default',
            min_color='ff0000',
            max_color='0000ff',
            too_low_color='111111',
            too_high_color='999999')
        legend.save()
        self.assertEquals(legend.min_color.r, 255)
        self.assertEquals(legend.max_color.r, 0)
        self.assertEquals(legend.max_color.b, 255)

    def test_color(self):
        """Testing the color object"""
        c = Color('ff8000')
        self.assertEquals(c.r, 255)
        self.assertEquals(c.g, 128)
        self.assertEquals(c.b, 0)

    def test_color2(self):
        c = Color(None)
        self.assertEquals(c.r, None)
        self.assertEquals(c.g, None)
        self.assertEquals(c.b, None)


class TestOperations(TestCase):

    def test_anchestor_registration(self):
        """Check basic functionality"""
        anchestors = AnchestorRegistration()
        self.assertFalse(anchestors.anchestor_of('child', 'parent'))
        anchestors.register_parent('child', 'parent')
        self.assertTrue(anchestors.anchestor_of('child', 'parent'))
        anchestors.register_parent('grandchild', 'child')
        self.assertTrue(anchestors.anchestor_of('grandchild', 'parent'))
        self.assertFalse(anchestors.anchestor_of('parent', 'grandchild'))

    def test_anchestor_registration2(self):
        """The anchestor registration doesn't mind cycles"""
        anchestors = AnchestorRegistration()
        anchestors.register_parent('child', 'parent')
        anchestors.register_parent('parent', 'child')
        self.assertTrue(anchestors.anchestor_of('child', 'parent'))
        self.assertTrue(anchestors.anchestor_of('parent', 'child'))

    def test_tree_from_list1(self):
        rows = []
        result_good = []
        result_function = tree_from_list(rows)
        self.assertEqual(result_function, result_good)

    def test_tree_from_list2(self):
        rows = [{'name': 'parent_name', 'parent': None},
                {'name': 'child_name', 'parent': 'parent_name'}]
        result_good = [
                {'name': 'parent_name',
                 'parent': None,
                 'children': [
                    {'name': 'child_name',
                     'parent': 'parent_name',
                     'children': []}]}]
        result_function = tree_from_list(
            rows,
            id_field='name',
            parent_field='parent',
            children_field='children',
            root_parent=None)
        self.assertEqual(result_function, result_good)

    def test_tree_from_list3(self):
        rows = [{'name': 'parent_name', 'parent': None},
                {'name': 'child_name', 'parent': 'parent_name'},
                {'name': 'child_name2', 'parent': 'parent_name'},
                {'name': 'child_name3', 'parent': 'parent_name'},
                {'name': 'child_child', 'parent': 'child_name3'}]
        result_good = [
                {'name': 'parent_name',
                 'parent': None,
                 'children': [
                    {'name': 'child_name',
                     'parent': 'parent_name',
                     'children': []},
                    {'name': 'child_name2',
                     'parent': 'parent_name',
                     'children': []},
                    {'name': 'child_name3',
                     'parent': 'parent_name',
                     'children': [
                         {'name': 'child_child',
                          'parent': 'child_name3',
                          'children': []}]},
                     ]}]
        result_function = tree_from_list(
            rows,
            id_field='name',
            parent_field='parent',
            children_field='children',
            root_parent=None)
        self.assertEqual(result_function, result_good)

    def test_tree_from_list_cyclic(self):
        """
        Cycle detection 1
        """
        rows = [{'name': 'child_name', 'parent': 'parent_name'},
                {'name': 'parent_name', 'parent': 'child_name'}]
        self.assertRaises(
            CycleError,
            tree_from_list,
            rows,
            id_field='name',
            parent_field='parent',
            children_field='children',
            root_parent='parent_name')

    def test_tree_from_list_cyclic2(self):
        """
        Cycle detection 2
        """
        rows = [{'name': 'parent_name', 'parent': 'parent_name'}, ]
        self.assertRaises(
            CycleError,
            tree_from_list,
            rows,
            id_field='name',
            parent_field='parent',
            children_field='children',
            root_parent='child_name')

    def test_named_list(self):
        rows = [
            ['a', 'b', 'c', 'd'],
            ['f', 'g', 'h', 'i']]
        names = ['name1', 'name2', 'name3', 'name4']
        result = named_list(rows, names)
        result_good = [
            {'name1': 'a', 'name2': 'b', 'name3': 'c', 'name4': 'd'},
            {'name1': 'f', 'name2': 'g', 'name3': 'h', 'name4': 'i'}]
        self.assertEqual(result, result_good)

    def test_unique_list(self):
        rows = [1, 2, 2, 3, 4, 5, 5, 7, 2, 5]
        result = unique_list(rows)
        result_good = [1, 2, 3, 4, 5, 7]
        self.assertEqual(result, result_good)

    def test_unique_list2(self):
        rows = [[1, 2], [2, 2], [3, 4], [2, 2], [1, 2]]
        result = unique_list(rows)
        result_good = [[1, 2], [2, 2], [3, 4]]
        self.assertEqual(result, result_good)


class CoordinatesTest(TestCase):
    fixtures = ('lizard_map', )

    def test_detect_prj1(self):
        prj = None
        self.assertEquals(
            lizard_map.coordinates.detect_prj(prj),
            lizard_map.coordinates.RD)

    def test_detect_prj2(self):
        prj = ('PROJCS["RD_New",GEOGCS["GCS_Amersfoort",'
               'DATUM["D_Amersfoort",'
               'SPHEROID["Bessel_1841",6377397.155,299.1528128]],'
               'PRIMEM["Greenwich",0.0],'
               'UNIT["Degree",0.0174532925199433]],'
               'PROJECTION["Double_Stereographic"],'
               'PARAMETER["False_Easting",155000.0],'
               'PARAMETER["False_Northing",463000.0],'
               'PARAMETER["Central_Meridian",5.38763888888889],'
               'PARAMETER["Scale_Factor",0.9999079],'
               'PARAMETER["Latitude_Of_Origin",52.15616055555555],'
               'UNIT["Meter",1.0]]')
        self.assertEquals(
            lizard_map.coordinates.detect_prj(prj),
            lizard_map.coordinates.RD)

    def test_detect_prj3(self):
        prj = ('GEOGCS["GCS_WGS_1984",'
               'DATUM["D_WGS_1984",'
               'SPHEROID["WGS_1984",6378137.0,298.257223563]],'
               'PRIMEM["Greenwich",0.0],'
               'UNIT["Degree",0.0174532925199433]]')
        self.assertEquals(
            lizard_map.coordinates.detect_prj(prj),
            lizard_map.coordinates.WGS84)

    # Jack *thinks* map_settings could be deleted

    # def test_map_settings(self):
    #     """
    #     Test MapSettings class. Nothing in settings.py, so revert to
    #     default google projection and srid.
    #     """
    #     map_settings = lizard_map.coordinates.MapSettings()

    #     self.assertTrue(map_settings.mapnik_projection(),
    #                     lizard_map.coordinates.GOOGLE)
    #     self.assertTrue(map_settings.srid, 900913)

    # def test_map_settings2(self):
    #     """
    #     Test custom settings for MapSettings.
    #     """

    #     MAP_SETTINGS = {
    #         'base_layer_type': 'WMS',  # OSM or WMS
    #         'projection': 'EPSG:28992',  # EPSG:900913, EPSG:28992
    #         'display_projection': 'EPSG:28992',  # EPSG:900913/28992/4326
    #         'startlocation_x': '144000',
    #         'startlocation_y': '486000',
    #         'startlocation_zoom': '4',
    #         'base_layer_wms': (
    #             'http://kaart.almere.nl/wmsconnector/com.esri.wms.Esrimap?'
    #             'SERVICENAME=AIKWMS&'),
    #         'base_layer_wms_layers': (
    #             'mrsid2008'),
    #         }
    #     map_settings = lizard_map.coordinates.MapSettings(MAP_SETTINGS)
    #     self.assertTrue(map_settings.mapnik_projection(),
    #                     lizard_map.coordinates.RD)
    #     self.assertTrue(map_settings.srid, 28992)

    def test_srs_to_google(self):
        x, y = lizard_map.coordinates.srs_to_google(
            'EPSG:28992', 35219, 467574)
        self.assertTrue(abs(x - 404721) < 1)
        self.assertTrue(abs(y - 6833334) < 1)

    def test_google_to_srs(self):
        x, y = lizard_map.coordinates.google_to_srs(
            579427, 6860742, 'EPSG:28992')
        self.assertTrue(abs(x - 142586) < 1)
        self.assertTrue(abs(y - 482911) < 1)


class SymbolManagerTest(TestCase):
    """
    Test the list_image_file_names funstion in symbol_manager.py.
    Expected > 5 items in the list.
    """
    def test_list_image_file_names(self):
        icon_names_list = lizard_map.symbol_manager.list_image_file_names()
        self.assertTrue(len(icon_names_list) > 5)


class DateRangeStore(unittest.TestCase):
    """Implements the tests for function compute_and_store_start_end."""

    def test_a(self):
        """Test the period attribute is stored."""

        session = {}

        date_range = {'period': PERIOD_DAY}
        compute_and_store_start_end(session, date_range)
        self.assertEqual(PERIOD_DAY, session[SESSION_DT_PERIOD])

        date_range = {'period': PERIOD_OTHER}
        compute_and_store_start_end(session, date_range)
        self.assertEqual(PERIOD_OTHER, session[SESSION_DT_PERIOD])

    def test_b(self):
        """Test only the computed values are stored."""

        session = {SESSION_DT_START: datetime.datetime(2011, 8, 1),
                   SESSION_DT_END: datetime.datetime(2011, 8, 30)}

        date_range = {'period': PERIOD_DAY}
        compute_and_store_start_end(session, date_range)

        self.assertEqual(datetime.datetime(2011, 8, 1),
                         session[SESSION_DT_START])
        self.assertEqual(datetime.datetime(2011, 8, 30),
                         session[SESSION_DT_END])

    def test_c(self):
        """Test the start and end datetime are stored for PERIOD_OTHER.

        The required information is stored in the form.

        """
        session = {}

        date_range = {'period': PERIOD_OTHER,
                      'dt_start': datetime.datetime(2011, 8, 1),
                      'dt_end': datetime.datetime(2011, 8, 30)}

        compute_and_store_start_end(session, date_range)

        self.assertEqual(datetime.datetime(2011, 8, 1),
                         session[SESSION_DT_START])
        self.assertEqual(datetime.datetime(2011, 8, 30),
                         session[SESSION_DT_END])

    def test_d(self):
        """Test the function stores the correct defaults for PERIOD_OTHER.

        The required information is not stored in the form.

        """
        session = {}

        date_range = {'period': PERIOD_OTHER}
        now = datetime.datetime(2011, 8, 30)
        compute_and_store_start_end(session, date_range, now=now)

        self.assertEqual(default_start(now), session[SESSION_DT_START])
        self.assertEqual(default_end(now), session[SESSION_DT_END])

    def test_e(self):
        """Test the start stored for PERIOD_OTHER is never after the end.

        The required information is stored in the form but the start is after
        the end.

        """
        session = {}

        date_range = {'period': PERIOD_OTHER,
                      'dt_start': datetime.datetime(2011, 8, 30),
                      'dt_end': datetime.datetime(2011, 8, 1)}

        compute_and_store_start_end(session, date_range)

        self.assertEqual(datetime.datetime(2011, 8, 30),
                         session[SESSION_DT_START])
        self.assertTrue(session[SESSION_DT_START] < session[SESSION_DT_END])


class DateRangeRetrieveSet(unittest.TestCase):
    """Implements the tests for function current_start_end_dates."""

    def setUp(self):
        self.today = datetime.datetime(2011, 8, 31)

        self.request = HttpRequest()
        self.request.session = {}

    def test_a(self):
        """Test the function the correct values for PERIOD_DAY.

        No session information is stored.

        """
        retrieve_period = lambda request: PERIOD_DAY
        start, end = current_start_end_dates(self.request, today=self.today,\
             retrieve_period_function=retrieve_period)

        self.assertEqual(start, datetime.timedelta(-1) + self.today)
        self.assertEqual(end, datetime.timedelta(0) + self.today)

    def test_b(self):
        """Test the function returns the correct values for PERIOD_DAY.

        The sessions specifies the required information.

        """
        self.request.session = {SESSION_DT_PERIOD: PERIOD_DAY}

        start, end = current_start_end_dates(self.request, today=self.today)

        self.assertEqual(start, datetime.timedelta(-1) + self.today)
        self.assertEqual(end, datetime.timedelta(0) + self.today)

    def test_c(self):
        """Test the function returns the defaults for period PERIOD_OTHER.

        No session information is stored.

        """
        retrieve_period = lambda request: PERIOD_OTHER
        start, end = current_start_end_dates(self.request, today=self.today,\
             retrieve_period_function=retrieve_period)

        self.assertEqual(start, default_start(self.today))
        self.assertEqual(end, default_end(self.today))
