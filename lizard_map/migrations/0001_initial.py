# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Workspace'
        db.create_table('lizard_map_workspace', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='Workspace', max_length=80, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('lizard_map', ['Workspace'])

        # Adding model 'WorkspaceItem'
        db.create_table('lizard_map_workspaceitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('workspace', self.gf('django.db.models.fields.related.ForeignKey')(related_name='workspace_items', to=orm['lizard_map.Workspace'])),
            ('adapter_class', self.gf('django.db.models.fields.SlugField')(db_index=True, max_length=50, blank=True)),
            ('adapter_layer_json', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('index', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceItem'])

        # Adding model 'WorkspaceCollage'
        db.create_table('lizard_map_workspacecollage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='Collage', max_length=80)),
            ('workspace', self.gf('django.db.models.fields.related.ForeignKey')(related_name='collages', to=orm['lizard_map.Workspace'])),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceCollage'])

        # Adding model 'WorkspaceCollageSnippetGroup'
        db.create_table('lizard_map_workspacecollagesnippetgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('workspace_collage', self.gf('django.db.models.fields.related.ForeignKey')(related_name='snippet_groups', to=orm['lizard_map.WorkspaceCollage'])),
            ('index', self.gf('django.db.models.fields.IntegerField')(default=1000)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
            ('boundary_value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('percentile_value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('restrict_to_month', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('aggregation_period', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('layout_title', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
            ('layout_x_label', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
            ('layout_y_label', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
            ('layout_y_min', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('layout_y_max', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceCollageSnippetGroup'])

        # Adding model 'WorkspaceCollageSnippet'
        db.create_table('lizard_map_workspacecollagesnippet', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='Snippet', max_length=80)),
            ('shortname', self.gf('django.db.models.fields.CharField')(default='Snippet', max_length=80, null=True, blank=True)),
            ('snippet_group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='snippets', to=orm['lizard_map.WorkspaceCollageSnippetGroup'])),
            ('workspace_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_map.WorkspaceItem'])),
            ('identifier_json', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('lizard_map', ['WorkspaceCollageSnippet'])

        # Adding model 'Legend'
        db.create_table('lizard_map_legend', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('descriptor', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('min_value', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('max_value', self.gf('django.db.models.fields.FloatField')(default=100)),
            ('steps', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('default_color', self.gf('lizard_map.fields.ColorField')(max_length=8)),
            ('min_color', self.gf('lizard_map.fields.ColorField')(max_length=8)),
            ('max_color', self.gf('lizard_map.fields.ColorField')(max_length=8)),
            ('too_low_color', self.gf('lizard_map.fields.ColorField')(max_length=8)),
            ('too_high_color', self.gf('lizard_map.fields.ColorField')(max_length=8)),
        ))
        db.send_create_signal('lizard_map', ['Legend'])

        # Adding model 'LegendPoint'
        db.create_table('lizard_map_legendpoint', (
            ('legend_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['lizard_map.Legend'], unique=True, primary_key=True)),
            ('icon', self.gf('django.db.models.fields.CharField')(default='empty.png', max_length=80)),
            ('mask', self.gf('django.db.models.fields.CharField')(default='empty_mask.png', max_length=80, null=True, blank=True)),
        ))
        db.send_create_signal('lizard_map', ['LegendPoint'])


    def backwards(self, orm):
        
        # Deleting model 'Workspace'
        db.delete_table('lizard_map_workspace')

        # Deleting model 'WorkspaceItem'
        db.delete_table('lizard_map_workspaceitem')

        # Deleting model 'WorkspaceCollage'
        db.delete_table('lizard_map_workspacecollage')

        # Deleting model 'WorkspaceCollageSnippetGroup'
        db.delete_table('lizard_map_workspacecollagesnippetgroup')

        # Deleting model 'WorkspaceCollageSnippet'
        db.delete_table('lizard_map_workspacecollagesnippet')

        # Deleting model 'Legend'
        db.delete_table('lizard_map_legend')

        # Deleting model 'LegendPoint'
        db.delete_table('lizard_map_legendpoint')


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
        'lizard_map.workspace': {
            'Meta': {'object_name': 'Workspace'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'Workspace'", 'max_length': '80', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'lizard_map.workspacecollage': {
            'Meta': {'object_name': 'WorkspaceCollage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'Collage'", 'max_length': '80'}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'collages'", 'to': "orm['lizard_map.Workspace']"})
        },
        'lizard_map.workspacecollagesnippet': {
            'Meta': {'object_name': 'WorkspaceCollageSnippet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier_json': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'Snippet'", 'max_length': '80'}),
            'shortname': ('django.db.models.fields.CharField', [], {'default': "'Snippet'", 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'snippet_group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'snippets'", 'to': "orm['lizard_map.WorkspaceCollageSnippetGroup']"}),
            'workspace_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_map.WorkspaceItem']"})
        },
        'lizard_map.workspacecollagesnippetgroup': {
            'Meta': {'ordering': "['name']", 'object_name': 'WorkspaceCollageSnippetGroup'},
            'aggregation_period': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'boundary_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '1000'}),
            'layout_title': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'layout_x_label': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'layout_y_label': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'layout_y_max': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'layout_y_min': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'percentile_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'restrict_to_month': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'workspace_collage': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'snippet_groups'", 'to': "orm['lizard_map.WorkspaceCollage']"})
        },
        'lizard_map.workspaceitem': {
            'Meta': {'ordering': "['index']", 'object_name': 'WorkspaceItem'},
            'adapter_class': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'adapter_layer_json': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'workspace_items'", 'to': "orm['lizard_map.Workspace']"})
        }
    }

    complete_apps = ['lizard_map']
