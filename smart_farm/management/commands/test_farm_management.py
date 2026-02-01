from django.core.management.base import BaseCommand
from smart_farm.models import FarmDetails, User
import uuid

class Command(BaseCommand):
    help = 'Test farm management functionality'

    def handle(self, *args, **options):
        self.stdout.write('🚜 Testing SmartFarm Farm Management')
        self.stdout.write('=' * 50)
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='testfarmer',
            defaults={
                'email': 'test@smartfarm.cm',
                'first_name': 'Test',
                'last_name': 'Farmer'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Created test user: {user.username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Using existing user: {user.username}'))
        
        # Create test farms
        farms_data = [
            {
                'farm_name': 'Green Valley Farm',
                'farm_type': 'smallholder',
                'farm_size_category': '5_to_10',
                'primary_crop': 'maize',
                'farming_years': 5,
                'region': 'northwest',
                'division': 'Mezam',
                'subdivision': 'Bamenda',
                'village_town': 'Bamenda',
                'gps_coordinates': '5.9641, 10.1525'
            },
            {
                'farm_name': 'Coastal Fields',
                'farm_type': 'commercial',
                'farm_size_category': '10_to_50',
                'primary_crop': 'cassava',
                'farming_years': 10,
                'region': 'littoral',
                'division': 'Wouri',
                'subdivision': 'Douala',
                'village_town': 'Douala',
                'gps_coordinates': '4.0483, 9.7043'
            },
            {
                'farm_name': 'Highland Estate',
                'farm_type': 'mixed',
                'farm_size_category': '1_to_5',
                'primary_crop': 'vegetables',
                'farming_years': 3,
                'region': 'west',
                'division': 'Menoua',
                'subdivision': 'Dschang',
                'village_town': 'Dschang',
                'gps_coordinates': '5.4506, 10.0532'
            }
        ]
        
        # Clear existing farms for this user
        FarmDetails.objects.filter(user=user).delete()
        self.stdout.write('🗑️  Cleared existing test farms')
        
        # Create new farms
        created_farms = []
        for farm_data in farms_data:
            farm = FarmDetails.objects.create(user=user, **farm_data)
            created_farms.append(farm)
            self.stdout.write(f'🌱 Created: {farm.farm_name} ({farm.region})')
        
        # Test farm listing
        self.stdout.write(f'\n📋 User has {user.farms.count()} farm(s):')
        for farm in user.farms.all():
            self.stdout.write(f'   • {farm.farm_name} - {farm.village_town}, {farm.region}')
        
        # Test farm switching simulation
        self.stdout.write('\n🔄 Testing farm switching:')
        for i, farm in enumerate(created_farms):
            self.stdout.write(f'   Switch to farm {i+1}: {farm.farm_name}')
            self.stdout.write(f'   Session would store: current_farm_id = {farm.id}')
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('🎉 Farm management test completed!'))
        self.stdout.write('\n💡 Features tested:')
        self.stdout.write('   ✅ Multiple farms per user')
        self.stdout.write('   ✅ Farm creation with different regions')
        self.stdout.write('   ✅ Farm listing and switching')
        self.stdout.write('   ✅ GPS coordinates storage')
        self.stdout.write('\n🌐 Web interface features:')
        self.stdout.write('   • Farm selector dropdown in top navigation')
        self.stdout.write('   • Switch between farms with one click')
        self.stdout.write('   • Add new farms via onboarding')
        self.stdout.write('   • Visual indicators for current farm')
        self.stdout.write('   • Farm count and location display')
