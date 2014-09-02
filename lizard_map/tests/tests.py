import datetime
import unittest

from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.test.client import MULTIPART_CONTENT
from django.test.client import BOUNDARY
from django.test.client import encode_multipart
import mock
import pytz
import rest_framework

from lizard_map.adapter import Graph
from lizard_map.adapter import parse_identifier_json
from lizard_map import dateperiods
from lizard_map.fields import Color
from lizard_map.mapnik_helper import database_settings
from lizard_map.models import Legend
from lizard_map.models import WorkspaceEdit
from lizard_map.models import WorkspaceEditItem
from lizard_map.operations import AnchestorRegistration
from lizard_map.operations import CycleError
from lizard_map.operations import named_list
from lizard_map.operations import tree_from_list
from lizard_map.operations import unique_list
from lizard_map.utility import float_to_string
from lizard_map.utility import short_string
from lizard_map.workspace import WorkspaceItemAdapter
from lizard_map.templatetags import workspaces
import lizard_map.admin
import lizard_map.coordinates
import lizard_map.layers
import lizard_map.models
import lizard_map.urls
import lizard_map.views


# class TestDateRange(TestCase):
#     """Test daterange.py"""

#     def setUp(self):
#         self.request = mock.Mock()
#         self.request.session = mock.Mock()
#         self.today = datetime.datetime(2011, 4, 21)
#         self.almost_one_day = datetime.timedelta(
#             hours=23, minutes=59, seconds=59)

#     def _test_set_date_range(self, request):

#         #set_date_range(self.request, now=self.today)
#         data = {'period': request.POST.get('period', None),
#                 'dt_start': request.POST.get('dt_start', None),
#                 'dt_end': request.POST.get('dt_end', None)}
#         form = lizard_map.forms.DateRangeForm(data)  # Fill in daterange
#         form.is_valid()  # it must succeed

#         view = lizard_map.views.DateRangeView()
#         view.request = request  # Manually put request in view
#         view.form_valid_action(form)  # Actually setting date range.

#         # Get current period, dt_start, dt_end
#         period = current_period(self.request)
#         dt_start, dt_end = current_start_end_dates(
#             self.request, today=self.today)

#         return period, dt_start, dt_end

#     def test_current_start_end_dates(self):
#         dt_start, dt_end = current_start_end_dates(
#             self.request, today=self.today)
#         dt_start_expected = self.today + PERIOD_DAYS[PERIOD_DAY][0]
#         dt_end_expected = self.today + PERIOD_DAYS[PERIOD_DAY][1]

#         self.assertEquals(dt_start, dt_start_expected)
#         self.assertEquals(dt_end, dt_end_expected)

#     def test_current_period(self):
#         """Test default period."""
#         period = current_period(self.request)
#         self.assertEquals(period, PERIOD_DAY)

#     def test_set_date_range(self):
#         """Set date range to period_day, then retrieve it back"""
#         # Fake Post
#         self.request.method = 'POST'
#         self.request.POST = {
#             'period': str(PERIOD_DAY)}
#         self.request.META = {}

#         period, dt_start, dt_end = self._test_set_date_range(self.request)

#         self.assertEquals(period, PERIOD_DAY)
#         self.assertEquals(dt_start, self.today + PERIOD_DAYS[PERIOD_DAY][0])
#         self.assertEquals(dt_end, self.today + PERIOD_DAYS[PERIOD_DAY][1])

#     def test_set_date_range2(self):
#         """Set custom date range, then retrieve it back"""
#         # Fake Post
#         self.request.method = 'POST'
#         dt_start_expected = datetime.datetime(2011, 5, 25)
#         dt_end_expected = datetime.datetime(2011, 5, 25, 23, 59, 59)
#         self.request.POST = {
#             'period': str(PERIOD_OTHER),
#             'dt_start': dt_start_expected,
#             'dt_end': dt_end_expected}
#         self.request.META = {}

#     #     period, dt_start, dt_end = self._test_set_date_range(self.request)
#     #     self.assertEquals(period, PERIOD_OTHER)
#     #     self.assertEquals(dt_start, dt_start_expected)
#     #     self.assertEquals(dt_end, dt_end_expected)
#     def test_set_date_range3(self):
#         """Set start date after end date: result must have dt_start<dt_end"""
#         timedelta_start = datetime.timedelta(days=20)
#         timedelta_end = datetime.timedelta(days=-15)

#         # Fake Post
#         self.request.method = 'POST'
#         self.request.POST = {
#             'period': str(PERIOD_OTHER),
#             'dt_start': self.today + timedelta_start,
#             'dt_end': self.today + timedelta_end}
#         self.request.META = {}

#         period, dt_start, dt_end = self._test_set_date_range(self.request)

#         self.assertEquals(period, PERIOD_OTHER)
#         self.assertTrue(dt_start < dt_end)


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
    # TODO: add tests that show what happens with non-timezone-aware
    # datetimes!

    def setUp(self):
        self.start_date = datetime.datetime(1979, 5, 25,
                                            tzinfo=pytz.UTC)  # It's a friday.
        self.end_date = datetime.datetime(1979, 7, 15,
                                          tzinfo=pytz.UTC)  # It's a sunday.

    def test_calc_aggregation_periods_all(self):
        periods = dateperiods.calc_aggregation_periods(
            self.start_date, self.end_date, dateperiods.ALL)
        self.assertEqual(periods[0][0], self.start_date)
        self.assertEqual(periods[0][1], self.end_date)

    def test_calc_aggregation_periods_year(self):
        end_date = datetime.datetime(1980, 4, 15, tzinfo=pytz.UTC)
        periods = dateperiods.calc_aggregation_periods(
            self.start_date, end_date, dateperiods.YEAR)
        self.assertEqual(periods[0][0], self.start_date)
        self.assertEqual(periods[0][1],
                         datetime.datetime(1980, 1, 1, tzinfo=pytz.UTC))
        self.assertEqual(periods[1][0],
                         datetime.datetime(1980, 1, 1, tzinfo=pytz.UTC))
        self.assertEqual(periods[1][1], end_date)

    def test_calc_aggregation_periods_quarter(self):
        end_date = datetime.datetime(1980, 4, 15, tzinfo=pytz.UTC)
        periods = dateperiods.calc_aggregation_periods(
            self.start_date, end_date, dateperiods.QUARTER)
        self.assertEqual(periods[0][0], self.start_date)
        self.assertEqual(periods[0][1],
                         datetime.datetime(1979, 7, 1, tzinfo=pytz.UTC))
        self.assertEqual(periods[-1][0],
                         datetime.datetime(1980, 4, 1, tzinfo=pytz.UTC))
        self.assertEqual(periods[-1][1], end_date)

    def test_calc_aggregation_periods_month(self):
        end_date = datetime.datetime(1980, 4, 15, tzinfo=pytz.UTC)
        first_day_of_new_month_after_startdate = datetime.datetime(
            1979, 6, 1, tzinfo=pytz.UTC)
        first_day_of_end_month = datetime.datetime(
            1980, 4, 1, tzinfo=pytz.UTC)
        periods = dateperiods.calc_aggregation_periods(
            self.start_date, end_date, dateperiods.MONTH)
        self.assertEqual(periods[0][0], self.start_date)
        self.assertEqual(periods[0][1],
                         first_day_of_new_month_after_startdate)
        self.assertEqual(periods[-1][0],
                         first_day_of_end_month)
        self.assertEqual(periods[-1][1], end_date)

    def test_calc_aggregation_periods_week(self):
        monday_after_startdate = datetime.datetime(1979, 5, 28,
                                                   tzinfo=pytz.UTC)
        monday_before_enddate = datetime.datetime(1979, 7, 9,
                                                  tzinfo=pytz.UTC)
        periods = dateperiods.calc_aggregation_periods(
            self.start_date, self.end_date, dateperiods.WEEK)
        self.assertEqual(periods[0][0], self.start_date)
        self.assertEqual(periods[0][1],
                         monday_after_startdate)
        self.assertEqual(periods[-1][0],
                         monday_before_enddate)
        self.assertEqual(periods[-1][1], self.end_date)

    def test_calc_aggregation_periods_day(self):
        periods = dateperiods.calc_aggregation_periods(
            self.start_date, self.end_date, dateperiods.DAY)
        self.assertEqual(periods[0][0], self.start_date)
        self.assertEqual(periods[0][1],
                         datetime.datetime(1979, 5, 26, tzinfo=pytz.UTC))
        self.assertEqual(periods[-1][0],
                         datetime.datetime(1979, 7, 14, tzinfo=pytz.UTC))
        self.assertEqual(periods[-1][1], self.end_date)

    def test_fancy_period(self):
        start_date = datetime.datetime(1979, 5, 25, tzinfo=pytz.UTC)
        end_date = datetime.datetime(1979, 7, 15, tzinfo=pytz.UTC)
        self.assertTrue(dateperiods.fancy_period(
                start_date, end_date, dateperiods.ALL))
        self.assertTrue(dateperiods.fancy_period(
                start_date, end_date, dateperiods.YEAR))
        self.assertTrue(dateperiods.fancy_period(
                start_date, end_date, dateperiods.QUARTER))
        self.assertTrue(dateperiods.fancy_period(
                start_date, end_date, dateperiods.MONTH))
        self.assertTrue(dateperiods.fancy_period(
                start_date, end_date, dateperiods.WEEK))
        self.assertTrue(dateperiods.fancy_period(
                start_date, end_date, dateperiods.DAY))


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


# class DateRangeStore(unittest.TestCase):
#     """Implements the tests for function compute_and_store_start_end."""

#     def test_a(self):
#         """Test the period attribute is stored."""

#         session = {}

#         date_range = {'period': PERIOD_DAY}
#         dateperiods.compute_and_store_start_end(session, date_range)
#         self.assertEqual(PERIOD_DAY, session[SESSION_DT_PERIOD])

#         date_range = {'period': PERIOD_OTHER}
#         dateperiods.compute_and_store_start_end(session, date_range)
#         self.assertEqual(PERIOD_OTHER, session[SESSION_DT_PERIOD])

#     def test_b(self):
#         """Test only the computed values are stored."""

#         session = {SESSION_DT_START: datetime.datetime(2011, 8, 1),
#                    SESSION_DT_END: datetime.datetime(2011, 8, 30)}

#         date_range = {'period': PERIOD_DAY}
#         dateperiods.compute_and_store_start_end(session, date_range)

#         self.assertEqual(datetime.datetime(2011, 8, 1),
#                          session[SESSION_DT_START])
#         self.assertEqual(datetime.datetime(2011, 8, 30),
#                          session[SESSION_DT_END])

#     def test_c(self):
#         """Test the start and end datetime are stored for PERIOD_OTHER.

#         The required information is stored in the form.

#         """
#         session = {}

#         date_range = {'period': PERIOD_OTHER,
#                       'dt_start': datetime.datetime(2011, 8, 1),
#                       'dt_end': datetime.datetime(2011, 8, 30)}

#         dateperiods.compute_and_store_start_end(session, date_range)

#         self.assertEqual(datetime.datetime(2011, 8, 1),
#                          session[SESSION_DT_START])
#         self.assertEqual(datetime.datetime(2011, 8, 30),
#                          session[SESSION_DT_END])

#     def test_d(self):
#         """Test the function stores the correct defaults for PERIOD_OTHER.

#         The required information is not stored in the form.

#         """
#         session = {}

#         date_range = {'period': PERIOD_OTHER}
#         now = datetime.datetime(2011, 8, 30)
#         dateperiods.compute_and_store_start_end(session, date_range, now=now)

#         self.assertEqual(default_start(now), session[SESSION_DT_START])
#         self.assertEqual(default_end(now), session[SESSION_DT_END])

#     def test_e(self):
#         """Test the start stored for PERIOD_OTHER is never after the end.

#         The required information is stored in the form but the start is after
#         the end.

#         """
#         session = {}

#         date_range = {'period': PERIOD_OTHER,
#                       'dt_start': datetime.datetime(2011, 8, 30),
#                       'dt_end': datetime.datetime(2011, 8, 1)}

#         dateperiods.compute_and_store_start_end(session, date_range)

#         self.assertEqual(datetime.datetime(2011, 8, 30),
#                          session[SESSION_DT_START])
#         self.assertTrue(session[SESSION_DT_START] < session[SESSION_DT_END])


# class DateRangeRetrieveSet(unittest.TestCase):
#     """Implements the tests for function current_start_end_dates."""

#     def setUp(self):
#         self.today = datetime.datetime(2011, 8, 31)

#         self.request = HttpRequest()
#         self.request.session = {}

#     def test_a(self):
#         """Test the function the correct values for PERIOD_DAY.

#         No session information is stored.

#         """
#         retrieve_period = lambda request: PERIOD_DAY
#         start, end = current_start_end_dates(self.request, today=self.today,\
#              retrieve_period_function=retrieve_period)

#         self.assertEqual(start, datetime.timedelta(-1) + self.today)
#         self.assertEqual(end, datetime.timedelta(0) + self.today)

#     def test_b(self):
#         """Test the function returns the correct values for PERIOD_DAY.

#         The sessions specifies the required information.

#         """
#         self.request.session = {SESSION_DT_PERIOD: PERIOD_DAY}

#         start, end = current_start_end_dates(self.request, today=self.today)

#         self.assertEqual(start, datetime.timedelta(-1) + self.today)
#         self.assertEqual(end, datetime.timedelta(0) + self.today)

#     def test_c(self):
#         """Test the function returns the defaults for period PERIOD_OTHER.

#         No session information is stored.

#         """
#         retrieve_period = lambda request: PERIOD_OTHER
#         start, end = current_start_end_dates(self.request, today=self.today,\
#              retrieve_period_function=retrieve_period)

#         self.assertEqual(start, default_start(self.today))
#         self.assertEqual(end, default_end(self.today))


class ViewStateServiceTest(unittest.TestCase):

    def setUp(self):
        self.request = HttpRequest()
        self.request.session = {}

    def test_smoke(self):
        """Just call the adapter and make sure it doesn't barf."""
        view = lizard_map.views.ViewStateService()
        request = HttpRequest()
        request.session = mock.Mock()
        self.assertEqual(type(view.get(request)),
                         rest_framework.response.Response)

    def test_rest_setup(self):
        """Test whether djangorestframework is properly set up.

        We do this by testing if the dict from the above test is returned as a
        proper json dict. This test is really only needed for *one* of the
        djangorestframework-using views. (We use this one because it is the
        easiest to test).
        """
        client = Client()
        url = reverse('lizard_map_view_state_service')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response._headers['content-type'][1],
                         'application/json')

    # TODO: commented out test, validation isn't happening anymore.
    # See https://github.com/lizardsystem/lizard-map/issues/16
    # def test_put_validation(self):
    #     """The input should be validated."""
    #     client = Client()
    #     url = reverse('lizard_map_view_state_service')
    #     data = {'range_type': 'invalid',
    #             'dt_start': 1,
    #             'dt_end': 2}
    #     self.assertRaises(ValidationError, client.put, url, data=data)

    def test_put_setup(self):
        """Test whether djangorestframework is properly set up.

        This tests the .put() functionality, whether request.DATA can properly
        be used.
        """
        client = Client()
        url = reverse('lizard_map_view_state_service')
        date1 = datetime.datetime(1979, 5, 25, tzinfo=pytz.UTC)
        date2 = datetime.datetime(1979, 7, 15, tzinfo=pytz.UTC)
        data = {'range_type': '2_day',
                'dt_start': unicode(date1),
                'dt_end': unicode(date2)}
        response = client.put(
            url, data=encode_multipart(BOUNDARY, data),
            content_type=MULTIPART_CONTENT)
        self.assertEqual(response.status_code, 200)
