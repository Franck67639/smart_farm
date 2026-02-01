from django.contrib import admin
from .models import MaizeVariety, FarmDetails, WeatherData

@admin.register(MaizeVariety)
class MaizeVarietyAdmin(admin.ModelAdmin):
    """Admin configuration for MaizeVariety model"""
    list_display = ['name', 'code', 'maturity_period', 'expected_yield', 'drought_tolerance', 'disease_resistance', 'is_active']
    list_filter = ['maturity_period', 'drought_tolerance', 'disease_resistance', 'is_active']
    search_fields = ['name', 'code', 'description', 'recommended_region']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description')
        }),
        ('Characteristics', {
            'fields': ('maturity_period', 'expected_yield', 'drought_tolerance', 'disease_resistance')
        }),
        ('Regional Information', {
            'fields': ('recommended_region',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make code readonly if object exists to prevent breaking references"""
        if obj:
            return ['code']
        return []

@admin.register(FarmDetails)
class FarmDetailsAdmin(admin.ModelAdmin):
    """Admin configuration for FarmDetails model"""
    list_display = ['farm_name', 'user', 'region', 'primary_crop', 'is_completed', 'completion_date']
    list_filter = ['region', 'farm_type', 'primary_crop', 'is_completed', 'soil_type', 'irrigation_method']
    search_fields = ['farm_name', 'user__email', 'user__full_name', 'village_town']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Farm Information', {
            'fields': ('user', 'farm_name', 'farm_type', 'farm_size_category', 'primary_crop', 'farming_years', 'selected_maize_variety')
        }),
        ('Location', {
            'fields': ('region', 'division', 'subdivision', 'village_town', 'gps_coordinates')
        }),
        ('Soil Information', {
            'fields': ('soil_type', 'soil_fertility', 'ph_level', 'soil_test_done', 'last_soil_test_date')
        }),
        ('Water & Irrigation', {
            'fields': ('water_source', 'irrigation_method', 'water_availability', 'irrigation_equipment')
        }),
        ('Equipment & Labor', {
            'fields': ('available_equipment', 'equipment_details', 'labor_source', 'labor_count')
        }),
        ('Farming Practices', {
            'fields': ('experience_level', 'farming_methods', 'fertilizer_usage', 'pesticide_usage', 'organic_farming')
        }),
        ('Goals & Challenges', {
            'fields': ('farming_goals', 'main_challenges', 'expected_yield', 'market_access')
        }),
        ('Additional Information', {
            'fields': ('additional_notes', 'phone_number')
        }),
        ('Status', {
            'fields': ('is_completed', 'completion_date')
        }),
    )
    
    readonly_fields = ['completion_date']

@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    """Admin configuration for WeatherData model"""
    list_display = ['farm', 'date', 'temperature_avg', 'humidity', 'rainfall', 'weather_condition']
    list_filter = ['date', 'weather_condition', 'data_source']
    search_fields = ['farm__farm_name', 'weather_condition']
    ordering = ['-date']
    date_hierarchy = 'date'

# Register custom User admin if needed
try:
    from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Only unregister and re-register if User is our custom model
    if User.__module__ == 'smart_farm.models':
        admin.site.unregister(User)
        
        @admin.register(User)
        class UserAdmin(DefaultUserAdmin):
            """Custom User admin"""
            list_display = ['email', 'full_name', 'phone', 'is_verified', 'is_staff', 'date_joined']
            list_filter = ['is_verified', 'is_staff', 'is_superuser', 'is_active']
            search_fields = ['email', 'full_name', 'phone']
            ordering = ['-date_joined']
            
            fieldsets = (
                (None, {
                    'fields': ('username', 'email', 'password')
                }),
                ('Personal info', {
                    'fields': ('first_name', 'last_name', 'full_name', 'phone')
                }),
                ('Permissions', {
                    'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')
                }),
                ('Important dates', {
                    'fields': ('last_login', 'date_joined')
                }),
            )
            
            add_fieldsets = (
                (None, {
                    'classes': ('wide',),
                    'fields': ('email', 'username', 'full_name', 'phone', 'password1', 'password2'),
                }),
            )
except:
    # If there's any issue with User registration, just skip it
    pass
