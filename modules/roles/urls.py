from django.urls import path

from . import views

urlpatterns = [
    path('', views.role_list, name='role_list'),
    path('add/', views.role_add, name='role_add'),
    path('<int:role_id>/edit/', views.role_edit, name='role_edit'),
    path('<int:role_id>/delete/', views.role_delete, name='role_delete'),
]
