from django.urls import path

from . import views

urlpatterns = [
    path('', views.user_list, name='user_list'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/password/', views.profile_password_view, name='profile_password'),
    path('add/', views.user_add, name='user_add'),
    path('<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('<int:user_id>/reset-password/', views.user_reset_password, name='user_reset_password'),
    path('<int:user_id>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),
    path('<int:user_id>/impersonate/', views.user_impersonate, name='user_impersonate'),
    path('stop-impersonating/', views.stop_impersonating, name='stop_impersonating'),
    path('admin-actions/', views.admin_actions_view, name='admin_actions'),
]
