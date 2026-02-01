from django.db import models
from django.contrib.auth import get_user_model
from smart_farm.models import FarmDetails, WeatherData as BaseWeatherData
import json

User = get_user_model()


class WeatherForecast(models.Model):
    """
    Store weather forecast data for farm fields
    """
    farm = models.ForeignKey(FarmDetails, on_delete=models.CASCADE, related_name='weather_forecasts')
    forecast_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Daily forecast data
    max_temp_c = models.FloatField()
    min_temp_c = models.FloatField()
    avg_temp_c = models.FloatField()
    max_wind_kph = models.FloatField()
    total_precip_mm = models.FloatField()
    avg_visibility_km = models.FloatField()
    avg_humidity = models.IntegerField()
    daily_chance_of_rain = models.IntegerField()
    daily_chance_of_snow = models.IntegerField()
    condition = models.CharField(max_length=200)
    uv_index = models.FloatField(null=True, blank=True)
    
    # Astronomical data
    sunrise = models.TimeField(null=True, blank=True)
    sunset = models.TimeField(null=True, blank=True)
    moon_phase = models.CharField(max_length=50, null=True, blank=True)
    moon_illumination = models.CharField(max_length=50, null=True, blank=True)
    
    # Air Quality (if available)
    air_quality_data = models.JSONField(null=True, blank=True)
    
    # Raw API response
    raw_data = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-forecast_date']
        unique_together = ['farm', 'forecast_date']
        indexes = [
            models.Index(fields=['farm', 'forecast_date']),
            models.Index(fields=['forecast_date']),
        ]
    
    def __str__(self):
        return f"Forecast for {self.farm.farm_name} on {self.forecast_date}"


class HistoricalWeather(models.Model):
    """
    Store historical weather data for analysis and model training
    """
    farm = models.ForeignKey(FarmDetails, on_delete=models.CASCADE, related_name='historical_weather')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Historical conditions
    max_temp_c = models.FloatField()
    min_temp_c = models.FloatField()
    avg_temp_c = models.FloatField()
    max_wind_kph = models.FloatField()
    total_precip_mm = models.FloatField()
    avg_visibility_km = models.FloatField()
    avg_humidity = models.IntegerField()
    condition = models.CharField(max_length=200)
    
    # Hourly data (stored as JSON)
    hourly_data = models.JSONField(default=dict)
    
    # Raw API response
    raw_data = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['farm', 'date']
        indexes = [
            models.Index(fields=['farm', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Historical weather for {self.farm.farm_name} on {self.date}"


class WeatherAlert(models.Model):
    """
    Store weather alerts for farm fields
    """
    farm = models.ForeignKey(FarmDetails, on_delete=models.CASCADE, related_name='weather_alerts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weather_alerts')
    
    # Alert details from API
    headline = models.CharField(max_length=500)
    severity = models.CharField(max_length=50)
    urgency = models.CharField(max_length=50)
    areas = models.CharField(max_length=500)
    category = models.CharField(max_length=100)
    certainty = models.CharField(max_length=50)
    event = models.CharField(max_length=200)
    note = models.TextField(blank=True)
    effective = models.DateTimeField()
    expires = models.DateTimeField()
    description = models.TextField()
    instruction = models.TextField(blank=True)
    
    # System fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Raw API response
    raw_data = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['farm', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['severity']),
            models.Index(fields=['expires']),
        ]
    
    def __str__(self):
        return f"{self.severity} {self.event} for {self.farm.farm_name}"


class WeatherCache(models.Model):
    """
    Cache for weather API responses to reduce API calls
    """
    cache_key = models.CharField(max_length=255, unique=True)
    data = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Cache: {self.cache_key}"


class WeatherAPIUsage(models.Model):
    """
    Track API usage for monitoring and rate limiting
    """
    date = models.DateField()
    endpoint = models.CharField(max_length=50)
    requests_made = models.IntegerField(default=0)
    successful_requests = models.IntegerField(default=0)
    failed_requests = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['date', 'endpoint']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.endpoint} usage on {self.date}: {self.requests_made} requests"
