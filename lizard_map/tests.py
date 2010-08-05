from django.test import TestCase

import lizard_map.admin
import lizard_map.models
import lizard_map.urls
import lizard_map.views
import lizard_map.layers
import lizard_map.workspace


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


class WorkspaceTest(TestCase):

    def test_workspace_creation(self):
        """We use the WorkspaceManager to find and create our workspaces"""
        mock_request = {}
        workspace_manager = lizard_map.workspace.WorkspaceManager(
            mock_request)

# TODO: re-integrate the doctests from models.txt somehow

