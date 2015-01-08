# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Deleting model 'WorkspaceCollageSnippetGroup'
        db.delete_table('lizard_map_workspacecollagesnippetgroup')

        # Deleting model 'WorkspaceItem'
        db.delete_table('lizard_map_workspaceitem')

        # Deleting model 'Workspace'
        db.delete_table('lizard_map_workspace')

        # Deleting model 'WorkspaceCollage'
        db.delete_table('lizard_map_workspacecollage')

        # Deleting model 'WorkspaceCollageSnippet'
        db.delete_table('lizard_map_workspacecollagesnippet')

        # Adding model 'CollageEdit'
        db.create_table('lizard_map_collageedit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True, null=True, blank=True)),
            ('session_key', self.gf('django.db.models.fields.CharField')(max_length=40, unique=True, null=True, blank=True)),
        ))
        db.send_create_signal('lizard_map', ['CollageEdit'])

        # Adding model 'WorkspaceStorage'
        db.create_table('lizard_map_workspacestorage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dt_start', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('dt_end', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('td_start', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('td_end', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('td', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('absolute', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('custom_time', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('x_min', self.gf('django.db.models.fields.FloatField')(default=-14675)),
            ('y_min', self.gf('django.db.models.fields.FloatField')(default=6668977)),
            ('x_max', self.gf('django.db.models.fields.FloatField')(default=1254790)),
            ('y_max', self.gf('django.db.models.fields.FloatField')(default=6964942)),
            ('background_map', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_map.BackgroundMap'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceStorage'])

        # Adding model 'CollageEditItem'
        db.create_table('lizard_map_collageedititem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('adapter_class', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('adapter_layer_json', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('index', self.gf('django.db.models.fields.IntegerField')(default=100, blank=True)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('clickable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('boundary_value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('percentile_value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('restrict_to_month', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('aggregation_period', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('collage', self.gf('django.db.models.fields.related.ForeignKey')(related_name='collage_items', to=orm['lizard_map.CollageEdit'])),
            ('identifier', self.gf('lizard_map.fields.JSONField')()),
        ))
        db.send_create_signal('lizard_map', ['CollageEditItem'])

        # Adding model 'WorkspaceEdit'
        db.create_table('lizard_map_workspaceedit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dt_start', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('dt_end', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('td_start', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('td_end', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('td', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('absolute', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('custom_time', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('x_min', self.gf('django.db.models.fields.FloatField')(default=-14675)),
            ('y_min', self.gf('django.db.models.fields.FloatField')(default=6668977)),
            ('x_max', self.gf('django.db.models.fields.FloatField')(default=1254790)),
            ('y_max', self.gf('django.db.models.fields.FloatField')(default=6964942)),
            ('background_map', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_map.BackgroundMap'], null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True, null=True, blank=True)),
            ('session_key', self.gf('django.db.models.fields.CharField')(max_length=40, unique=True, null=True, blank=True)),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceEdit'])

        # Adding model 'WorkspaceEditItem'
        db.create_table('lizard_map_workspaceedititem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('adapter_class', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('adapter_layer_json', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('index', self.gf('django.db.models.fields.IntegerField')(default=100, blank=True)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('clickable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('workspace', self.gf('django.db.models.fields.related.ForeignKey')(related_name='workspace_items', to=orm['lizard_map.WorkspaceEdit'])),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceEditItem'])

        # Adding model 'WorkspaceStorageItem'
        db.create_table('lizard_map_workspacestorageitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('adapter_class', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('adapter_layer_json', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('index', self.gf('django.db.models.fields.IntegerField')(default=100, blank=True)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('clickable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('workspace', self.gf('django.db.models.fields.related.ForeignKey')(related_name='workspace_items', to=orm['lizard_map.WorkspaceStorage'])),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceStorageItem'])


    def backwards(self, orm):

        # Adding model 'WorkspaceCollageSnippetGroup'
        db.create_table('lizard_map_workspacecollagesnippetgroup', (
            ('layout_y_label', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
            ('workspace_collage', self.gf('django.db.models.fields.related.ForeignKey')(related_name='snippet_groups', to=orm['lizard_map.WorkspaceCollage'])),
            ('restrict_to_month', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('layout_title', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('aggregation_period', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('index', self.gf('django.db.models.fields.IntegerField')(default=1000)),
            ('layout_y_min', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
            ('boundary_value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('percentile_value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('layout_y_max', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('layout_x_label', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceCollageSnippetGroup'])

        # Adding model 'WorkspaceItem'
        db.create_table('lizard_map_workspaceitem', (
            ('index', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('adapter_layer_json', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('workspace', self.gf('django.db.models.fields.related.ForeignKey')(related_name='workspace_items', to=orm['lizard_map.Workspace'])),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('adapter_class', self.gf('django.db.models.fields.SlugField')(blank=True, max_length=50, db_index=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceItem'])

        # Adding model 'Workspace'
        db.create_table('lizard_map_workspace', (
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='My Workspace', max_length=80, blank=True)),
        ))
        db.send_create_signal('lizard_map', ['Workspace'])

        # Adding model 'WorkspaceCollage'
        db.create_table('lizard_map_workspacecollage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('workspace', self.gf('django.db.models.fields.related.ForeignKey')(related_name='collages', to=orm['lizard_map.Workspace'])),
            ('name', self.gf('django.db.models.fields.CharField')(default='Collage', max_length=80)),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceCollage'])

        # Adding model 'WorkspaceCollageSnippet'
        db.create_table('lizard_map_workspacecollagesnippet', (
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='Snippet', max_length=80)),
            ('snippet_group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='snippets', to=orm['lizard_map.WorkspaceCollageSnippetGroup'])),
            ('workspace_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_map.WorkspaceItem'])),
            ('shortname', self.gf('django.db.models.fields.CharField')(default='Snippet', max_length=80, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier_json', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceCollageSnippet'])

        # Deleting model 'CollageEdit'
        db.delete_table('lizard_map_collageedit')

        # Deleting model 'WorkspaceStorage'
        db.delete_table('lizard_map_workspacestorage')

        # Deleting model 'CollageEditItem'
        db.delete_table('lizard_map_collageedititem')

        # Deleting model 'WorkspaceEdit'
        db.delete_table('lizard_map_workspaceedit')

        # Deleting model 'WorkspaceEditItem'
        db.delete_table('lizard_map_workspaceedititem')

        # Deleting model 'WorkspaceStorageItem'
        db.delete_table('lizard_map_workspacestorageitem')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'lizard_map.backgroundmap': {
            'Meta': {'ordering': "('index',)", 'object_name': 'BackgroundMap'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'google_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'layer_names': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'layer_type': ('django.db.models.fields.IntegerField', [], {}),
            'layer_url': ('django.db.models.fields.CharField', [], {'default': "'http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png'", 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'lizard_map.collageedit': {
            'Meta': {'object_name': 'CollageEdit'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        'lizard_map.collageedititem': {
            'Meta': {'ordering': '()', 'object_name': 'CollageEditItem'},
            'adapter_class': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'adapter_layer_json': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'aggregation_period': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'boundary_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'clickable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'collage': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'collage_items'", 'to': "orm['lizard_map.CollageEdit']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('lizard_map.fields.JSONField', [], {}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'percentile_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'restrict_to_month': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'lizard_map.legend': {
            'Meta': {'object_name': 'Legend'},
            'default_color': ('lizard_map.fields.ColorField', [], {'max_length': '8'}),
            'descriptor': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_color': ('lizard_map.fields.ColorField', [], {'max_length': '8'}),
            'max_value': ('django.db.models.fields.FloatField', [], {'default': '100'}),
            'min_color': ('lizard_map.fields.ColorField', [], {'max_length': '8'}),
            'min_value': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'steps': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'too_high_color': ('lizard_map.fields.ColorField', [], {'max_length': '8'}),
            'too_low_color': ('lizard_map.fields.ColorField', [], {'max_length': '8'})
        },
        'lizard_map.legendpoint': {
            'Meta': {'object_name': 'LegendPoint', '_ormbases': ['lizard_map.Legend']},
            'icon': ('django.db.models.fields.CharField', [], {'default': "'empty.png'", 'max_length': '80'}),
            'legend_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['lizard_map.Legend']", 'unique': 'True', 'primary_key': 'True'}),
            'mask': ('django.db.models.fields.CharField', [], {'default': "'empty_mask.png'", 'max_length': '80', 'null': 'True', 'blank': 'True'})
        },
        'lizard_map.setting': {
            'Meta': {'object_name': 'Setting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'lizard_map.workspaceedit': {
            'Meta': {'object_name': 'WorkspaceEdit'},
            'absolute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'background_map': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_map.BackgroundMap']", 'null': 'True', 'blank': 'True'}),
            'custom_time': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'td': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'td_end': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'td_start': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'x_max': ('django.db.models.fields.FloatField', [], {'default': '1254790'}),
            'x_min': ('django.db.models.fields.FloatField', [], {'default': '-14675'}),
            'y_max': ('django.db.models.fields.FloatField', [], {'default': '6964942'}),
            'y_min': ('django.db.models.fields.FloatField', [], {'default': '6668977'})
        },
        'lizard_map.workspaceedititem': {
            'Meta': {'ordering': "('index', 'visible', 'name')", 'object_name': 'WorkspaceEditItem'},
            'adapter_class': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'adapter_layer_json': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'clickable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'workspace_items'", 'to': "orm['lizard_map.WorkspaceEdit']"})
        },
        'lizard_map.workspacestorage': {
            'Meta': {'object_name': 'WorkspaceStorage'},
            'absolute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'background_map': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_map.BackgroundMap']", 'null': 'True', 'blank': 'True'}),
            'custom_time': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'td': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'td_end': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'td_start': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'x_max': ('django.db.models.fields.FloatField', [], {'default': '1254790'}),
            'x_min': ('django.db.models.fields.FloatField', [], {'default': '-14675'}),
            'y_max': ('django.db.models.fields.FloatField', [], {'default': '6964942'}),
            'y_min': ('django.db.models.fields.FloatField', [], {'default': '6668977'})
        },
        'lizard_map.workspacestorageitem': {
            'Meta': {'ordering': "('index', 'visible', 'name')", 'object_name': 'WorkspaceStorageItem'},
            'adapter_class': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'adapter_layer_json': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'clickable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'workspace_items'", 'to': "orm['lizard_map.WorkspaceStorage']"})
        }
    }

    complete_apps = ['lizard_map']
