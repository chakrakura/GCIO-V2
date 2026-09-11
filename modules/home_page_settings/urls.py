from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_page_settings_view, name='home_page_settings'),
    path('preview/', views.client_home_preview, name='client_home_preview'),
    path('preview/<int:report_id>/', views.client_home_preview_report, name='client_home_preview_report'),
]
