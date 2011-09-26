from django.contrib import admin

from lizard_map.models import BackgroundMap
#from lizard_map.models import Legend
#from lizard_map.models import LegendPoint
from lizard_map.models import Setting
from lizard_map.models import CollageEdit
from lizard_map.models import CollageEditItem
#from lizard_map.models import Workspace
#from lizard_map.models import WorkspaceCollage
#from lizard_map.models import WorkspaceCollageSnippet
#from lizard_map.models import WorkspaceCollageSnippetGroup
#from lizard_map.models import WorkspaceItem
from lizard_map.models import WorkspaceEdit
from lizard_map.models import WorkspaceEditItem
from lizard_map.models import WorkspaceStorage
from lizard_map.models import WorkspaceStorageItem


# class WorkspaceItemInline(admin.TabularInline):
#     model = WorkspaceItem


class WorkspaceEditItemInline(admin.TabularInline):
    model = WorkspaceEditItem


class WorkspaceStorageItemInline(admin.TabularInline):
    model = WorkspaceStorageItem


class CollageEditItemInline(admin.TabularInline):
    model = CollageEditItem


# class WorkspaceCollageInline(admin.TabularInline):
#     model = WorkspaceCollage


# class WorkspaceCollageSnippetInline(admin.TabularInline):
#     model = WorkspaceCollageSnippet


# class WorkspaceCollageSnippetGroupInline(admin.TabularInline):
#     model = WorkspaceCollageSnippetGroup


class CollageEditAdmin(admin.ModelAdmin):
    inlines = [
        CollageEditItemInline,
        ]


class CollageEditItemAdmin(admin.ModelAdmin):
    pass


# class WorkspaceAdmin(admin.ModelAdmin):
#     inlines = [
#         WorkspaceItemInline,
#         WorkspaceCollageInline,
#         ]


class WorkspaceEditAdmin(admin.ModelAdmin):
    inlines = [
        WorkspaceEditItemInline,
        ]


class WorkspaceStorageAdmin(admin.ModelAdmin):
    inlines = [
        WorkspaceStorageItemInline,
        ]


# class WorkspaceCollageAdmin(admin.ModelAdmin):
#     inlines = [
#         WorkspaceCollageSnippetGroupInline,
#         ]


# class WorkspaceCollageSnippetGroupAdmin(admin.ModelAdmin):
#     list_display = ('snippets_summary', 'workspace', 'workspace_collage',
#                     'index', 'name', )
#     inlines = [
#         WorkspaceCollageSnippetInline,
#         ]


class BackgroundMapAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'default', 'index', )
    list_editable = ('default', 'index', 'active', )


admin.site.register(BackgroundMap, BackgroundMapAdmin)
admin.site.register(CollageEdit, CollageEditAdmin)
admin.site.register(CollageEditItem, CollageEditItemAdmin)
# admin.site.register(Legend)
# admin.site.register(LegendPoint)
admin.site.register(Setting)
# admin.site.register(Workspace, WorkspaceAdmin)
# admin.site.register(WorkspaceCollage, WorkspaceCollageAdmin)
# admin.site.register(WorkspaceCollageSnippet)
# admin.site.register(WorkspaceCollageSnippetGroup,
#                     WorkspaceCollageSnippetGroupAdmin)
# admin.site.register(WorkspaceItem)
admin.site.register(WorkspaceEdit, WorkspaceEditAdmin)
admin.site.register(WorkspaceStorage, WorkspaceStorageAdmin)
