import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class WeatherAPIService:
    """
    Service class to handle all WeatherAPI.com operations
    """
    
    BASE_URL = "https://api.weatherapi.com/v1"
    CACHE_TIMEOUT = 300  # 5 minutes for current weather
    FORECAST_CACHE_TIMEOUT = 1800  # 30 minutes for forecast
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('WEATHER_API_KEY')
        if not self.api_key:
            # Don't raise error during import, just log warning
            logger.warning("WeatherAPI key not found. Weather functionality will be disabled.")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL for API endpoint"""
        return f"{self.BASE_URL}/{endpoint}"
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to WeatherAPI.com
        Includes error handling and logging
        """
        if not self.api_key:
            raise Exception("WeatherAPI key not configured. Please set WEATHER_API_KEY environment variable.")
        
        try:
            url = self._build_url(endpoint)
            params['key'] = self.api_key
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'error' in data:
                logger.error(f"WeatherAPI error: {data['error']}")
                raise Exception(f"WeatherAPI error: {data['error']['message']}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"Weather API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def format_coordinates(self, latitude: float, longitude: float) -> str:
        """
        Format coordinates for API query
        Returns "Latitude,Longitude" string
        """
        return f"{latitude},{longitude}"
    
    def get_current_weather(self, latitude: float, longitude: float, aqi: bool = False) -> Dict[str, Any]:
        """
        Get current weather conditions for specific coordinates
        
        Args:
            latitude: Farm field latitude
            longitude: Farm field longitude
            aqi: Include Air Quality Index data
        
        Returns:
            Current weather data
        """
        coords = self.format_coordinates(latitude, longitude)
        cache_key = f"current_weather_{coords}_{aqi}"
        
        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        params = {
            'q': coords,
            'aqi': 'yes' if aqi else 'no'
        }
        
        data = self._make_request('current.json', params)
        
        # Cache the result
        cache.set(cache_key, data, self.CACHE_TIMEOUT)
        
        return data
    
    def get_forecast(self, latitude: float, longitude: float, days: int = 7, 
                    aqi: bool = False, alerts: bool = False, pollen: bool = False) -> Dict[str, Any]:
        """
        Get weather forecast for specific coordinates
        
        Args:
            latitude: Farm field latitude
            longitude: Farm field longitude
            days: Number of forecast days (1-14)
            aqi: Include Air Quality Index data
            alerts: Include weather alerts
            pollen: Include pollen forecast (if available in plan)
        
        Returns:
            Forecast data with daily predictions
        """
        coords = self.format_coordinates(latitude, longitude)
        cache_key = f"forecast_{coords}_{days}_{aqi}_{alerts}_{pollen}"
        
        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        params = {
            'q': coords,
            'days': min(days, 14),  # API limit is 14 days
            'aqi': 'yes' if aqi else 'no',
            'alerts': 'yes' if alerts else 'no'
        }
        
        # Add pollen parameter if requested (enterprise feature)
        if pollen:
            params['pollen'] = 'yes'
        
        data = self._make_request('forecast.json', params)
        
        # Cache the result
        cache.set(cache_key, data, self.FORECAST_CACHE_TIMEOUT)
        
        return data
    
    def get_historical_weather(self, latitude: float, longitude: float, 
                             date: datetime) -> Dict[str, Any]:
        """
        Get historical weather data for specific date
        
        Args:
            latitude: Farm field latitude
            longitude: Farm field longitude
            date: Date for historical data
        
        Returns:
            Historical weather data
        """
        coords = self.format_coordinates(latitude, longitude)
        cache_key = f"historical_{coords}_{date.strftime('%Y-%m-%d')}"
        
        # Try to get from cache first (historical data doesn't change)
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        params = {
            'q': coords,
            'dt': date.strftime('%Y-%m-%d')
        }
        
        data = self._make_request('history.json', params)
        
        # Cache historical data for longer period
        cache.set(cache_key, data, 86400)  # 24 hours
        
        return data
    
    def get_weather_alerts(self, latitude: float, longitude: float) -> List[Dict[str, Any]]:
        """
        Get weather alerts for specific location
        
        Args:
            latitude: Farm field latitude
            longitude: Farm field longitude
        
        Returns:
            List of weather alerts
        """
        forecast_data = self.get_forecast(latitude, longitude, days=1, alerts=True)
        
        alerts = []
        if 'alerts' in forecast_data.get('forecast', {}):
            alerts = forecast_data['forecast']['alerts']['alert']
        
        return alerts
    
    def extract_crop_relevant_data(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract weather data relevant for crop management
        
        Args:
            weather_data: Raw weather API response
        
        Returns:
            Processed data for agricultural use
        """
        current = weather_data.get('current', {})
        location = weather_data.get('location', {})
        
        extracted = {
            'location': {
                'name': location.get('name'),
                'region': location.get('region'),
                'country': location.get('country'),
                'lat': location.get('lat'),
                'lon': location.get('lon'),
                'localtime': location.get('localtime')
            },
            'current': {
                'temperature_c': current.get('temp_c'),
                'temperature_f': current.get('temp_f'),
                'condition': current.get('condition', {}).get('text'),
                'humidity': current.get('humidity'),
                'wind_kph': current.get('wind_kph'),
                'wind_direction': current.get('wind_dir'),
                'pressure_mb': current.get('pressure_mb'),
                'precipitation_mm': current.get('precip_mm'),
                'visibility_km': current.get('vis_km'),
                'uv_index': current.get('uv'),
                'gust_kph': current.get('gust_kph'),
                'last_updated': current.get('last_updated')
            }
        }
        
        # Add Air Quality data if available
        if 'air_quality' in current:
            extracted['air_quality'] = current['air_quality']
        
        return extracted
    
    def extract_forecast_data(self, forecast_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract forecast data relevant for crop management
        
        Args:
            forecast_data: Raw forecast API response
        
        Returns:
            Processed forecast data for agricultural use
        """
        location = forecast_data.get('location', {})
        forecast = forecast_data.get('forecast', {})
        
        extracted = {
            'location': {
                'name': location.get('name'),
                'region': location.get('region'),
                'country': location.get('country'),
                'lat': location.get('lat'),
                'lon': location.get('lon')
            },
            'current': forecast.get('current', {}),
            'forecast_days': []
        }
        
        # Process daily forecast data
        for day_data in forecast.get('forecastday', []):
            day = day_data.get('day', {})
            astro = day_data.get('astro', {})
            
            day_extracted = {
                'date': day_data.get('date'),
                'max_temp_c': day.get('maxtemp_c'),
                'min_temp_c': day.get('mintemp_c'),
                'avg_temp_c': day.get('avgtemp_c'),
                'max_wind_kph': day.get('maxwind_kph'),
                'total_precip_mm': day.get('totalprecip_mm'),
                'avg_visibility_km': day.get('avgvis_km'),
                'avg_humidity': day.get('avghumidity'),
                'daily_chance_of_rain': day.get('daily_chance_of_rain'),
                'daily_chance_of_snow': day.get('daily_chance_of_snow'),
                'condition': day.get('condition', {}).get('text'),
                'uv_index': day.get('uv'),
                'sunrise': astro.get('sunrise'),
                'sunset': astro.get('sunset'),
                'moonrise': astro.get('moonrise'),
                'moonset': astro.get('moonset'),
                'moon_phase': astro.get('moon_phase'),
                'moon_illumination': astro.get('moon_illumination')
            }
            
            # Add hourly data if needed
            if 'hour' in day_data:
                day_extracted['hourly'] = day_data['hour']
            
            # Add Air Quality if available
            if 'air_quality' in day:
                day_extracted['air_quality'] = day['air_quality']
            
            extracted['forecast_days'].append(day_extracted)
        
        # Add alerts if available
        if 'alerts' in forecast:
            extracted['alerts'] = forecast['alerts']
        
        return extracted


# Create singleton instance when needed
def get_weather_service():
    """Get weather service instance"""
    return WeatherAPIService()
