# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'JTILog'
        db.create_table('aaf_auth_jtilog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('jti', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('aaf_auth', ['JTILog'])


    def backwards(self, orm):
        # Deleting model 'JTILog'
        db.delete_table('aaf_auth_jtilog')


    models = {
        'aaf_auth.jtilog': {
            'Meta': {'object_name': 'JTILog'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jti': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['aaf_auth']