# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    return render(request, 'index.html', {'title' : 'Home'})

def projects(request):
    return render(request, 'projects.html', {'title' : 'Projects'})

def posts(request):
    return render(request, 'posts.html', {'title' : 'Posts'})

def downloads(request):
    return render(request, 'downloads.html', {'title' : 'Downloads'})

def about(request):
    return render(request, 'about.html', {'title' : 'About Me'})
