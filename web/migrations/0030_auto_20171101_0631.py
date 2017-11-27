# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-01 00:31
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0029_auto_20171030_2246'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='phone',
            field=models.CharField(blank=True, default='', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='register_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 1, 0, 31, 52, 946569, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='superadminsettings',
            name='date',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 1, 0, 31, 52, 954372, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='tree',
            name='lastTimeShow',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 1, 0, 31, 52, 951050, tzinfo=utc)),
        ),
    ]
