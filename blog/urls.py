from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('<slug:slug>/', views.detail, name='detail'),
    path('', views.index, name='index'),
]