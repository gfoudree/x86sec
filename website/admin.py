# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Post, Download, Project
# Register your models here.

admin.site.register(Post)
admin.site.register(Download)
admin.site.register(Project)
