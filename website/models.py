# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Post(models.Model):
    pub_date = models.DateTimeField()
    tags = models.CharField(max_length=100)
    content = models.TextField()
    title = models.CharField(max_length=100)
    gpg_signature = models.TextField()

class Download(models.Model):
    tags = models.CharField(max_length=100)
    name = models.CharField(max_length=50)
    os = models.CharField(max_length=15)
    description = models.TextField()
    link = models.URLField()

#call manage.py makemigrations to create migrations
#call manage.py migrate to apply changes to DB
