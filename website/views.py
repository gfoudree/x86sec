# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from .models import Project

# Create your views here.
def index(request):
    return render(request, 'index.html', {'title' : 'Home'})

def projects(request):
    projects = Project.objects.all()
    return render(request, 'projects.html', {'title' : 'Projects', 'projects' : projects})

def projectViewer(request, project):
    return render(request, 'projectViewer.html', {'title' : project})

def posts(request):
    return render(request, 'posts.html', {'title' : 'Posts'})

def downloads(request):
    return render(request, 'downloads.html', {'title' : 'Downloads'})

def about(request):
    return render(request, 'about.html', {'title' : 'About Me'})
