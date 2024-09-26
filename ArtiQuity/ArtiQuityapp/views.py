from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def home(request):
    return render(request,'ArtQuityapp/home.html')
def about(request):
    return HttpResponse("Welcome to ArtiQuity")

