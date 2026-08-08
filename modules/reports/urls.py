from django.urls import path

from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('add/', views.report_add, name='report_add'),
    path('generate-ai/', views.generate_ai_draft, name='report_generate_ai'),
    path('<int:report_id>/edit/', views.report_edit, name='report_edit'),
    path('<int:report_id>/delete/', views.report_delete, name='report_delete'),
]
