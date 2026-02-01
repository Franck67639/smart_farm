from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class User(AbstractUser):
    """Extended User model for SmartFarm"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    full_name = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']
    
    def __str__(self):
        return self.email

class MaizeVariety(models.Model):
    """Maize varieties managed by admin for user selection during onboarding"""
    
    MATURITY_CHOICES = [
        ('early', 'Early (60-80 days)'),
        ('medium', 'Medium (80-100 days)'),
        ('late', 'Late (100-120 days)'),
    ]
    
    name = models.CharField(max_length=100, help_text="Name of the maize variety")
    code = models.CharField(max_length=50, unique=True, help_text="Unique code for the variety")
    description = models.TextField(blank=True, help_text="Brief description of the variety")
    maturity_period = models.CharField(max_length=20, choices=MATURITY_CHOICES, help_text="Maturity period")
    expected_yield = models.FloatField(help_text="Expected yield in tons per hectare")
    drought_tolerance = models.BooleanField(default=False, help_text="Drought tolerant variety")
    disease_resistance = models.BooleanField(default=False, help_text="Disease resistant variety")
    recommended_region = models.CharField(max_length=100, blank=True, help_text="Recommended regions for planting")
    image = models.ImageField(upload_to='maize_varieties/', blank=True, null=True, help_text="Image of the variety")
    is_active = models.BooleanField(default=True, help_text="Whether this variety is available for selection")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Maize Variety"
        verbose_name_plural = "Maize Varieties"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class FarmDetails(models.Model):
    """Comprehensive farm details collected during onboarding"""
    
    # Farm Basic Information
    FARM_TYPE_CHOICES = [
        ('smallholder', 'Smallholder'),
        ('commercial', 'Commercial'),
        ('subsistence', 'Subsistence'),
        ('mixed', 'Mixed'),
    ]
    
    FARM_SIZE_CHOICES = [
        ('less_than_1', 'Less than 1 hectare'),
        ('1_to_5', '1-5 hectares'),
        ('5_to_10', '5-10 hectares'),
        ('10_to_50', '10-50 hectares'),
        ('more_than_50', 'More than 50 hectares'),
    ]
    
    PRIMARY_CROP_CHOICES = [
        ('maize', 'Maize'),
        ('cassava', 'Cassava'),
        ('beans', 'Beans'),
        ('rice', 'Rice'),
        ('vegetables', 'Vegetables'),
        ('mixed', 'Mixed Crops'),
        ('other', 'Other'),
    ]
    
    # Location Information
    REGION_CHOICES = [
        ('northwest', 'Northwest'),
        ('southwest', 'Southwest'),
        ('west', 'West'),
        ('littoral', 'Littoral'),
        ('center', 'Center'),
        ('east', 'East'),
        ('adamawa', 'Adamawa'),
        ('far_north', 'Far North'),
        ('north', 'North'),
        ('south', 'South'),
    ]
    
    # Soil Information
    SOIL_TYPE_CHOICES = [
        ('sandy', 'Sandy'),
        ('clay', 'Clay'),
        ('loamy', 'Loamy'),
        ('silty', 'Silty'),
        ('peaty', 'Peaty'),
        ('chalky', 'Chalky'),
        ('unknown', 'Unknown'),
    ]
    
    FERTILITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High'),
        ('unknown', 'Unknown'),
    ]
    
    # Water/Irrigation Information
    WATER_SOURCE_CHOICES = [
        ('rain_fed', 'Rain-fed only'),
        ('well', 'Well'),
        ('borehole', 'Borehole'),
        ('river', 'River/Stream'),
        ('lake', 'Lake'),
        ('municipal', 'Municipal supply'),
        ('mixed', 'Mixed sources'),
    ]
    
    IRRIGATION_CHOICES = [
        ('none', 'No irrigation'),
        ('drip', 'Drip irrigation'),
        ('sprinkler', 'Sprinkler'),
        ('flood', 'Flood irrigation'),
        ('manual', 'Manual watering'),
        ('other', 'Other'),
    ]
    
    # Experience Level
    EXPERIENCE_CHOICES = [
        ('beginner', 'Beginner - Less than 2 years'),
        ('intermediate', 'Intermediate - 2-5 years'),
        ('advanced', 'Advanced - 5-10 years'),
        ('expert', 'Expert - More than 10 years'),
    ]
    
    # Farm Equipment
    EQUIPMENT_CHOICES = [
        ('tractor', 'Tractor'),
        ('plow', 'Plow'),
        ('harrow', 'Harrow'),
        ('planter', 'Planter/Seeder'),
        ('harvester', 'Harvester'),
        ('sprayer', 'Sprayer'),
        ('irrigation_pump', 'Irrigation pump'),
        ('thresher', 'Thresher'),
        ('none', 'No equipment'),
        ('other', 'Other'),
    ]
    
    # Main Model Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
    
    # Step 1: Basic Farm Information
    farm_name = models.CharField(max_length=200, help_text="Name of your farm")
    farm_type = models.CharField(max_length=20, choices=FARM_TYPE_CHOICES, help_text="Type of farming operation")
    farm_size_category = models.CharField(max_length=20, choices=FARM_SIZE_CHOICES, help_text="Size of your farm")
    primary_crop = models.CharField(max_length=20, choices=PRIMARY_CROP_CHOICES, help_text="Main crop grown")
    farming_years = models.IntegerField(help_text="How many years have you been farming?")
    selected_maize_variety = models.ForeignKey(MaizeVariety, on_delete=models.SET_NULL, null=True, blank=True, help_text="Selected maize variety")
    
    # Step 2: Location Information
    region = models.CharField(max_length=20, choices=REGION_CHOICES, help_text="Region where farm is located")
    division = models.CharField(max_length=100, help_text="Division/Department")
    subdivision = models.CharField(max_length=100, help_text="Subdivision/District")
    village_town = models.CharField(max_length=100, help_text="Village or town name")
    gps_coordinates = models.CharField(max_length=100, blank=True, help_text="GPS coordinates (optional)")
    
    # Step 3: Soil Information
    soil_type = models.CharField(max_length=20, choices=SOIL_TYPE_CHOICES, help_text="Type of soil on your farm")
    soil_fertility = models.CharField(max_length=20, choices=FERTILITY_CHOICES, help_text="Soil fertility level")
    ph_level = models.FloatField(null=True, blank=True, help_text="Soil pH level (if known)")
    soil_test_done = models.BooleanField(default=False, help_text="Have you done soil testing?")
    last_soil_test_date = models.DateField(null=True, blank=True, help_text="Date of last soil test")
    
    # Step 4: Water and Irrigation
    water_source = models.CharField(max_length=20, choices=WATER_SOURCE_CHOICES, help_text="Main water source")
    irrigation_method = models.CharField(max_length=20, choices=IRRIGATION_CHOICES, help_text="Irrigation method used")
    water_availability = models.CharField(max_length=100, help_text="Water availability throughout the year")
    irrigation_equipment = models.TextField(blank=True, help_text="Describe irrigation equipment available")
    
    # Step 5: Farm Equipment and Resources
    available_equipment = models.JSONField(default=list, help_text="List of available equipment")
    equipment_details = models.TextField(blank=True, help_text="Additional equipment details")
    labor_source = models.CharField(max_length=100, help_text="Source of labor (family, hired, mixed)")
    labor_count = models.IntegerField(null=True, blank=True, help_text="Number of regular workers")
    
    # Step 6: Farming Practices and Experience
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, help_text="Farming experience level")
    farming_methods = models.TextField(help_text="Describe your farming methods")
    fertilizer_usage = models.BooleanField(default=True, help_text="Do you use fertilizers?")
    pesticide_usage = models.BooleanField(default=True, help_text="Do you use pesticides?")
    organic_farming = models.BooleanField(default=False, help_text="Do you practice organic farming?")
    
    # Step 7: Goals and Challenges
    farming_goals = models.TextField(help_text="What are your farming goals?")
    main_challenges = models.TextField(help_text="What are your main farming challenges?")
    expected_yield = models.FloatField(null=True, blank=True, help_text="Expected yield per hectare (tons)")
    market_access = models.CharField(max_length=200, help_text="How do you access markets?")
    
    # Additional Information
    additional_notes = models.TextField(blank=True, help_text="Any additional information")
    phone_number = models.CharField(max_length=20, blank=True, help_text="Alternative contact number")
    
    # Metadata
    is_completed = models.BooleanField(default=False, help_text="Whether onboarding is completed")
    completion_date = models.DateTimeField(null=True, blank=True, help_text="Date when onboarding was completed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Farm Details"
        verbose_name_plural = "Farm Details"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Farm Details - {self.farm_name} ({self.user.email})"
    
    def mark_completed(self):
        """Mark onboarding as completed"""
        self.is_completed = True
        self.completion_date = timezone.now()
        self.save()
    
    def completion_percentage(self):
        """Calculate completion percentage based on filled fields"""
        required_fields = [
            'farm_name', 'farm_type', 'farm_size_category', 'primary_crop',
            'farming_years', 'region', 'division', 'subdivision', 'village_town',
            'soil_type', 'soil_fertility', 'water_source', 'irrigation_method',
            'experience_level', 'farming_methods', 'farming_goals', 'main_challenges',
            'market_access'
        ]
        
        filled_count = sum(1 for field in required_fields if getattr(self, field))
        return int((filled_count / len(required_fields)) * 100)
    
    def get_farm_size_display_range(self):
        """Get human-readable farm size range"""
        size_ranges = {
            'less_than_1': '< 1 hectare',
            '1_to_5': '1-5 hectares',
            '5_to_10': '5-10 hectares',
            '10_to_50': '10-50 hectares',
            'more_than_50': '> 50 hectares',
        }
        return size_ranges.get(self.farm_size_category, 'Unknown')
    
    def get_equipment_display(self):
        """Get formatted equipment list"""
        equipment_names = {
            'tractor': 'Tractor',
            'plow': 'Plow',
            'harrow': 'Harrow',
            'planter': 'Planter/Seeder',
            'harvester': 'Harvester',
            'sprayer': 'Sprayer',
            'irrigation_pump': 'Irrigation pump',
            'thresher': 'Thresher',
            'none': 'No equipment',
            'other': 'Other',
        }
        return [equipment_names.get(eq, eq) for eq in self.available_equipment]

class WeatherData(models.Model):
    """Store weather data for farm locations"""
    farm = models.ForeignKey(FarmDetails, on_delete=models.CASCADE, related_name='weather_data')
    date = models.DateField()
    temperature_min = models.FloatField(null=True, blank=True)
    temperature_max = models.FloatField(null=True, blank=True)
    temperature_avg = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    rainfall = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    weather_condition = models.CharField(max_length=50, blank=True)
    data_source = models.CharField(max_length=50, default='api')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['farm', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Weather - {self.farm.farm_name} ({self.date})"
