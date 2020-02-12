# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from website.models import Project, Post, Download

# Create your views here.
def index(request):
    post_objs = Post.objects.all()
    return render(request, 'index.html', {'title' : 'Home', 'posts' : reversed(post_objs)}) #Serve in reverse order

def projects(request):
    project_objs = Project.objects.all()
    return render(request, 'projects.html', {'title' : 'Projects', 'projects' : project_objs})

def downloads(request):
    download_objs = Download.objects.all()
    return render(request, 'downloads.html', {'title' : 'Downloads'})

def about(request):
    return render(request, 'about.html', {'title' : 'About Me'})
