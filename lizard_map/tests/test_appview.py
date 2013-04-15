from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils import simplejson as json
from lizard_map.models import WorkspaceEdit
import lizard_map.admin
import lizard_map.coordinates
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

    def test_workspace_edit_wms(self):
        url = reverse('lizard_map_workspace_edit_wms',
                      kwargs={'workspace_item_id': self.workspace.id})
        # ^^^ Check; that's workspace ID instead of workspaceitem ID.
        url += ('?LAYERS=basic&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&'
                'STYLES=&EXCEPTIONS=application%2Fvnd.ogc.se_inimage&'
                'FORMAT=image%2Fjpeg&SRS=EPSG%3A900913&'
                'BBOX=430987.5469813,6803449.8497827,'
                '669012.4530187,6896550.1502173&'
                'WIDTH=1557&HEIGHT=609')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

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

    def test_buttons_on(self):
        view = lizard_map.views.AppView()
        self.assertTrue(view.map_show_multiselect)
        self.assertTrue(view.map_show_daterange)
        self.assertTrue(view.map_show_default_zoom)
        self.assertEquals(view.content_actions, 3)

    def test_buttons_off_view(self):
        view = lizard_map.views.AppView()
        view.map_show_multiselect = False
        view.map_show_daterange = False
        view.map_show_default_zoom = False
        self.assertEquals(view.content_actions, 0)

    @override_settings(MAP_SHOW_MULTISELECT=False,
                       MAP_SHOW_DATERANGE=False,
                       MAP_SHOW_DEFAULT_ZOOM=False)
    def test_buttons_off_settings(self):
        view = lizard_map.views.AppView()
        self.assertEquals(view.content_actions, 0)
