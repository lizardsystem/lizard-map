# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'CollageStorageItem.collage_storage'
        db.delete_column(u'lizard_map_collagestorageitem', 'collage_storage_id')

        # Adding field 'CollageStorageItem.collage'
        db.add_column(u'lizard_map_collagestorageitem', 'collage',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='collage_items', to=orm['lizard_map.CollageStorage']),
                      keep_default=False)


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'CollageStorageItem.collage_storage'
        raise RuntimeError("Cannot reverse this migration. 'CollageStorageItem.collage_storage' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'CollageStorageItem.collage_storage'
        db.add_column(u'lizard_map_collagestorageitem', 'collage_storage',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='collage_items', to=orm['lizard_map.CollageStorage']),
                      keep_default=False)

        # Deleting field 'CollageStorageItem.collage'
        db.delete_column(u'lizard_map_collagestorageitem', 'collage_id')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'lizard_map.backgroundmap': {
            'Meta': {'ordering': "('index',)", 'object_name': 'BackgroundMap'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'google_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'is_base_layer': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_single_tile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'layer_names': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'layer_type': ('django.db.models.fields.IntegerField', [], {}),
            'layer_url': ('django.db.models.fields.CharField', [], {'default': "'http://tile.openstreetmap.nl/tiles/${z}/${x}/${y}.png'", 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'lizard_map.collageedit': {
            'Meta': {'object_name': 'CollageEdit'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'lizard_map.collageedititem': {
            'Meta': {'ordering': "('name',)", 'object_name': 'CollageEditItem'},
            'adapter_class': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'adapter_layer_json': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'aggregation_period': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'boundary_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'clickable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'collage': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'collage_items'", 'to': u"orm['lizard_map.CollageEdit']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'percentile_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'restrict_to_month': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'lizard_map.collagestorage': {
            'Meta': {'ordering': "('index',)", 'object_name': 'CollageStorage'},
            'data_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['lizard_security.DataSet']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'secret_slug': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True'})
        },
        u'lizard_map.collagestorageitem': {
            'Meta': {'ordering': "('name',)", 'object_name': 'CollageStorageItem'},
            'adapter_class': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'adapter_layer_json': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'aggregation_period': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'boundary_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'clickable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'collage': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'collage_items'", 'to': u"orm['lizard_map.CollageStorage']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'percentile_value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'restrict_to_month': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'lizard_map.legend': {
            'Meta': {'object_name': 'Legend'},
            'default_color': ('lizard_map.fields.ColorField', [], {'max_length': '8'}),
            'descriptor': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_color': ('lizard_map.fields.ColorField', [], {'max_length': '8'}),
            'max_value': ('django.db.models.fields.FloatField', [], {'default': '100'}),
            'min_color': ('lizard_map.fields.ColorField', [], {'max_length': '8'}),
            'min_value': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'steps': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'too_high_color': ('lizard_map.fields.ColorField', [], {'max_length': '8'}),
            'too_low_color': ('lizard_map.fields.ColorField', [], {'max_length': '8'})
        },
        u'lizard_map.legendpoint': {
            'Meta': {'object_name': 'LegendPoint', '_ormbases': [u'lizard_map.Legend']},
            'icon': ('django.db.models.fields.CharField', [], {'default': "'empty.png'", 'max_length': '80'}),
            u'legend_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['lizard_map.Legend']", 'unique': 'True', 'primary_key': 'True'}),
            'mask': ('django.db.models.fields.CharField', [], {'default': "'empty_mask.png'", 'max_length': '80', 'null': 'True', 'blank': 'True'})
        },
        u'lizard_map.setting': {
            'Meta': {'object_name': 'Setting'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'lizard_map.workspaceedit': {
            'Meta': {'object_name': 'WorkspaceEdit'},
            'absolute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'background_map': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['lizard_map.BackgroundMap']", 'null': 'True', 'blank': 'True'}),
            'custom_time': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'td': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'td_end': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'td_start': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'x_max': ('django.db.models.fields.FloatField', [], {'default': '1254790'}),
            'x_min': ('django.db.models.fields.FloatField', [], {'default': '-14675'}),
            'y_max': ('django.db.models.fields.FloatField', [], {'default': '6964942'}),
            'y_min': ('django.db.models.fields.FloatField', [], {'default': '6668977'})
        },
        u'lizard_map.workspaceedititem': {
            'Meta': {'ordering': "('index', 'visible', 'name')", 'object_name': 'WorkspaceEditItem'},
            'adapter_class': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'adapter_layer_json': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'clickable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'workspace_items'", 'to': u"orm['lizard_map.WorkspaceEdit']"})
        },
        u'lizard_map.workspacestorage': {
            'Meta': {'ordering': "('index',)", 'object_name': 'WorkspaceStorage'},
            'absolute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'background_map': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['lizard_map.BackgroundMap']", 'null': 'True', 'blank': 'True'}),
            'custom_time': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'data_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['lizard_security.DataSet']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'extent_is_set': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rightbar_is_collapsed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'secret_slug': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True'}),
            'sidebar_is_collapsed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'td': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'td_end': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'td_start': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'x_max': ('django.db.models.fields.FloatField', [], {'default': '1254790'}),
            'x_min': ('django.db.models.fields.FloatField', [], {'default': '-14675'}),
            'y_max': ('django.db.models.fields.FloatField', [], {'default': '6964942'}),
            'y_min': ('django.db.models.fields.FloatField', [], {'default': '6668977'})
        },
        u'lizard_map.workspacestorageitem': {
            'Meta': {'ordering': "('index', 'visible', 'name')", 'object_name': 'WorkspaceStorageItem'},
            'adapter_class': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'adapter_layer_json': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'clickable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'workspace_items'", 'to': u"orm['lizard_map.WorkspaceStorage']"})
        },
        u'lizard_security.dataset': {
            'Meta': {'ordering': "['name']", 'object_name': 'DataSet'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'})
        }
    }

    complete_apps = ['lizard_map']