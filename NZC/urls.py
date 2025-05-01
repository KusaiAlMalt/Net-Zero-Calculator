from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('pdf', views.pdf, name='pdf'),
    path('manual', views.manual, name='manual'),
    path('results', views.results, name='results'),
    path('ccs_methods', views.ccs_methods, name='ccs_methods'),
]