from django.contrib import admin

from lizard_map.models import BackgroundMap
from lizard_map.models import Setting


class BackgroundMapAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'default', 'index', )
    list_editable = ('default', 'index', 'active', )


admin.site.register(BackgroundMap, BackgroundMapAdmin)
admin.site.register(Setting)
