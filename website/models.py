# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Post(models.Model):
    pub_date = models.DateTimeField()
    tags = models.CharField(max_length=100)
    content = models.CharField(max_length=50)
    title = models.CharField(max_length=100)

class Download(models.Model):
    tags = models.CharField(max_length=100)
    name = models.CharField(max_length=50)
    os = models.CharField(max_length=15, blank=True)
    description = models.TextField()
    link = models.URLField()

class Project(models.Model):
    tags = models.CharField(max_length=100)
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    description = models.TextField()
    screenshots = models.CharField(max_length=500, blank=True)
    githubLink = models.URLField()

#call manage.py makemigrations to create migrations
#call manage.py migrate to apply changes to DB
