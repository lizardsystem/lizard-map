import datetime

from django.test import TestCase
import pkg_resources

from lizard_map.animation import AnimationSettings
from lizard_map.daterange import current_start_end_dates
from lizard_map.models import Workspace
from lizard_map.models import WorkspaceItem
from lizard_map.utility import short_string
from lizard_map.workspace import WorkspaceManager
import lizard_map.admin
import lizard_map.layers
import lizard_map.models
import lizard_map.urls
import lizard_map.views


class LayersTest(TestCase):
    """WMS layer functions are generally defined in layers.py. One can add his
    own in other apps. shapefile_layer is an example function.
    """

    def test_initialization(self):
        mock_workspace = None
        ws_adapter = lizard_map.layers.WorkspaceItemAdapterShapefile(
            mock_workspace, layer_arguments={})
        layers, styles = ws_adapter.layer()
        # TODO: test output.


class WorkspaceManagerTest(TestCase):

    def test_smoke(self):
        """We use the WorkspaceManager to find and create our workspaces"""
        mock_request = {}
        workspace_manager = WorkspaceManager(
            mock_request)
        self.assertTrue(workspace_manager)  # It exists.


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
        """A workspace always has a name.  It is 'workspace' by default."""
        workspace = Workspace()
        self.assertEquals(workspace.name, u'Workspace')

    def test_representation(self):
        workspace = Workspace()
        workspace.save()
        # No errors: fine.  As long as we return something.
        self.assertTrue(unicode(workspace))

    def test_absolute_url(self):
        workspace = Workspace()
        workspace.save()
        self.assertTrue(workspace.get_absolute_url().endswith('/workspace/1/'))


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
        workspace_item.adapter_class = 'adapter_shapefile'
        self.assertTrue(isinstance(
                workspace_item.adapter,
                lizard_map.layers.WorkspaceItemAdapterShapefile))

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
