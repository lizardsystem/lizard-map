from django.contrib.auth.models import User
from django.test import TestCase

from lizard_map.templatetags import workspaces
from lizard_map.models import WorkspaceEdit
from lizard_map.models import CollageEdit


class WorkspacesTest(TestCase):
    """Only smoke tests"""

    class MockRequest(object):
        session = None

    def setUp(self):
        pass

    def test_workspace_edit(self):
        user = User(username='my_little_pony')
        workspace_edit = WorkspaceEdit.get_or_create('fake_key', user)
        mock_request = self.MockRequest()
        context = {'request': mock_request, 'user': user}
        workspaces.workspace_edit(context, workspace_edit)

    def test_collage_edit(self):
        user = User(username='my_little_pony')
        collage_edit = CollageEdit.get_or_create('fake_key', user)
        mock_request = self.MockRequest()
        context = {'request': mock_request, 'user': user}
        workspaces.collage_edit(context, collage_edit)

    def test_collage_item_statistics(self):
        user = User(username='my_little_pony')
        collage_edit = CollageEdit.get_or_create('fake_key', user)
        collage_edit.collage_items.create(
            name='naam1',
            adapter_class='fake adapter',
            adapter_layer_json='',
            identifier='{"id":"id"}')
        mock_request = self.MockRequest()
        workspaces.collage_edit(mock_request, collage_edit.collage_items.all())

    def test_collage_items_html(self):
        user = User(username='my_little_pony')
        collage_edit = CollageEdit.get_or_create('fake_key', user)
        collage_edit.collage_items.create(
            name='naam1',
            adapter_class='fake adapter',
            adapter_layer_json='',
            identifier='{"id":"id"}')
        workspaces.collage_items_html(
            collage_edit.collage_items.all())
