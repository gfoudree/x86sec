# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-06 23:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0002_project'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='link',
        ),
        migrations.AlterField(
            model_name='project',
            name='screenshots',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
