from django.contrib import admin
from django.urls import path
from mon_application import views

urlpatterns = [
    path('', views.renderIndex, name="index"),
    path('planning/', views.planning_view, name='planning'),
]
