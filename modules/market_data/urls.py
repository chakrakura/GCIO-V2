from django.urls import path

from . import views

urlpatterns = [
    path('', views.market_data_view, name='market_data'),
    path('refresh/', views.market_data_refresh_all, name='market_data_refresh_all'),
    path('<int:instrument_id>/refresh/', views.market_data_refresh_one, name='market_data_refresh_one'),
    path('<int:instrument_id>/toggle/<str:field>/', views.market_data_toggle, name='market_data_toggle'),
]
