from lizard_map.models import Workspace


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
        else:
            #clear all items in temp workspace
            for workspace in self.workspaces['temp']:
                workspace.workspace_items.all().delete()

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

    def layer(self, *args, **kwargs):
        raise "Not implemented"

    def search(self, x, r, radius=None, *args, **kwargs):
        raise "Not implemented"

    def location(self, id=None):
        raise "Not implemented"

    def image(self, id_list=None):
        raise "Not implemented"
