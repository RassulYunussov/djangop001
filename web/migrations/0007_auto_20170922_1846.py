# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-22 12:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0006_auto_20170922_1841'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
