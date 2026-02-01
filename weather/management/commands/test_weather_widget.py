from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from smart_farm.models import FarmDetails
from weather.services import WeatherAPIService
from weather.models import WeatherForecast, WeatherAlert
from smart_farm.models import WeatherData
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Test weather widget functionality'

    def handle(self, *args, **options):
        # Get test user and farm
        try:
            user = User.objects.get(username='testuser')
            farm = FarmDetails.objects.get(user=user)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Test user not found'))
            return
        except FarmDetails.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Test farm not found'))
            return

        self.stdout.write(f'📍 Testing weather for: {farm.farm_name}')
        self.stdout.write(f'🆔 Farm ID: {farm.id}')
        
        # Parse GPS coordinates
        try:
            if farm.gps_coordinates:
                lat_str, lon_str = farm.gps_coordinates.split(',')
                latitude = float(lat_str.strip())
                longitude = float(lon_str.strip())
            else:
                # Default to Cameroon coordinates
                latitude = 3.8480
                longitude = 11.5021
        except:
            latitude = 3.8480
            longitude = 11.5021

        self.stdout.write(f'🌍 Coordinates: {latitude}, {longitude}')

        # Test weather service
        service = WeatherAPIService()
        
        try:
            # Get current weather
            current_data = service.get_current_weather(latitude, longitude)
            self.stdout.write(self.style.SUCCESS('✅ Current weather fetched successfully'))
            
            # Create weather data record
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
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'🌡️  {action} weather record: {weather_record}')
            
            # Get forecast
            forecast_data = service.get_forecast(latitude, longitude, days=3)
            self.stdout.write(self.style.SUCCESS('✅ Forecast fetched successfully'))
            
            processed_forecast = service.extract_forecast_data(forecast_data)
            
            for day_data in processed_forecast['forecast_days']:
                forecast, created = WeatherForecast.objects.update_or_create(
                    farm=farm,
                    forecast_date=timezone.datetime.strptime(day_data['date'], '%Y-%m-%d').date(),
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
                        'raw_data': day_data
                    }
                )
                action = 'Created' if created else 'Updated'
                self.stdout.write(f'📅 {action} forecast for {day_data["date"]}: {day_data["max_temp_c"]}°C/{day_data["min_temp_c"]}°C')
            
            self.stdout.write(self.style.SUCCESS('🎉 Weather widget test completed successfully!'))
            self.stdout.write(f'🌐 Visit http://localhost:8000/ and login with testuser/testpass123 to see the weather widget')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
