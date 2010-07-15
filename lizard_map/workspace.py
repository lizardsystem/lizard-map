import os

from django.conf import settings

from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
import simplejson as json

from lizard_map.models import Workspace
from lizard_map.models import ICON_ORIGINALS
from lizard_map.symbol_manager import SymbolManager


class WorkspaceManager:
    def __init__(self, request):
        self.request = request
        self.workspaces = {}

    def save_workspaces(self):
        """save workspaces to session"""
        workspaces_id = {}
        for k, workspace_list in self.workspaces.items():
            workspaces_id[k] = [workspace.id for workspace in workspace_list]
        self.request.session['workspaces'] = workspaces_id

    def load_workspaces(self, workspaces_id=None):
        """load workspaces from session

        returns number of workspaces that could not be loaded"""
        errors = 0
        # TODO: fix up workspaces_id and workspace_ids as those terms are too
        # similar.  They will lead to coding errors.
        if workspaces_id is None:
            workspaces_id = self.request.session['workspaces']
        for k, workspace_ids in workspaces_id.items():
            self.workspaces[k] = []
            for workspace_id in workspace_ids:
                try:
                    new_workspace = Workspace.objects.get(pk=workspace_id)
                    self.workspaces[k].append(new_workspace)
                except Workspace.DoesNotExist:
                    errors += 1
        return errors

    def empty(self, category='temp'):
        #clear all items in workspace category
        for workspace in self.workspaces[category]:
            workspace.workspace_items.all().delete()

    def load_or_create(self, new_workspace=False):
        """load workspaces references by session['workspaces'] or
        create new workspace

        workspaces are returned in a dictionary:
        {
        'default': [...default layers],
        'temp': workspace_temp,
        'user': [...user workspaces]
        }

        they are stored in the session as a dictionary of ids:
        {
        'default': [id1, id2, ...],
        'temp': [id, ],
        'user': [id3, id4, ...],
        }
        """

        self.workspaces = {}
        changes = False
        if 'workspaces' in self.request.session:
            changes = self.load_workspaces()

        #check if components exist, else create them
        if not 'default' in self.workspaces:
            try:
                self.workspaces['default'] = [Workspace.objects.get(name='achtergrond'), ]
            except Workspace.DoesNotExist:
                pass
            changes = True

        if not 'temp' in self.workspaces:
            workspace_temp = Workspace(name='temp')
            workspace_temp.save()
            self.workspaces['temp'] = [workspace_temp, ]
            changes = True

        if (new_workspace or
            not 'user' in self.workspaces or
            not len(self.workspaces['user'])):
            workspace_user = Workspace()
            workspace_user.save()
            self.workspaces['user'] = [workspace_user, ]
            changes = True

        #create collage if necessary, it is stored in the workspace
        if len(self.workspaces['user'][0].collages.all()) == 0:
            self.workspaces['user'][0].collages.create()

        if changes:
            self.save_workspaces()
        return self.workspaces


# The Workspace item adapter implements workspace item behavior of a
# specific type adapter_class"
class WorkspaceItemAdapter(object):
    layer_arguments = {}

    def __init__(self, workspace_item, layer_arguments=None):
        self.workspace_item = workspace_item
        if layer_arguments is not None:
            self.layer_arguments = layer_arguments
        else:
            self.layer_arguments = {}

    def layer(self):
        """Return xyz"""
        raise NotImplementedError

    def search(self, x, y, radius=None):
        """Return list of dicts for matching items.

        {'distance': <float>,
        'workspace_item': <...>,
        'identifier': {...},
        'google_x': x coordinate in google,
        'google_y': y coordinate in google,
        'object': <object>} of closest fews point that matches x, y, radius.

        """
        raise NotImplementedError

    def location(self, identifier=None, layout=None):
        """Return fews point representation corresponding to filter_id, location_id and
        parameter_id in same format as search function

        layout is a dict with extra optional layout parameters:
        y_min, y_max, y_label, x_label, line_avg, line_max, line_min

        {'object': <...>,
        'google_x': x coordinate in google,
        'google_y': y coordinate in google,
        'workspace_item': <...>,
        'identifier': {...}}

        """
        raise NotImplementedError

    def image(self, identifiers=None, start_date=None, end_date=None, width=None, height=None):
        """Return xyz"""
        raise NotImplementedError

    def symbol_url(self, identifier=None, start_date=None, end_date=None, icon_style=None):
        """Return symbol for identifier"""
        sm = SymbolManager(ICON_ORIGINALS, os.path.join(
                settings.MEDIA_ROOT,
                'generated_icons'))
        if icon_style is None:
            icon_style = {'icon': 'brug.png'}
        output_filename = sm.get_symbol_transformed(icon_style['icon'], **icon_style)
        return settings.MEDIA_URL + 'generated_icons/' + output_filename

    def html(self, identifiers=None, add_snippet=False):
        return 'html output for this adapter is not implemented'

    def html_default(self, identifiers=None, add_snippet=False):
        """
        Returns html representation of given identifier_list.
        This particular view always renders a list of items, then 1 image

        Use this function if html function behaviour is default:
        def html(self, identifiers):
            return super(WorkspaceItemAdapterKrw, self).html_default(
                identifiers)
        """
        title = self.workspace_item.name

        # Make 'display_group'
        display_group = [self.location(**identifier) for identifier in identifiers]

        # Image url
        img_url = reverse(
            "lizard_map.workspace_item_image",
            kwargs={'workspace_item_id': self.workspace_item.id}
            )
        identifiers_escaped = [json.dumps(identifier).replace('"', '%22') for \
                                   identifier in identifiers]
        img_url = img_url + '?' + '&'.join(['identifier=%s' % i for i in
                                            identifiers_escaped])

        return render_to_string(
            'lizard_map/popup.html',
            {
                'title': title,
                'display_group': display_group,
                'img_url': img_url,
                'symbol_url': self.symbol_url(),
                'add_snippet': add_snippet,
                }
            )
