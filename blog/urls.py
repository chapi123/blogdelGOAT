from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('cuenta/', views.account, name='account'),
    path('sesion-cerrada/', views.logged_out, name='logged_out'),
    path('deslogearse/', views.logout_view, name='logout'),
    path('<slug:slug>/comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('<slug:slug>/', views.detail, name='detail'),
    path('', views.index, name='index'),
]