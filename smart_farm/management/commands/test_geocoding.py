from django.core.management.base import BaseCommand
from smart_farm.services import geocoding_service

class Command(BaseCommand):
    help = 'Test geocoding functionality'

    def handle(self, *args, **options):
        self.stdout.write('🌍 Testing SmartFarm Geocoding Service')
        self.stdout.write('=' * 50)
        
        # Test coordinates for major Cameroon cities
        test_locations = [
            {'name': 'Yaoundé', 'lat': 3.8480, 'lng': 11.5021},
            {'name': 'Douala', 'lat': 4.0483, 'lng': 9.7043},
            {'name': 'Bamenda', 'lat': 5.9641, 'lng': 10.1525},
            {'name': 'Buea', 'lat': 4.1517, 'lng': 9.2391},
            {'name': 'Garoua', 'lat': 9.3045, 'lng': 13.3938},
        ]
        
        for location in test_locations:
            self.stdout.write(f'\n📍 Testing {location["name"]} ({location["lat"]}, {location["lng"]})')
            
            result = geocoding_service.reverse_geocode(location['lat'], location['lng'])
            
            if result:
                self.stdout.write(self.style.SUCCESS('✅ Success!'))
                self.stdout.write(f'   Village/Town: {result["village_town"]}')
                self.stdout.write(f'   Division: {result["division"]}')
                self.stdout.write(f'   Region: {result["region"]}')
                self.stdout.write(f'   Country: {result["country"]}')
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to geocode'))
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('🎉 Geocoding test completed!'))
        self.stdout.write('\n💡 Usage in onboarding:')
        self.stdout.write('   1. Enter GPS coordinates manually or use "Detect My Location"')
        self.stdout.write('   2. System automatically populates: Village/Town, Division, Region')
        self.stdout.write('   3. Form fields are filled with accurate location data')
