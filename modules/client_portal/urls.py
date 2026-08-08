from django.urls import path

from . import views

urlpatterns = [
    path('', views.client_home, name='client_home'),
    path('browse/', views.client_browse, name='client_browse'),
    path('publications/', views.client_publications, name='client_publications'),
    path('exclusive-reports/', views.client_exclusive_reports, name='client_exclusive_reports'),
    path('publications/<slug:slug>/', views.client_publication_series, name='client_publication_series'),
    path('saved/', views.client_saved_reports, name='client_saved_reports'),
    path('help/', views.client_help_support, name='client_help_support'),
    path('archive/', views.client_archive, name='client_archive'),
    path('<int:report_id>/save/', views.client_toggle_save, name='client_toggle_save'),
    path('<int:report_id>/', views.client_report_detail, name='client_report_detail'),
]
