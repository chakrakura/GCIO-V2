from django.urls import path

from . import views

urlpatterns = [
    path('', views.organization_list, name='organization_list'),
    path('add/', views.organization_add, name='organization_add'),
    path('<int:org_id>/edit/', views.organization_edit, name='organization_edit'),
    path('<int:org_id>/toggle-status/', views.organization_toggle_status, name='organization_toggle_status'),
]
