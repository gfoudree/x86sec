# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-11 19:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0003_auto_20170706_2335'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='gpg_signature',
        ),
    ]
