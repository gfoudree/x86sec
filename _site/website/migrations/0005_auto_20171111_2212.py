# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-11 22:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0004_remove_post_gpg_signature'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='content',
            field=models.CharField(max_length=25),
        ),
    ]