# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-03 17:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0015_auto_20170916_1311'),
    ]

    operations = [
        migrations.CreateModel(
            name='IntraserviceTest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('status', models.BooleanField()),
                ('error', models.CharField(max_length=60)),
            ],
        ),
    ]
