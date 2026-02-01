from django.core.management.base import BaseCommand
from smart_farm.models import MaizeVariety

class Command(BaseCommand):
    help = 'Create initial maize varieties for SmartFarm'

    def handle(self, *args, **options):
        varieties = [
            {
                'name': 'CAMEROON HYBRID 1',
                'code': 'CM_H1',
                'description': 'High-yielding hybrid variety developed for Cameroon climate conditions',
                'image_url': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=200&h=200&fit=crop&crop=center&auto=format',
                'characteristics': {
                    'maturity_days': 90,
                    'yield_potential': '8-10 tons/ha',
                    'drought_tolerance': 'High',
                    'disease_resistance': 'Medium',
                    'plant_height': '200-250 cm',
                    'kernel_color': 'Yellow',
                    'recommended_density': '53,000 plants/ha'
                }
            },
            {
                'name': 'WHITE GOLD',
                'code': 'WG_001',
                'description': 'Premium white maize variety with excellent grain quality',
                'image_url': 'https://images.unsplash.com/photo-1578946373699-a5c8142b8c1b?w=200&h=200&fit=crop&crop=center&auto=format',
                'characteristics': {
                    'maturity_days': 95,
                    'yield_potential': '6-8 tons/ha',
                    'drought_tolerance': 'Medium',
                    'disease_resistance': 'High',
                    'plant_height': '180-220 cm',
                    'kernel_color': 'White',
                    'recommended_density': '50,000 plants/ha'
                }
            },
            {
                'name': 'YELLOW DENT',
                'code': 'YD_002',
                'description': 'Traditional yellow dent corn suitable for animal feed and industrial use',
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=200&h=200&fit=crop&crop=center&auto=format',
                'characteristics': {
                    'maturity_days': 100,
                    'yield_potential': '7-9 tons/ha',
                    'drought_tolerance': 'Medium',
                    'disease_resistance': 'Medium',
                    'plant_height': '220-280 cm',
                    'kernel_color': 'Yellow',
                    'recommended_density': '48,000 plants/ha'
                }
            },
            {
                'name': 'FLINT CORN',
                'code': 'FC_003',
                'description': 'Hard kernel variety excellent for flour production',
                'image_url': 'https://images.unsplash.com/photo-1602661424532-74d44ddc4d9a?w=200&h=200&fit=crop&crop=center&auto=format',
                'characteristics': {
                    'maturity_days': 105,
                    'yield_potential': '5-7 tons/ha',
                    'drought_tolerance': 'High',
                    'disease_resistance': 'High',
                    'plant_height': '150-200 cm',
                    'kernel_color': 'Orange/Red',
                    'recommended_density': '55,000 plants/ha'
                }
            },
            {
                'name': 'SWEET CORN',
                'code': 'SC_004',
                'description': 'High sugar content variety for fresh market consumption',
                'image_url': 'https://images.unsplash.com/photo-1598300041222-3bb90d3e4375?w=200&h=200&fit=crop&crop=center&auto=format',
                'characteristics': {
                    'maturity_days': 70,
                    'yield_potential': '4-6 tons/ha',
                    'drought_tolerance': 'Low',
                    'disease_resistance': 'Medium',
                    'plant_height': '150-200 cm',
                    'kernel_color': 'Yellow/White',
                    'recommended_density': '45,000 plants/ha'
                }
            },
            {
                'name': 'POPCORN',
                'code': 'PC_005',
                'description': 'Specialty variety for popcorn production',
                'image_url': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=200&h=200&fit=crop&crop=center&auto=format',
                'characteristics': {
                    'maturity_days': 110,
                    'yield_potential': '3-5 tons/ha',
                    'drought_tolerance': 'Medium',
                    'disease_resistance': 'High',
                    'plant_height': '120-180 cm',
                    'kernel_color': 'Yellow/White',
                    'recommended_density': '60,000 plants/ha'
                }
            },
            {
                'name': 'BLUE CORN',
                'code': 'BC_006',
                'description': 'Heirloom variety with high antioxidant content',
                'image_url': 'https://images.unsplash.com/photo-1598300041222-3bb90d3e4375?w=200&h=200&fit=crop&crop=center&auto=format',
                'characteristics': {
                    'maturity_days': 115,
                    'yield_potential': '4-6 tons/ha',
                    'drought_tolerance': 'High',
                    'disease_resistance': 'Medium',
                    'plant_height': '180-220 cm',
                    'kernel_color': 'Blue',
                    'recommended_density': '52,000 plants/ha'
                }
            },
            {
                'name': 'RED CORN',
                'code': 'RC_007',
                'description': 'Specialty red variety for traditional and niche markets',
                'image_url': 'https://images.unsplash.com/photo-1578946373699-a5c8142b8c1b?w=200&h=200&fit=crop&crop=center&auto=format',
                'characteristics': {
                    'maturity_days': 100,
                    'yield_potential': '5-7 tons/ha',
                    'drought_tolerance': 'Medium',
                    'disease_resistance': 'High',
                    'plant_height': '200-250 cm',
                    'kernel_color': 'Red',
                    'recommended_density': '51,000 plants/ha'
                }
            }
        ]

        created_count = 0
        for variety_data in varieties:
            variety, created = MaizeVariety.objects.get_or_create(
                code=variety_data['code'],
                defaults=variety_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created maize variety: {variety.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Maize variety already exists: {variety.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new maize varieties')
        )
