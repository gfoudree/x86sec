# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-11 22:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0005_auto_20171111_2212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='download',
            name='os',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AlterField(
            model_name='post',
            name='content',
            field=models.CharField(max_length=50),
        ),
    ]