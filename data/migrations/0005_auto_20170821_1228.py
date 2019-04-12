# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-21 09:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0004_intraservicetask_pended_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='intraservicetask',
            old_name='pended_type',
            new_name='postponed_type',
        ),
        migrations.AddField(
            model_name='intraservicetask',
            name='postponed_executor',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='data.Executor'),
        ),
    ]