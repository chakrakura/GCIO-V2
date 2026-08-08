from django.urls import path

from . import views

urlpatterns = [
    path('', views.ai_integration_view, name='ai_integration'),
    path('<str:provider>/test/', views.test_connection, name='ai_test_connection'),
]
