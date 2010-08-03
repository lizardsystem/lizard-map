from django.contrib import admin

from lizard_map.models import Workspace
from lizard_map.models import WorkspaceItem
from lizard_map.models import WorkspaceCollage
from lizard_map.models import WorkspaceCollageSnippet


class WorkspaceItemInline(admin.TabularInline):
    model = WorkspaceItem


class WorkspaceCollageInline(admin.TabularInline):
    model = WorkspaceCollage


class WorkspaceCollageSnippetInline(admin.TabularInline):
    model = WorkspaceCollageSnippet


class WorkspaceAdmin(admin.ModelAdmin):
    inlines = [
        WorkspaceItemInline,
        WorkspaceCollageInline,
        ]


class WorkspaceCollageAdmin(admin.ModelAdmin):
    inlines = [
        WorkspaceCollageSnippetInline,
        ]

admin.site.register(Workspace, WorkspaceAdmin)
admin.site.register(WorkspaceItem)
admin.site.register(WorkspaceCollage, WorkspaceCollageAdmin)
admin.site.register(WorkspaceCollageSnippet)
