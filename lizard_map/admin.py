from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from lizard_security.admin import SecurityFilteredAdmin

from lizard_map.models import BackgroundMap
from lizard_map.models import Legend
from lizard_map.models import LegendPoint
from lizard_map.models import Setting
from lizard_map.models import CollageEdit
from lizard_map.models import CollageEditItem
from lizard_map.models import WorkspaceEdit
from lizard_map.models import WorkspaceEditItem
from lizard_map.models import WorkspaceStorage
from lizard_map.models import WorkspaceStorageItem
from lizard_map.models import CollageStorage
from lizard_map.models import CollageStorageItem


class WorkspaceEditItemInline(admin.TabularInline):
    model = WorkspaceEditItem


class WorkspaceStorageItemInline(admin.TabularInline):
    model = WorkspaceStorageItem


class CollageEditItemInline(admin.TabularInline):
    model = CollageEditItem


class CollageEditAdmin(admin.ModelAdmin):
    inlines = [
        CollageEditItemInline,
        ]


class CollageEditItemAdmin(admin.ModelAdmin):
    pass


class WorkspaceEditAdmin(admin.ModelAdmin):
    inlines = [
        WorkspaceEditItemInline,
        ]


class WorkspaceStorageAdmin(SecurityFilteredAdmin):
    list_display = ('name', 'owner', 'secret_slug', 'index', 'data_set')
    inlines = [
        WorkspaceStorageItemInline,
        ]


class BackgroundMapAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'default', 'index', )
    list_editable = ('default', 'index', 'active', )


class CollageStorageItemInline(admin.TabularInline):
    model = CollageStorageItem


class CollageStorageAdmin(SecurityFilteredAdmin):
    list_display = ('name', 'owner', 'secret_slug', 'url', 'data_set')
    readonly_fields = ('url',)
    inlines = [
        CollageStorageItemInline,
        ]

    def url(self, instance):
        if instance.secret_slug:
            the_url = reverse(
                'lizard_map_collage_slug_storage',
                kwargs={'collage_storage_slug': instance.secret_slug})
        else:
            the_url = reverse(
                'lizard_map_collage_storage',
                kwargs={'collage_id': instance.id})

        return mark_safe('<a href="%s">%s</a>' % (the_url, the_url))


admin.site.register(BackgroundMap, BackgroundMapAdmin)
admin.site.register(CollageEdit, CollageEditAdmin)
admin.site.register(CollageStorage, CollageStorageAdmin)
admin.site.register(CollageEditItem, CollageEditItemAdmin)
admin.site.register(Legend)
admin.site.register(LegendPoint)
admin.site.register(Setting)
admin.site.register(WorkspaceEdit, WorkspaceEditAdmin)
admin.site.register(WorkspaceStorage, WorkspaceStorageAdmin)
