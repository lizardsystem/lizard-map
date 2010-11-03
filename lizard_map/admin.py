from django.contrib import admin

from lizard_map.models import Legend
from lizard_map.models import LegendPoint
from lizard_map.models import Workspace
from lizard_map.models import WorkspaceItem
from lizard_map.models import WorkspaceCollage
from lizard_map.models import WorkspaceCollageSnippet
from lizard_map.models import WorkspaceCollageSnippetGroup


class WorkspaceItemInline(admin.TabularInline):
    model = WorkspaceItem


class WorkspaceCollageInline(admin.TabularInline):
    model = WorkspaceCollage


class WorkspaceCollageSnippetInline(admin.TabularInline):
    model = WorkspaceCollageSnippet


class WorkspaceCollageSnippetGroupInline(admin.TabularInline):
    model = WorkspaceCollageSnippetGroup


class WorkspaceAdmin(admin.ModelAdmin):
    inlines = [
        WorkspaceItemInline,
        WorkspaceCollageInline,
        ]


class WorkspaceCollageAdmin(admin.ModelAdmin):
    inlines = [
        WorkspaceCollageSnippetGroupInline,
        ]


class WorkspaceCollageSnippetGroupAdmin(admin.ModelAdmin):
    list_display = ('snippets_summary', 'workspace', 'workspace_collage',
                    'index', 'name', )
    inlines = [
        WorkspaceCollageSnippetInline,
        ]


admin.site.register(Legend)
admin.site.register(LegendPoint)
admin.site.register(Workspace, WorkspaceAdmin)
admin.site.register(WorkspaceItem)
admin.site.register(WorkspaceCollage, WorkspaceCollageAdmin)
admin.site.register(WorkspaceCollageSnippet)
admin.site.register(WorkspaceCollageSnippetGroup,
                    WorkspaceCollageSnippetGroupAdmin)
