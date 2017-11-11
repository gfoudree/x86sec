# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from website.models import Project, Post

# Create your views here.
def index(request):
    posts = Post.objects.all()
    return render(request, 'index.html', {'title' : 'Home', 'posts' : posts})

def projects(request):
    projects = Project.objects.all()
    return render(request, 'projects.html', {'title' : 'Projects', 'projects' : projects})

def projectViewer(request, project):
    return render(request, 'projectViewer.html', {'title' : project})

def downloads(request):
    return render(request, 'downloads.html', {'title' : 'Downloads'})

def about(request):
    return render(request, 'about.html', {'title' : 'About Me'})
