# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-04 12:42
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0016_auto_20171004_1839'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='register_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 4, 12, 42, 43, 919017, tzinfo=utc)),
        ),
    ]
