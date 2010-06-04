from django.contrib import admin

from lizard_map.models import Workspace
from lizard_map.models import WorkspaceItem
from lizard_map.models import WorkspaceCollage
from lizard_map.models import WorkspaceCollageSnippet


class WorkspaceItemInline(admin.TabularInline):
    model = WorkspaceItem


class WorkspaceAdmin(admin.ModelAdmin):
    inlines = [
        WorkspaceItemInline,
        ]


admin.site.register(Workspace, WorkspaceAdmin)
admin.site.register(WorkspaceItem)
admin.site.register(WorkspaceCollage)
admin.site.register(WorkspaceCollageSnippet)
