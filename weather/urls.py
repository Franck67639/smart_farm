from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    # Main weather views
    path('', views.weather_dashboard, name='dashboard'),
    
    # API endpoints
    path('api/update/<uuid:field_id>/', views.update_weather_data, name='update_weather'),
    path('api/historical/<uuid:field_id>/', views.get_historical_weather, name='historical'),
    path('api/alerts/', views.get_weather_alerts, name='alerts'),
    path('api/alert/<int:alert_id>/acknowledge/', views.acknowledge_alert, name='acknowledge_alert'),
    
    # Widget and components
    path('widget/<uuid:field_id>/', views.weather_widget, name='widget'),
    path('widget/', views.weather_widget, name='widget_default'),
    path('calendar/<uuid:field_id>/', views.forecast_calendar, name='calendar'),
    path('analytics/<uuid:field_id>/', views.weather_analytics, name='analytics'),
]
