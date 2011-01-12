import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.utils import simplejson as json
import pkg_resources

from lizard_map.adapter import Graph
from lizard_map.adapter import parse_identifier_json
from lizard_map.adapter import workspace_item_image_url
from lizard_map.animation import AnimationSettings
from lizard_map.daterange import current_start_end_dates
from lizard_map.dateperiods import ALL
from lizard_map.dateperiods import YEAR
from lizard_map.dateperiods import QUARTER
from lizard_map.dateperiods import MONTH
from lizard_map.dateperiods import WEEK
from lizard_map.dateperiods import DAY
from lizard_map.dateperiods import calc_aggregation_periods
from lizard_map.dateperiods import fancy_period
from lizard_map.mapnik_helper import database_settings
from lizard_map.models import Color
from lizard_map.models import Legend
from lizard_map.models import Workspace
from lizard_map.models import WorkspaceCollage
from lizard_map.models import WorkspaceCollageSnippetGroup
from lizard_map.models import WorkspaceItem
from lizard_map.operations import AnchestorRegistration
from lizard_map.operations import CycleError
from lizard_map.operations import named_list
from lizard_map.operations import tree_from_list
from lizard_map.operations import unique_list
from lizard_map.utility import float_to_string
from lizard_map.utility import short_string
from lizard_map.workspace import WorkspaceItemAdapter
from lizard_map.workspace import WorkspaceManager
from lizard_map.templatetags import map as map_functions
from lizard_map.templatetags import workspaces
import lizard_map.admin
import lizard_map.coordinates
import lizard_map.layers
import lizard_map.models
import lizard_map.urls
import lizard_map.views


class WorkspaceManagerTest(TestCase):

    class MockRequest(object):
        session = {}

    def setUp(self):
        mock_request = self.MockRequest()
        self.workspace_manager = WorkspaceManager(
            mock_request)

    def test_smoke(self):
        """We use the WorkspaceManager to find and create our workspaces"""
        self.assertTrue(self.workspace_manager)  # It exists.

    def test_load_or_create(self):
        workspace_groups = self.workspace_manager.load_or_create()
        self.assertTrue(workspace_groups)

    def test_load(self):
        workspace_groups = self.workspace_manager.load_or_create()
        self.assertTrue(workspace_groups)
        self.workspace_manager.save_workspaces()
        errors = self.workspace_manager.load_workspaces()
        self.assertEqual(errors, 0)

    def test_save(self):
        workspace_groups = self.workspace_manager.load_or_create()
        self.assertTrue(workspace_groups)
        self.workspace_manager.save_workspaces()

    def test_empty(self):
        workspace_groups = self.workspace_manager.load_or_create()
        self.assertTrue(workspace_groups)
        self.workspace_manager.empty()


class ViewsTest(TestCase):

    class MockRequest(object):
        session = {}

    def setUp(self):
        self.client = Client()
        self.workspace = Workspace()
        self.workspace.save()
        self.collage = WorkspaceCollage(workspace=self.workspace)
        self.collage.save()

    def test_homepage(self):
        url = reverse('lizard_map_workspace',
                      kwargs={'workspace_id': self.workspace.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_wms(self):
        url = reverse('lizard_map_wms',
                      kwargs={'workspace_id': self.workspace.id})
        url += ('?LAYERS=basic&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&'
                'STYLES=&EXCEPTIONS=application%2Fvnd.ogc.se_inimage&'
                'FORMAT=image%2Fjpeg&SRS=EPSG%3A900913&'
                'BBOX=430987.5469813,6803449.8497827,'
                '669012.4530187,6896550.1502173&'
                'WIDTH=1557&HEIGHT=609')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_collage(self):
        url = reverse('lizard_map.collage',
                      kwargs={'collage_id': self.collage.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_collage_popup(self):
        url = reverse('lizard_map.collage_popup',
                      kwargs={'collage_id': self.collage.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_search_coordinates(self):
        url = reverse('lizard_map.search_coordinates')
        url += '?x=430987.5469813&y=6817896.448126&radius=100'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_search_name(self):
        url = reverse('lizard_map.search_name')
        url += '?x=430987.5469813&y=6817896.448126&radius=100'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_map_location_save(self):
        """Save map location, see if it doesn't crash
        """
        client = Client()
        url = reverse('lizard_map.map_location_save')
        response = client.post(url, {'x': 100, 'y': 150, 'zoom': 10})
        self.assertEqual(response.status_code, 200)

    def test_map_location_load_default(self):
        """Save map location, then load it back.
        """
        url_load = reverse('lizard_map.map_location_load_default')
        response_load = self.client.get(url_load)
        self.assertEqual(response_load.status_code, 200)
        result = json.loads(response_load.content)
        self.assertEqual(
            result,
            {'x': '550000',
             'y': '6850000',
             'zoom': '10'})


class WorkspaceTest(TestCase):

    def test_workspace_contains_items(self):
        """A workspace can contain workspace items"""
        workspace1 = Workspace()
        workspace1.save()
        self.assertTrue(workspace1)
        self.assertFalse(workspace1.workspace_items.all())  # Empty.
        workspace_item1 = workspace1.workspace_items.create()
        workspace_item2 = workspace1.workspace_items.create()
        self.assertEquals(len(workspace1.workspace_items.all()), 2)
        self.assertTrue(workspace_item1 in workspace1.workspace_items.all())
        self.assertTrue(workspace_item2 in workspace1.workspace_items.all())

    def test_name(self):
        """A workspace always has a name.  It is 'My Workspace' by
        default."""
        workspace = Workspace()
        self.assertEquals(workspace.name, u'My Workspace')

    def test_representation(self):
        workspace = Workspace()
        workspace.save()
        # No errors: fine.  As long as we return something.
        self.assertTrue(unicode(workspace))

    def test_absolute_url(self):
        workspace = Workspace()
        workspace.save()
        # The initial version of this test asserted that the absolute URL ended
        # with '/workspace/1', apparantly assuming that the new workspace would
        # have id 1. However, that does not have to be the case.
        expected_end = '/workspace/%d/' % workspace.id
        self.assertTrue(workspace.get_absolute_url().endswith(expected_end))


class WorkspaceClientTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_workspace_item_add(self):
        workspace = Workspace()
        workspace.save()
        url = reverse('lizard_map_workspace_item_add',
                      kwargs={'workspace_id': str(workspace.id)})
        params = {'name': 'test workspace_item',
                  'adapter_class': 'test adapter_class',
                  'adapter_layer_json': '{"json"}'}
        self.client.post(url, params)
        self.assertTrue(workspace.workspace_items.filter())

    def test_workspace_item_reorder(self):
        workspace = Workspace()
        workspace.save()
        workspace_item1 = workspace.workspace_items.create()
        workspace_item2 = workspace.workspace_items.create()
        url = reverse('lizard_map_workspace_item_reorder',
                      kwargs={'workspace_id': str(workspace.id)})
        order = {'workspace-items[]': [
                str(workspace_item2.id),
                str(workspace_item1.id)]}
        self.client.post(url, order)

        self.assertEqual(workspace.workspace_items.all()[0], workspace_item2)
        self.assertEqual(workspace.workspace_items.all()[1], workspace_item1)

    def test_workspace_item_edit(self):
        workspace = Workspace()
        workspace.save()
        workspace_item1 = workspace.workspace_items.create(
            name='test workspaceitem')

        url = reverse('lizard_map_workspace_item_edit')
        self.client.post(
            url,
            {'workspace_item_id': str(workspace_item1.id), 'visible': 'false'})
        self.assertEqual(
            WorkspaceItem.objects.get(name='test workspaceitem').visible,
            False)
        self.client.post(
            url,
            {'workspace_item_id': str(workspace_item1.id), 'visible': 'true'})
        self.assertEqual(
            WorkspaceItem.objects.get(name='test workspaceitem').visible,
            True)

    def test_workspace_item_delete(self):
        workspace = Workspace()
        workspace.save()
        workspace_item1 = workspace.workspace_items.create(
            name='test workspaceitem')

        url = reverse('lizard_map_workspace_item_delete')
        self.client.post(
            url,
            {'object_id': str(workspace_item1.id)})
        self.assertFalse(workspace.workspace_items.all())

    def test_workspace_extent_temp(self):
        """
        Tests if the workspace extent does not crash (although the
        content will be meaningless).
        """
        url = reverse('lizard_map_session_workspace_extent_temp')
        result = self.client.get(url, {})
        self.assertEqual(result.status_code, 200)

    # Not testable without adapter
    # def test_workspace_extent(self):
    #     """
    #     Tests if the workspace extent does not crash (although the
    #     content will be meaningless).
    #     """
    #     workspace = Workspace()
    #     workspace.save()
    #     workspace_item1 = workspace.workspace_items.create(
    #         name='test workspaceitem')
    #     url = reverse('lizard_map_workspace_item_extent')
    #     result = self.client.get(url, {
    #             'workspace_item_id': workspace_item1.id})
    #     self.assertEqual(result.status_code, 200)
    #     self.assertTrue('north' in result.content)


    # Not testable without adapter
    # def test_workspace_item_image(self):
    #     workspace = Workspace()
    #     workspace.save()
    #     workspace_item1 = workspace.workspace_items.create(
    #         name='test workspaceitem')

    #     url = reverse('lizard_map_workspace_item_image')
    #     url += '?identifier={test_identifier}'
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)

    # TODO: snippet stuff


class WorkspaceItemTest(TestCase):

    def test_has_adapter(self):
        """A workspace item can point to a method that returns a layer."""
        workspace_item = WorkspaceItem()
        self.assertFalse(workspace_item.has_adapter())
        workspace_item.adapter_class = 'todo'
        self.assertTrue(workspace_item.has_adapter())

    def test_entry_points_exist(self):
        """There's at least one adapter entry point registered."""
        self.assertTrue(list(pkg_resources.iter_entry_points(
                    group='lizard_map.adapter_class')))

    def test_entry_point_lookup(self):
        """The string that identifies a method is looked up as a so-called
        entry point."""
        workspace_item = WorkspaceItem()
        workspace_item.adapter_class = 'todo'
        self.assertRaises(lizard_map.models.AdapterClassNotFoundError,
                          lambda: workspace_item.adapter,
                          # ^^^ lambda as adapter is a property and
                          # assertRaises expects a callable.
                          )
        workspace_item.adapter_class = 'adapter_dummy'
        workspace_item.adapter_layer_json = ("{}")
        self.assertTrue(isinstance(
                workspace_item.adapter,
                lizard_map.layers.AdapterDummy))

    def test_adapter_arguments(self):
        """The layer method probably needs arguments. You can store them as a
        json string."""
        workspace_item = WorkspaceItem()
        self.assertTrue(isinstance(workspace_item.adapter_layer_arguments,
                                   dict))
        self.assertFalse(len(workspace_item.adapter_layer_arguments))
        workspace_item.adapter_layer_json = '{"bla": "yes"}'
        self.assertEquals(workspace_item.adapter_layer_arguments['bla'],
                          'yes')

    def test_name(self):
        """A workspace item always has a name.  It is blank by default,
        though."""
        workspace_item = WorkspaceItem()
        self.assertEquals(workspace_item.name, '')
        workspace_item2 = WorkspaceItem(name='bla')
        self.assertEquals(workspace_item2.name, 'bla')

    def test_representation(self):
        workspace = Workspace()
        workspace.save()
        workspace_item = workspace.workspace_items.create()
        # No errors: fine.  As long as we return something.
        self.assertTrue(unicode(workspace_item))


class TestCollages(TestCase):

    def test_creation(self):
        workspace = Workspace()
        workspace.save()  # save() because we need our generated id.
        self.assertFalse(workspace.collages.all())
        workspace.collages.create(name='user collage')
        self.assertTrue(workspace.collages.all())


class TestAnimationSettings(TestCase):
    """Tests for animation.py."""

    def setUp(self):

        class Mock(dict):
            pass

        self.request = Mock()
        self.request.session = Mock()

    def _fill_date_range(self):
        """Helper method: fill session with date range info."""
        twothousand = datetime.datetime(year=2000, month=1, day=1)
        twothousandthree = datetime.datetime(year=2003, month=1, day=1)
        self.request.session['date_start'] = twothousand
        self.request.session['date_end'] = twothousandthree

    def test_date_range_helper(self):
        """Make sure _fill_date_range() works."""
        self._fill_date_range()
        start, end = current_start_end_dates(self.request)
        self.assertEquals(start.year, 2000)
        self.assertEquals(end.year, 2003)

    def test_smoke(self):
        animation_settings = AnimationSettings(request=self.request)
        self.assertTrue(animation_settings)  # It exists.

    def test_session_initialisation(self):
        self.assertFalse('animation_settings' in self.request.session)
        AnimationSettings(self.request)
        self.assertTrue('animation_settings' in self.request.session)

    def test_slider_position(self):
        """Are the getters/setters working?"""
        animation_settings = AnimationSettings(self.request)
        animation_settings.slider_position = 42
        self.assertTrue(self.request.session.modified)
        self.assertEquals(animation_settings.slider_position, 42)
        self.assertEquals(self.request.session[
                'animation_settings']['slider_position'], 42)

    def test_initial_slider_position(self):
        """Slider position should be 0 if not initialised.
        In any case, it should not return a keyerror."""
        animation_settings = AnimationSettings(self.request)
        self.assertEquals(animation_settings.slider_position, 0)

    def test_initial_info_gathering(self):
        """Do we return the correct date range and position?"""
        self._fill_date_range()
        animation_settings = AnimationSettings(self.request)
        result = animation_settings.info()
        self.assertEquals(result['min'], 0)
        self.assertEquals(result['max'], 1096)
        self.assertEquals(result['step'], 1)
        self.assertEquals(result['value'], 0)
        self.assertEquals(result['selected_date'].year, 2000)

    def test_info_gathering(self):
        """Do we return the correct date range and position?"""
        self._fill_date_range()
        animation_settings = AnimationSettings(self.request)
        animation_settings.slider_position = 400
        result = animation_settings.info()
        self.assertEquals(result['min'], 0)
        self.assertEquals(result['max'], 1096)
        self.assertEquals(result['step'], 1)
        self.assertEquals(result['value'], 400)
        self.assertEquals(result['selected_date'].year, 2001)

    def test_impossible_negative_corner_case(self):
        """Negative dates."""
        self._fill_date_range()
        animation_settings = AnimationSettings(self.request)
        animation_settings.slider_position = -400
        result = animation_settings.info()
        self.assertEquals(result['value'], 0)

    def test_impossible_beyond_max_corner_case(self):
        """Value beyond the max possible."""
        self._fill_date_range()
        animation_settings = AnimationSettings(self.request)
        animation_settings.slider_position = 4000
        result = animation_settings.info()
        self.assertEquals(result['value'], 1096)  # Max available.


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

    def test_workspace_item_image_url(self):
        workspace_item_id = 1  # Does not have to exist.
        identifiers = [{}, {}]
        self.assertTrue(workspace_item_image_url(
                workspace_item_id, identifiers))

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
        self.workspace = Workspace()
        self.workspace.save()
        workspace_item = WorkspaceItem(workspace=self.workspace)
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

    def test_html_default_snippet_group(self):
        workspace_collage = WorkspaceCollage(workspace=self.workspace)
        workspace_collage.save()
        snippet_group = WorkspaceCollageSnippetGroup(
            workspace_collage=workspace_collage)
        snippet_group.save()
        self.assertTrue(self.adapter.html_default(snippet_group=snippet_group))

    def test_legend_object_default(self):
        self.adapter.legend_object_default('no_name')

    def test_legend_default(self):
        legend_object = self.adapter.legend_object_default('no_name')
        self.adapter.legend_default(legend_object)


class DatePeriodsTest(TestCase):

    def test_calc_aggregation_periods_all(self):
        start_date = datetime.date(1979, 5, 25)
        end_date = datetime.date(1980, 4, 15)
        periods = calc_aggregation_periods(start_date, end_date, ALL)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], end_date)

    def test_calc_aggregation_periods_year(self):
        start_date = datetime.date(1979, 5, 25)
        end_date = datetime.date(1980, 4, 15)
        periods = calc_aggregation_periods(start_date, end_date, YEAR)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], datetime.date(1980, 1, 1))
        self.assertEqual(periods[1][0], datetime.date(1980, 1, 1))
        self.assertEqual(periods[1][1], end_date)

    def test_calc_aggregation_periods_quarter(self):
        start_date = datetime.date(1979, 5, 25)
        end_date = datetime.date(1980, 4, 15)
        periods = calc_aggregation_periods(start_date, end_date, QUARTER)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], datetime.date(1979, 7, 1))
        self.assertEqual(periods[-1][0], datetime.date(1980, 4, 1))
        self.assertEqual(periods[-1][1], end_date)

    def test_calc_aggregation_periods_month(self):
        start_date = datetime.date(1979, 5, 25)
        end_date = datetime.date(1980, 4, 15)
        periods = calc_aggregation_periods(start_date, end_date, MONTH)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], datetime.date(1979, 6, 1))
        self.assertEqual(periods[-1][0], datetime.date(1980, 4, 1))
        self.assertEqual(periods[-1][1], end_date)

    def test_calc_aggregation_periods_week(self):
        start_date = datetime.date(1979, 5, 25)  # It's a friday.
        end_date = datetime.date(1979, 7, 15)  # It's a sunday.
        periods = calc_aggregation_periods(start_date, end_date, WEEK)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], datetime.date(1979, 5, 28))
        self.assertEqual(periods[-1][0], datetime.date(1979, 7, 9))
        self.assertEqual(periods[-1][1], end_date)

    def test_calc_aggregation_periods_day(self):
        start_date = datetime.date(1979, 5, 25)
        end_date = datetime.date(1979, 7, 15)
        periods = calc_aggregation_periods(start_date, end_date, DAY)
        self.assertEqual(periods[0][0], start_date)
        self.assertEqual(periods[0][1], datetime.date(1979, 5, 26))
        self.assertEqual(periods[-1][0], datetime.date(1979, 7, 14))
        self.assertEqual(periods[-1][1], end_date)

    def test_fancy_period(self):
        start_date = datetime.date(1979, 5, 25)
        end_date = datetime.date(1979, 7, 15)
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

    def test_map_variables(self):
        """Just see if map_variables crashes"""
        parser = None
        token = None
        map_functions.map_variables(parser, token)

    def test_detect_browser(self):
        """Just see if detect_browser crashes"""
        parser = None
        token = None
        map_functions.detect_browser(parser, token)


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
