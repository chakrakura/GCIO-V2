from django.urls import path

from . import views

urlpatterns = [
    path('', views.taxonomy_view, name='taxonomy'),
    path('<slug:tab>/', views.taxonomy_view, name='taxonomy_tab'),
    path('<slug:tab>/add/', views.taxonomy_add, name='taxonomy_add'),
    path('<slug:tab>/<int:term_id>/edit/', views.taxonomy_edit, name='taxonomy_edit'),
    path('<slug:tab>/<int:term_id>/delete/', views.taxonomy_delete, name='taxonomy_delete'),
]
