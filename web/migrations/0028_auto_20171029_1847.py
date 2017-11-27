# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-29 12:47
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0027_auto_20171029_1834'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='register_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 29, 12, 47, 52, 377287, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='tree',
            name='lastTimeShow',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 29, 12, 47, 52, 381773, tzinfo=utc)),
        ),
    ]
