from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q
from django.core.paginator import Paginator

from .models import WeatherForecast, HistoricalWeather, WeatherAlert
from .services import WeatherAPIService
from smart_farm.models import FarmDetails, WeatherData
import logging

logger = logging.getLogger(__name__)


@login_required
@require_GET
def weather_dashboard(request):
    """
    Main weather dashboard view
    """
    user = request.user
    farm_details = FarmDetails.objects.filter(user=user)
    
    # Get current weather for all fields
    current_weather = {}
    forecasts = {}
    alerts = {}
    
    for farm in farm_details:
        # Get latest current weather
        latest_weather = WeatherData.objects.filter(farm=farm).first()
        if latest_weather:
            current_weather[farm.id] = latest_weather
        
        # Get upcoming forecasts (next 7 days)
        farm_forecasts = WeatherForecast.objects.filter(
            farm=farm,
            forecast_date__gte=timezone.now().date()
        ).order_by('forecast_date')[:7]
        forecasts[farm.id] = farm_forecasts
        
        # Get active alerts
        farm_alerts = WeatherAlert.objects.filter(
            farm=farm,
            user=user,
            is_active=True,
            expires__gte=timezone.now()
        ).order_by('-created_at')
        alerts[farm.id] = farm_alerts
    
    context = {
        'farm_details_list': farm_details,
        'current_weather': current_weather,
        'forecasts': forecasts,
        'alerts': alerts,
        'page_title': 'Weather Dashboard'
    }
    
    return render(request, 'weather/dashboard.html', context)


@login_required
@require_GET
def update_weather_data(request, field_id):
    """
    Update weather data for a specific field
    """
    farm = get_object_or_404(FarmDetails, id=field_id, user=request.user)
    
    try:
        service = WeatherAPIService()
        
        # Get current weather - use default coordinates if not available
        latitude = getattr(farm, 'latitude', None) or 3.8480  # Default Cameroon coordinates
        longitude = getattr(farm, 'longitude', None) or 11.5021
        
        current_data = service.get_current_weather(
            latitude, 
            longitude, 
            aqi=True
        )
        
        # Save current weather
        processed_current = service.extract_crop_relevant_data(current_data)
        weather_record, created = WeatherData.objects.update_or_create(
            farm=farm,
            date=timezone.now().date(),
            defaults={
                'temperature_min': processed_current['current']['temperature_c'] - 2,
                'temperature_max': processed_current['current']['temperature_c'] + 2,
                'temperature_avg': processed_current['current']['temperature_c'],
                'humidity': processed_current['current']['humidity'],
                'rainfall': processed_current['current'].get('precipitation_mm', 0),
                'wind_speed': processed_current['current']['wind_kph'],
                'weather_condition': processed_current['current']['condition'],
                'data_source': 'weatherapi'
            }
        )
        
        # Get forecast data
        forecast_data = service.get_forecast(
            latitude,
            longitude,
            days=7,
            aqi=True,
            alerts=True,
            pollen=True
        )
        
        # Save forecast data
        processed_forecast = service.extract_forecast_data(forecast_data)
        for day_data in processed_forecast['forecast_days']:
            WeatherForecast.objects.update_or_create(
                farm=farm,
                forecast_date=datetime.strptime(day_data['date'], '%Y-%m-%d').date(),
                defaults={
                    'max_temp_c': day_data['max_temp_c'],
                    'min_temp_c': day_data['min_temp_c'],
                    'avg_temp_c': day_data['avg_temp_c'],
                    'max_wind_kph': day_data['max_wind_kph'],
                    'total_precip_mm': day_data['total_precip_mm'],
                    'avg_visibility_km': day_data['avg_visibility_km'],
                    'avg_humidity': day_data['avg_humidity'],
                    'daily_chance_of_rain': day_data.get('daily_chance_of_rain', 0),
                    'daily_chance_of_snow': day_data.get('daily_chance_of_snow', 0),
                    'condition': day_data['condition'],
                    'uv_index': day_data.get('uv_index'),
                    'sunrise': None,
                    'sunset': None,
                    'moon_phase': day_data.get('moon_phase'),
                    'moon_illumination': day_data.get('moon_illumination'),
                    'air_quality_data': day_data.get('air_quality'),
                    'raw_data': day_data
                }
            )
        
        # Process alerts
        if 'alerts' in processed_forecast:
            for alert_data in processed_forecast['alerts']['alert']:
                WeatherAlert.objects.update_or_create(
                    farm=farm,
                    user=request.user,
                    headline=alert_data['headline'],
                    defaults={
                        'severity': alert_data['severity'],
                        'urgency': alert_data['urgency'],
                        'areas': alert_data['areas'],
                        'category': alert_data['category'],
                        'certainty': alert_data['certainty'],
                        'event': alert_data['event'],
                        'note': alert_data.get('note', ''),
                        'effective': datetime.strptime(alert_data['effective'], '%Y-%m-%dT%H:%M:%S%z'),
                        'expires': datetime.strptime(alert_data['expires'], '%Y-%m-%dT%H:%M:%S%z'),
                        'description': alert_data['desc'],
                        'instruction': alert_data.get('instruction', ''),
                        'raw_data': alert_data
                    }
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Weather data updated successfully',
            'weather': {
                'temperature': weather_record.temperature_avg,
                'condition': weather_record.weather_condition,
                'humidity': weather_record.humidity,
                'wind_speed': weather_record.wind_speed,
                'precipitation': weather_record.rainfall,
                'date': weather_record.date.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating weather data for farm {field_id}: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_GET
def get_historical_weather(request, field_id):
    """
    Get historical weather data for a field
    """
    farm = get_object_or_404(FarmDetails, id=field_id, user=request.user)
    
    # Get query parameters
    days = int(request.GET.get('days', 30))
    start_date = timezone.now().date() - timedelta(days=days)
    
    historical_data = HistoricalWeather.objects.filter(
        farm=farm,
        date__gte=start_date
    ).order_by('date')
    
    data = []
    for record in historical_data:
        data.append({
            'date': record.date.strftime('%Y-%m-%d'),
            'max_temp': record.max_temp_c,
            'min_temp': record.min_temp_c,
            'avg_temp': record.avg_temp_c,
            'precipitation': record.total_precip_mm,
            'humidity': record.avg_humidity,
            'condition': record.condition
        })
    
    return JsonResponse({
        'success': True,
        'data': data,
        'field_name': farm.farm_name
    })


@login_required
@require_GET
def get_weather_alerts(request):
    """
    Get active weather alerts for user's fields
    """
    user = request.user
    alerts = WeatherAlert.objects.filter(
        user=user,
        is_active=True,
        expires__gte=timezone.now()
    ).order_by('-created_at')
    
    alert_data = []
    for alert in alerts:
        alert_data.append({
            'id': alert.id,
            'field_name': alert.farm.farm_name,
            'headline': alert.headline,
            'severity': alert.severity,
            'event': alert.event,
            'description': alert.description,
            'instruction': alert.instruction,
            'effective': alert.effective.strftime('%Y-%m-%d %H:%M'),
            'expires': alert.expires.strftime('%Y-%m-%d %H:%M'),
            'acknowledged': alert.acknowledged
        })
    
    return JsonResponse({
        'success': True,
        'alerts': alert_data
    })


@login_required
@require_POST
def acknowledge_alert(request, alert_id):
    """
    Acknowledge a weather alert
    """
    alert = get_object_or_404(WeatherAlert, id=alert_id, user=request.user)
    
    alert.acknowledged = True
    alert.acknowledged_at = timezone.now()
    alert.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Alert acknowledged'
    })


@login_required
@require_GET
def weather_widget(request, field_id=None):
    """
    Render weather widget for dashboard
    """
    if field_id:
        farm = get_object_or_404(FarmDetails, id=field_id, user=request.user)
        farms = [farm]
    else:
        # Get user's farm details
        farms = FarmDetails.objects.filter(user=request.user)[:1]
        farm = farms.first() if farms else None
    
    if not farm:
        return render(request, 'weather/widget_empty.html')
    
    # Get latest weather data
    weather = WeatherData.objects.filter(farm=farm).first()
    
    context = {
        'field': farm,
        'weather': weather,
        'alerts_count': WeatherAlert.objects.filter(
            farm=farm,
            user=request.user,
            is_active=True,
            expires__gte=timezone.now(),
            acknowledged=False
        ).count()
    }
    
    return render(request, 'weather/widget.html', context)


@login_required
@require_GET
def forecast_calendar(request, field_id):
    """
    Get forecast data in calendar format
    """
    farm = get_object_or_404(FarmDetails, id=field_id, user=request.user)
    
    # Get 30-day forecast
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=30)
    
    forecasts = WeatherForecast.objects.filter(
        farm=farm,
        forecast_date__gte=start_date,
        forecast_date__lte=end_date
    ).order_by('forecast_date')
    
    calendar_data = {}
    for forecast in forecasts:
        calendar_data[forecast.forecast_date.strftime('%Y-%m-%d')] = {
            'max_temp': forecast.max_temp_c,
            'min_temp': forecast.min_temp_c,
            'condition': forecast.condition,
            'precipitation': forecast.total_precip_mm,
            'rain_chance': forecast.daily_chance_of_rain
        }
    
    return JsonResponse({
        'success': True,
        'calendar_data': calendar_data,
        'field_name': farm.farm_name
    })


@login_required
@require_GET
def weather_analytics(request, field_id):
    """
    Get weather analytics for a field
    """
    farm = get_object_or_404(FarmDetails, id=field_id, user=request.user)
    
    # Get historical data for analysis
    historical = HistoricalWeather.objects.filter(
        farm=farm,
        date__gte=timezone.now().date() - timedelta(days=365)
    ).order_by('date')
    
    # Calculate analytics
    if historical.exists():
        avg_temp = sum(record.avg_temp_c for record in historical) / len(historical)
        total_precip = sum(record.total_precip_mm for record in historical)
        rainy_days = len([r for r in historical if r.total_precip_mm > 0])
        
        # Temperature trends
        temps = [record.avg_temp_c for record in historical]
        temp_trend = 'increasing' if temps[-10:] and sum(temps[-10:]) / 10 > sum(temps[:10]) / 10 else 'decreasing'
        
        analytics = {
            'avg_temperature': round(avg_temp, 1),
            'total_precipitation': round(total_precip, 1),
            'rainy_days': rainy_days,
            'rainy_days_percentage': round((rainy_days / len(historical)) * 100, 1),
            'temperature_trend': temp_trend,
            'data_points': len(historical)
        }
    else:
        analytics = None
    
    return JsonResponse({
        'success': True,
        'analytics': analytics,
        'field_name': farm.farm_name
    })
