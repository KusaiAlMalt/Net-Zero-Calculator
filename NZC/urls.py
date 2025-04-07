from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), #TODO: add index page
    path('about/', views.about, name='about'), #TODO: add about page
    path('pdf/', views.pdf, name='pdf'), #TODO: add pdf page
    path('manual/', views.manual, name='manual'), #TODO: add manual page
    path('results/', views.results, name='results'), #TODO: add results page
]