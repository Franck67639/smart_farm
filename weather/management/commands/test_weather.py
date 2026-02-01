from django.core.management.base import BaseCommand
from weather.services import WeatherAPIService

class Command(BaseCommand):
    help = 'Test weather API integration'

    def handle(self, *args, **options):
        service = WeatherAPIService()
        
        try:
            # Test with Cameroon coordinates
            data = service.get_current_weather(3.8480, 11.5021)
            
            self.stdout.write(self.style.SUCCESS('✅ Weather API working successfully!'))
            self.stdout.write(f"📍 Location: {data['location']['name']}, {data['location']['country']}")
            self.stdout.write(f"🌡️  Current temp: {data['current']['temp_c']}°C")
            self.stdout.write(f"☁️  Condition: {data['current']['condition']['text']}")
            self.stdout.write(f"💧 Humidity: {data['current']['humidity']}%")
            self.stdout.write(f"💨 Wind: {data['current']['wind_kph']} km/h")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
