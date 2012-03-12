# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Setting.key'
        db.alter_column('lizard_map_setting', 'key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40))


    def backwards(self, orm):
        
        # Changing field 'Setting.key'
        db.alter_column('lizard_map_setting', 'key', self.gf('django.db.models.fields.CharField')(max_length=20, unique=True))


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
        'lizard_map.workspace': {
            'Meta': {'object_name': 'Workspace'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'My Workspace'", 'max_length': '80', 'blank': 'True'}),
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
            'Meta': {'ordering': "['name']", 'object_name': 'WorkspaceCollageSnippet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier_json': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'Snippet'", 'max_length': '80'}),
            'shortname': ('django.db.models.fields.CharField', [], {'default': "'Snippet'", 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'snippet_group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'snippets'", 'to': "orm['lizard_map.WorkspaceCollageSnippetGroup']"}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
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
