from django.core.management.base import BaseCommand
from smart_farm.models import MaizeVariety

class Command(BaseCommand):
    help = 'Add sample maize varieties for the onboarding process'

    def handle(self, *args, **options):
        # Clear existing varieties
        MaizeVariety.objects.all().delete()
        
        varieties = [
            {
                'name': 'CAMEROON HYBRID 1',
                'code': 'CMH001',
                'description': 'High-yielding hybrid variety suitable for Cameroon conditions',
                'maturity_period': 'medium',
                'expected_yield': 4.5,
                'drought_tolerance': True,
                'disease_resistance': True,
                'recommended_region': 'Northwest, Southwest, West'
            },
            {
                'name': 'EARLY GOLD',
                'code': 'EG002',
                'description': 'Early maturing variety for short rainy seasons',
                'maturity_period': 'early',
                'expected_yield': 3.8,
                'drought_tolerance': True,
                'disease_resistance': False,
                'recommended_region': 'Far North, North'
            },
            {
                'name': 'LATE HARVEST PRO',
                'code': 'LHP003',
                'description': 'Late maturing variety with excellent grain quality',
                'maturity_period': 'late',
                'expected_yield': 5.2,
                'drought_tolerance': False,
                'disease_resistance': True,
                'recommended_region': 'Center, East, Littoral'
            },
            {
                'name': 'DROUGHT MASTER',
                'code': 'DM004',
                'description': 'Specially bred for drought-prone areas',
                'maturity_period': 'medium',
                'expected_yield': 3.5,
                'drought_tolerance': True,
                'disease_resistance': False,
                'recommended_region': 'Far North, Adamawa'
            },
            {
                'name': 'ORGANIC SELECT',
                'code': 'OS005',
                'description': 'Organic-friendly variety with natural pest resistance',
                'maturity_period': 'medium',
                'expected_yield': 3.2,
                'drought_tolerance': False,
                'disease_resistance': True,
                'recommended_region': 'Northwest, Southwest'
            },
            {
                'name': 'COMMERCIAL PLUS',
                'code': 'CP006',
                'description': 'High-yield commercial variety for large farms',
                'maturity_period': 'late',
                'expected_yield': 6.0,
                'drought_tolerance': False,
                'disease_resistance': True,
                'recommended_region': 'Littoral, Center, West'
            },
            {
                'name': 'SMALLHOLDER SPECIAL',
                'code': 'SS007',
                'description': 'Perfect for smallholder farmers with limited resources',
                'maturity_period': 'early',
                'expected_yield': 2.8,
                'drought_tolerance': True,
                'disease_resistance': False,
                'recommended_region': 'All regions'
            },
            {
                'name': 'MOUNTAIN VARIETY',
                'code': 'MV008',
                'description': 'Adapted for high-altitude farming areas',
                'maturity_period': 'medium',
                'expected_yield': 3.0,
                'drought_tolerance': False,
                'disease_resistance': True,
                'recommended_region': 'Northwest, West'
            }
        ]
        
        created_count = 0
        for var_data in varieties:
            variety = MaizeVariety.objects.create(**var_data)
            created_count += 1
            self.stdout.write(f'Created: {variety.name} ({variety.code})')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} maize varieties!')
        )
        
        # Show summary
        total_varieties = MaizeVariety.objects.count()
        active_varieties = MaizeVariety.objects.filter(is_active=True).count()
        
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  Total varieties: {total_varieties}')
        self.stdout.write(f'  Active varieties: {active_varieties}')
        self.stdout.write(f'  Early maturing: {MaizeVariety.objects.filter(maturity_period="early").count()}')
        self.stdout.write(f'  Medium maturing: {MaizeVariety.objects.filter(maturity_period="medium").count()}')
        self.stdout.write(f'  Late maturing: {MaizeVariety.objects.filter(maturity_period="late").count()}')
        self.stdout.write(f'  Drought tolerant: {MaizeVariety.objects.filter(drought_tolerance=True).count()}')
        self.stdout.write(f'  Disease resistant: {MaizeVariety.objects.filter(disease_resistance=True).count()}')
