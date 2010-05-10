from django.contrib import admin

from lizard_map.models import Workspace
from lizard_map.models import WorkspaceItem

admin.site.register(Workspace)
admin.site.register(WorkspaceItem)
