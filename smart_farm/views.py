from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import csv
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import json
import re
from datetime import datetime

from .models import User, FarmDetails, MaizeVariety

def landing_view(request):
    """Landing page for SmartFarm Cameroon"""
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'landing.html')

def login_view(request):
    """Handle login using email"""

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')  # Get email directly
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        user = None

        # Check if email exists first
        try:
            user_obj = User.objects.get(email=email)
            # Email exists, now check password
            if user_obj.check_password(password):
                user = authenticate(request, email=user_obj.email, password=password)
            else:
                # Email exists but password is wrong
                messages.error(request, 'Incorrect password. Please try again.')
                return render(request, 'auth/login.html')
        except User.DoesNotExist:
            # Email doesn't exist
            messages.error(request, 'No account found with this email address.')
            return render(request, 'auth/login.html')

        if user is not None:
            login(request, user)

            # Handle "Remember Me"
            if not remember:
                request.session.set_expiry(0)  # session expires when browser closes

            messages.success(request, f'Welcome back, {user.full_name}!')
            return redirect('dashboard')

    return render(request, 'auth/login.html')


def validate_registration_data(request):
    """
    Validate registration form data and return errors if any
    """
    errors = {}
    
    # Get form data
    email = request.POST.get('email', '').strip()
    full_name = request.POST.get('full_name', '').strip()
    phone = request.POST.get('phone', '').strip()
    password = request.POST.get('password', '')
    confirm_password = request.POST.get('confirm_password', '')
    terms = request.POST.get('terms')
    
    # Email validation
    if not email:
        errors['email'] = 'Email is required'
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'Please enter a valid email address'
        if User.objects.filter(email__iexact=email).exists():
            errors['email'] = 'Email already registered'
    
    # Full name validation
    if not full_name:
        errors['full_name'] = 'Full name is required'
    elif len(full_name) < 2:
        errors['full_name'] = 'Full name must be at least 2 characters long'
    
    # Phone validation
    if not phone:
        errors['phone'] = 'Phone number is required'
    elif not re.match(r'^\+?[\d\s\-\(\)]{10,20}$', phone):
        errors['phone'] = 'Please enter a valid phone number'
    
    # Password validation
    if not password:
        errors['password'] = 'Password is required'
    elif len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters long'
    elif not re.search(r'[A-Z]', password):
        errors['password'] = 'Password must contain at least one uppercase letter'
    elif not re.search(r'[a-z]', password):
        errors['password'] = 'Password must contain at least one lowercase letter'
    elif not re.search(r'\d', password):
        errors['password'] = 'Password must contain at least one number'
    
    # Password confirmation
    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match'
    
    # Terms validation
    if not terms:
        errors['terms'] = 'You must agree to the terms and conditions'
    
    return errors

def create_user_account(request):
    """
    Create user account after validation passes
    """
    try:
        with transaction.atomic():
            email = request.POST.get('email').strip()
            user = User.objects.create_user(
                email=email,
                password=request.POST.get('password'),
                full_name=request.POST.get('full_name').strip(),
                phone=request.POST.get('phone').strip()
            )
            
            # Queue welcome email using ultra-lightweight service (minimal resources)
            try:
                from .mail_service_ultralight import ultra_light_mail_service
                success = ultra_light_mail_service.send_welcome_email(user)
                if success:
                    logger.info(f"Welcome email queued for {email}")
                else:
                    logger.warning(f"Failed to queue welcome email for {email}")
            except Exception as e:
                # Log error but don't fail user creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to queue welcome email for {email}: {e}")
            
            return user, None
    except Exception as e:
        return None, str(e)

def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        # Validate form data
        errors = validate_registration_data(request)
        
        if errors:
            # Add specific error messages
            for field, error_message in errors.items():
                messages.error(request, f"{field.replace('_', ' ').title()}: {error_message}")
            return render(request, 'auth/register.html')
        
        # Create user account
        user, creation_error = create_user_account(request)
        
        if creation_error:
            messages.error(request, f'Registration failed: {creation_error}')
            return render(request, 'auth/register.html')
        
        if user:
            # Auto-login after registration
            login(request, user)
            messages.success(request, 'Account created successfully! Redirecting to onboarding...')
            return redirect('onboarding')
    
    return render(request, 'auth/register.html')

@login_required
def logout_view(request):
    """Handle user logout"""
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')

@login_required
def dashboard_view(request):
    """Main dashboard view"""
    # Get all user farms
    user_farms = FarmDetails.objects.filter(user=request.user)
    
    # Get current farm from session or use first farm
    current_farm_id = request.session.get('current_farm_id')
    current_farm = None
    
    if current_farm_id:
        try:
            current_farm = user_farms.get(id=current_farm_id)
        except FarmDetails.DoesNotExist:
            current_farm = None
    
    # If no current farm in session or it doesn't exist, use first farm
    if not current_farm and user_farms.exists():
        current_farm = user_farms.first()
        request.session['current_farm_id'] = str(current_farm.id)
    
    # Get weather data for current farm
    from weather.models import WeatherForecast, WeatherAlert
    from smart_farm.models import WeatherData
    
    weather_data = None
    weather_forecasts = []
    weather_alerts = []
    
    if current_farm:
        # Get latest weather data
        latest_weather = WeatherData.objects.filter(farm=current_farm).first()
        if latest_weather:
            weather_data = latest_weather
        
        # Get upcoming forecasts (next 3 days)
        forecasts = WeatherForecast.objects.filter(
            farm=current_farm,
            forecast_date__gte=timezone.now().date()
        ).order_by('forecast_date')[:3]
        weather_forecasts = forecasts
        
        # Get active alerts
        alerts = WeatherAlert.objects.filter(
            farm=current_farm,
            user=request.user,
            is_active=True,
            expires__gte=timezone.now()
        ).order_by('-created_at')
        weather_alerts = alerts
    
    context = {
        'user': request.user,
        'user_farms': user_farms,
        'current_farm': current_farm,
        'farm_details': current_farm,  # For backward compatibility
        'current_time': datetime.now().strftime('%I:%M %p'),
        'weather': weather_data,
        'forecasts': weather_forecasts,
        'alerts': weather_alerts,
        'alerts_count': len([a for a in weather_alerts if not a.acknowledged]),
        'primary_field': current_farm,  # For weather widget compatibility
    }
    return render(request, 'dashboard.html', context)

@login_required
def switch_farm(request, farm_id):
    """Switch to a different farm"""
    try:
        farm = FarmDetails.objects.get(id=farm_id, user=request.user)
        request.session['current_farm_id'] = str(farm.id)
        messages.success(request, f'Switched to {farm.farm_name}')
    except FarmDetails.DoesNotExist:
        messages.error(request, 'Farm not found')
    
    return redirect('dashboard')

@login_required
def add_new_farm(request):
    """Start onboarding for a new farm"""
    # Clear any existing onboarding session data
    if 'onboarding_data' in request.session:
        del request.session['onboarding_data']
    
    # Set flag to indicate this is adding a new farm
    request.session['adding_new_farm'] = True
    
    messages.info(request, 'Let\'s add your new farm! Please complete the onboarding process.')
    return redirect('onboarding')

@login_required
def delete_farm(request, farm_id):
    """Delete a farm"""
    try:
        farm = FarmDetails.objects.get(id=farm_id, user=request.user)
        
        # Check if user has other farms
        user_farms = FarmDetails.objects.filter(user=request.user)
        
        if user_farms.count() <= 1:
            messages.error(request, 'You cannot delete your only farm. Please add another farm first.')
        else:
            farm_name = farm.farm_name
            farm.delete()
            
            # If this was the current farm, switch to another
            if request.session.get('current_farm_id') == str(farm.id):
                new_farm = user_farms.exclude(id=farm_id).first()
                if new_farm:
                    request.session['current_farm_id'] = str(new_farm.id)
            
            messages.success(request, f'{farm_name} has been deleted successfully.')
            
    except FarmDetails.DoesNotExist:
        messages.error(request, 'Farm not found')
    
    return redirect('farm_list')

@login_required
def farm_list_view(request):
    """Display all user's farms"""
    farms = FarmDetails.objects.filter(user=request.user).order_by('-created_at')
    current_farm_id = request.session.get('current_farm_id')
    
    context = {
        'farms': farms,
        'current_farm_id': current_farm_id,
        'total_farms': farms.count(),
    }
    return render(request, 'farm/farm_list.html', context)

@login_required
def farm_detail_view(request, farm_id):
    """Display detailed information about a specific farm"""
    try:
        farm = FarmDetails.objects.get(id=farm_id, user=request.user)
        
        # Get weather data for this farm
        weather_data = {}
        weather_forecasts = []
        weather_alerts = []
        
        # Try to get weather data if location is available
        if farm.gps_coordinates:
            try:
                from .weather_service import WeatherService
                weather_service = WeatherService()
                
                # Parse coordinates
                if ',' in farm.gps_coordinates:
                    lat, lng = map(float, farm.gps_coordinates.split(','))
                else:
                    # Fallback to region-based weather
                    lat, lng = 3.8480, 11.5021  # Cameroon center
                
                weather_data = weather_service.get_current_weather(lat, lng)
                weather_forecasts = weather_service.get_forecast(lat, lng, days=5)
                weather_alerts = weather_service.get_weather_alerts(lat, lng)
                
            except Exception as e:
                print(f"Weather service error: {e}")
                weather_data = {}
                weather_forecasts = []
                weather_alerts = []
        
        context = {
            'farm': farm,
            'weather': weather_data,
            'forecasts': weather_forecasts,
            'alerts': weather_alerts,
            'alerts_count': len([a for a in weather_alerts if not getattr(a, 'acknowledged', False)]),
            'completion_percentage': farm.completion_percentage(),
        }
        return render(request, 'farm/farm_detail.html', context)
        
    except FarmDetails.DoesNotExist:
        messages.error(request, 'Farm not found')
        return redirect('farm_list')

@login_required
def onboarding_step_view(request):
    """Handle onboarding steps"""
    # Check if this is adding a new farm
    is_adding_new_farm = request.session.get('adding_new_farm', False)
    
    if is_adding_new_farm:
        # Create a new farm with defaults for adding another farm
        farm_details = FarmDetails.objects.create(
            user=request.user,
            farm_name=f"{request.user.full_name or request.user.email}'s Farm",
            farm_type='smallholder',
            farm_size_category='1_to_5',
            primary_crop='maize',
            farming_years=1,  # Required field with default
            region='center',  # Required field with default
            division='',
            subdivision='',
            village_town='',
            soil_type='loamy',
            soil_fertility='medium',
            water_source='rain_fed',
            irrigation_method='none',
            experience_level='beginner',
            fertilizer_usage=True,
            pesticide_usage=True,
            organic_farming=False,
        )
    else:
        # Get the user's current farm or create a new one if none exists
        current_farm_id = request.session.get('current_farm_id')
        if current_farm_id:
            try:
                farm_details = FarmDetails.objects.get(id=current_farm_id, user=request.user)
            except FarmDetails.DoesNotExist:
                # If current farm ID is invalid, get the latest farm
                farm_details = FarmDetails.objects.filter(user=request.user).latest('created_at')
        else:
            # Get the latest farm or create a new one
            try:
                farm_details = FarmDetails.objects.filter(user=request.user).latest('created_at')
            except FarmDetails.DoesNotExist:
                farm_details = FarmDetails.objects.create(
                    user=request.user,
                    farm_name=f"{request.user.full_name or request.user.email}'s Farm",
                    farm_type='smallholder',
                    farm_size_category='1_to_5',
                    primary_crop='maize',
                    farming_years=1,  # Required field with default
                    region='center',  # Required field with default
                    division='',
                    subdivision='',
                    village_town='',
                    soil_type='loamy',
                    soil_fertility='medium',
                    water_source='rain_fed',
                    irrigation_method='none',
                    experience_level='beginner',
                    fertilizer_usage=True,
                    pesticide_usage=True,
                    organic_farming=False,
                )
    
    # Get maize varieties for step 1 (or any step where you want to show them)
    maize_varieties = MaizeVariety.objects.filter(is_active=True)
    
    context = {
        'total_steps': 7,
        'progress_percentage': farm_details.completion_percentage(),
        'farm_details': farm_details,
        'maize_varieties': maize_varieties,
        'current_time': datetime.now().strftime('%I:%M %p'),
        'is_adding_new_farm': is_adding_new_farm,
    }
    
    return render(request, 'partials/_onboarding.html', context)

@login_required
@require_http_methods(["GET"])
def weather_partial_view(request):
    """Return weather widget partial for HTMX updates"""
    context = {
        'current_time': datetime.now().strftime('%I:%M %p'),
        # Add weather data here
    }
    return render(request, 'partials/_weather_widget.html', context)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_onboarding_step_view(request):
    """Save onboarding step data"""
    try:
        data = json.loads(request.body)
        step = data.get('step')
        
        # Check if this is adding a new farm
        is_adding_new_farm = request.session.get('adding_new_farm', False)
        
        if is_adding_new_farm:
            # Create new farm with required defaults for first step
            if step == 1:
                farm_details = FarmDetails.objects.create(
                    user=request.user,
                    farm_name=data.get('farmName', f"{request.user.full_name or request.user.email}'s Farm"),
                    farm_type=data.get('farmType', 'smallholder'),
                    farm_size_category=data.get('farmSizeCategory', '1_to_5'),
                    primary_crop=data.get('primaryCrop', 'maize'),
                    farming_years=1,  # Required field with default
                    region='center',  # Required field with default
                    village_town='',  # Required field with default
                    soil_type='loamy',
                    soil_fertility='medium',
                    water_source='rain_fed',
                    irrigation_method='none',
                    experience_level='beginner',
                    fertilizer_usage=True,
                    pesticide_usage=True,
                    organic_farming=False,
                )
            else:
                # For subsequent steps, get the existing farm
                farm_details = FarmDetails.objects.filter(user=request.user).latest('created_at')
        else:
            # Get or create existing farm details
            farm_details, created = FarmDetails.objects.get_or_create(
                user=request.user,
                defaults={
                    'farm_name': f"{request.user.full_name or request.user.email}'s Farm",
                    'farm_type': 'smallholder',
                    'farm_size_category': '1_to_5',
                    'primary_crop': 'maize',
                    'farming_years': 1,  # Required field with default
                    'region': 'center',  # Required field with default
                    'village_town': '',  # Required field with default
                    'soil_type': 'loamy',
                    'soil_fertility': 'medium',
                    'water_source': 'rain_fed',
                    'irrigation_method': 'none',
                    'experience_level': 'beginner',
                    'fertilizer_usage': True,
                    'pesticide_usage': True,
                    'organic_farming': False,
                }
            )
        
        # Update farm details based on step
        if step == 1:  # Basic farm information
            farm_details.farm_name = data.get('farmName', farm_details.farm_name)
            farm_details.farm_type = data.get('farmType', farm_details.farm_type)
            farm_details.farm_size_category = data.get('farmSizeCategory') or data.get('farmSize', farm_details.farm_size_category)
            farm_details.primary_crop = data.get('primaryCrop', farm_details.primary_crop)
            
            # Convert farming_years to integer with default
            farming_years = data.get('farmingYears', 1)
            try:
                farm_details.farming_years = int(farming_years) if farming_years else 1
            except (ValueError, TypeError):
                farm_details.farming_years = 1
            
            # Handle maize variety selection
            maize_variety_id = data.get('selectedMaizeVariety')
            if maize_variety_id:
                try:
                    variety = MaizeVariety.objects.get(id=maize_variety_id, is_active=True)
                    farm_details.selected_maize_variety = variety
                except MaizeVariety.DoesNotExist:
                    pass
            
        elif step == 2:  # Location information
            farm_details.region = data.get('region', farm_details.region)
            farm_details.division = data.get('division', farm_details.division)
            farm_details.subdivision = data.get('subdivision', farm_details.subdivision)
            farm_details.village_town = data.get('villageTown', farm_details.village_town)
            farm_details.gps_coordinates = data.get('gpsCoordinates', farm_details.gps_coordinates)
            
        elif step == 3:  # Soil information
            farm_details.soil_type = data.get('soilType', farm_details.soil_type)
            farm_details.soil_fertility = data.get('soilFertility', farm_details.soil_fertility)
            farm_details.ph_level = data.get('soilPh') or data.get('phLevel', farm_details.ph_level)
            farm_details.soil_test_done = data.get('soilTestDone', False)
            
            # Handle last_soil_test_date properly - convert empty string to None
            last_soil_test_date = data.get('lastSoilTestDate', '')
            if last_soil_test_date and last_soil_test_date.strip():
                try:
                    farm_details.last_soil_test_date = last_soil_test_date
                except ValueError:
                    # If date format is invalid, keep existing value or set to None
                    farm_details.last_soil_test_date = None
            else:
                farm_details.last_soil_test_date = None
            
        elif step == 4:  # Water and irrigation
            farm_details.water_source = data.get('waterSource', farm_details.water_source)
            farm_details.irrigation_method = data.get('irrigationMethod', farm_details.irrigation_method)
            farm_details.water_availability = data.get('waterAvailability', farm_details.water_availability)
            farm_details.irrigation_equipment = data.get('irrigationEquipment', '')
            
        elif step == 5:  # Equipment and resources
            farm_details.available_equipment = data.get('availableEquipment', [])
            farm_details.equipment_details = data.get('equipmentDetails', '')
            farm_details.labor_source = data.get('laborSource', farm_details.labor_source)
            
            # Convert labor_count to integer with default
            labor_count = data.get('laborCount', 1)
            try:
                farm_details.labor_count = int(labor_count) if labor_count else None
            except (ValueError, TypeError):
                farm_details.labor_count = None
            
        elif step == 6:  # Farming practices
            farm_details.experience_level = data.get('experienceLevel', farm_details.experience_level)
            farm_details.farming_methods = data.get('farmingMethods', farm_details.farming_methods)
            farm_details.fertilizer_usage = data.get('fertilizerUsage', True)
            farm_details.pesticide_usage = data.get('pesticideUsage', True)
            farm_details.organic_farming = data.get('organicFarming', False)
            
        elif step == 7:  # Goals and challenges
            farm_details.farming_goals = data.get('farmingGoals', '')
            farm_details.main_challenges = data.get('mainChallenges', '')
            
            # Handle expected_yield properly - convert empty string to None
            expected_yield = data.get('expectedYield', '')
            if expected_yield and expected_yield.strip():
                try:
                    farm_details.expected_yield = float(expected_yield)
                except (ValueError, TypeError):
                    # If conversion fails, keep existing value or set to None
                    farm_details.expected_yield = None
            else:
                farm_details.expected_yield = None
                
            farm_details.market_access = data.get('marketAccess', '')
            
            # Mark as completed if this is the final step
            farm_details.mark_completed()
        
        farm_details.save()
        
        return JsonResponse({
            'success': True, 
            'progress_percentage': farm_details.completion_percentage(),
            'is_completed': farm_details.is_completed
        })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def complete_onboarding_view(request):
    """Complete onboarding and finalize farm details"""
    try:
        data = json.loads(request.body)
        
        # Check if this is adding a new farm or updating existing
        is_adding_new_farm = request.session.get('adding_new_farm', False)
        
        if is_adding_new_farm:
            # Create new farm with required defaults
            farm_details = FarmDetails.objects.create(
                user=request.user,
                farm_name=data.get('farmName', f"{request.user.full_name or request.user.email}'s Farm"),
                farm_type=data.get('farmType', 'smallholder'),
                farm_size_category=data.get('farmSizeCategory') or data.get('farmSize', '1_to_5'),
                primary_crop=data.get('primaryCrop', 'maize'),
                farming_years=1,  # Required field with default
                region=data.get('region', 'center'),  # Required field with default
                village_town=data.get('villageTown', ''),  # Required field with default
                soil_type=data.get('soilType', 'loamy'),
                soil_fertility=data.get('soilFertility', 'medium'),
                water_source=data.get('waterSource', 'rain_fed'),
                irrigation_method=data.get('irrigationMethod', 'none'),
                experience_level=data.get('experienceLevel', 'beginner'),
                fertilizer_usage=True,
                pesticide_usage=True,
                organic_farming=False,
            )
            
            # Clear the session flag
            del request.session['adding_new_farm']
        else:
            # Update existing farm that was created during onboarding
            farm_details = FarmDetails.objects.filter(user=request.user).first()
            if not farm_details:
                farm_details = FarmDetails.objects.create(
                    user=request.user,
                    farm_name=data.get('farmName', f"{request.user.full_name or request.user.email}'s Farm"),
                    farm_type=data.get('farmType', 'smallholder'),
                    farm_size_category=data.get('farmSizeCategory') or data.get('farmSize', '1_to_5'),
                    primary_crop=data.get('primaryCrop', 'maize'),
                    farming_years=1,  # Required field with default
                    region=data.get('region', 'center'),  # Required field with default
                    village_town=data.get('villageTown', ''),  # Required field with default
                    soil_type=data.get('soilType', 'loamy'),
                    soil_fertility=data.get('soilFertility', 'medium'),
                    water_source=data.get('waterSource', 'rain_fed'),
                    irrigation_method=data.get('irrigationMethod', 'none'),
                    experience_level=data.get('experienceLevel', 'beginner'),
                    fertilizer_usage=True,
                    pesticide_usage=True,
                    organic_farming=False,
                )
        
        # Update fields from request data (prioritize request data over session data)
        # Basic farm information
        farm_details.farm_name = data.get('farmName', farm_details.farm_name)
        farm_details.farm_type = data.get('farmType', farm_details.farm_type)
        farm_details.farm_size_category = data.get('farmSizeCategory') or data.get('farmSize', farm_details.farm_size_category)
        farm_details.primary_crop = data.get('primaryCrop', farm_details.primary_crop)
        
        # Handle farming_years conversion
        farming_years = data.get('farmingYears', farm_details.farming_years)
        try:
            farm_details.farming_years = int(farming_years) if farming_years else 1
        except (ValueError, TypeError):
            farm_details.farming_years = 1
        
        # Location information
        farm_details.region = data.get('region', farm_details.region)
        farm_details.division = data.get('division', farm_details.division)
        farm_details.subdivision = data.get('subdivision', farm_details.subdivision)
        farm_details.village_town = data.get('villageTown', farm_details.village_town)
        
        # Handle GPS coordinates
        gps_coords = data.get('gpsCoordinates', {})
        if isinstance(gps_coords, dict) and gps_coords.get('lat') and gps_coords.get('lng'):
            farm_details.gps_coordinates = f"{gps_coords['lat']}, {gps_coords['lng']}"
        elif isinstance(gps_coords, str):
            farm_details.gps_coordinates = gps_coords
        
        # Soil information
        farm_details.soil_type = data.get('soilType', farm_details.soil_type)
        farm_details.soil_fertility = data.get('soilFertility', farm_details.soil_fertility)
        farm_details.ph_level = data.get('soilPh') or data.get('phLevel', farm_details.ph_level)
        farm_details.soil_test_done = data.get('soilTestDone', False)
        
        # Handle last_soil_test_date properly - convert empty string to None
        last_soil_test_date = data.get('lastSoilTestDate', '')
        if last_soil_test_date and last_soil_test_date.strip():
            try:
                farm_details.last_soil_test_date = last_soil_test_date
            except ValueError:
                # If date format is invalid, keep existing value or set to None
                farm_details.last_soil_test_date = None
        else:
            farm_details.last_soil_test_date = None
        
        # Water and irrigation
        farm_details.water_source = data.get('waterSource', farm_details.water_source)
        farm_details.irrigation_method = data.get('irrigationMethod', farm_details.irrigation_method)
        farm_details.water_availability = data.get('waterAvailability', farm_details.water_availability)
        farm_details.irrigation_equipment = data.get('irrigationEquipment', '')
        
        # Equipment and resources
        farm_details.available_equipment = data.get('availableEquipment', [])
        farm_details.equipment_details = data.get('equipmentDetails', '')
        farm_details.labor_source = data.get('laborSource', farm_details.labor_source)
        
        # Handle labor_count conversion
        labor_count = data.get('laborCount', farm_details.labor_count)
        try:
            farm_details.labor_count = int(labor_count) if labor_count else None
        except (ValueError, TypeError):
            farm_details.labor_count = None
        
        # Farming practices
        farm_details.experience_level = data.get('experienceLevel', farm_details.experience_level)
        farm_details.farming_methods = data.get('farmingMethods', farm_details.farming_methods)
        farm_details.fertilizer_usage = data.get('fertilizerUsage', True)
        farm_details.pesticide_usage = data.get('pesticideUsage', True)
        farm_details.organic_farming = data.get('organicFarming', False)
        
        # Goals and challenges
        farm_details.farming_goals = data.get('farmingGoals', '')
        farm_details.main_challenges = data.get('mainChallenges', '')
        
        # Handle expected_yield properly - convert empty string to None
        expected_yield = data.get('expectedYield', '')
        if expected_yield and expected_yield.strip():
            try:
                farm_details.expected_yield = float(expected_yield)
            except (ValueError, TypeError):
                # If conversion fails, keep existing value or set to None
                farm_details.expected_yield = None
        else:
            farm_details.expected_yield = None
            
        farm_details.market_access = data.get('marketAccess', '')
        
        # Maize variety
        selected_variety = data.get('maizeVariety') or data.get('selectedMaizeVariety')
        if selected_variety:
            try:
                from smart_farm.models import MaizeVariety
                variety = MaizeVariety.objects.get(id=selected_variety, is_active=True)
                farm_details.selected_maize_variety = variety
            except MaizeVariety.DoesNotExist:
                pass
        
        # Final fields from completion request
        farm_details.additional_notes = data.get('additionalNotes', '')
        farm_details.phone_number = data.get('phoneNumber', '')
        
        # Mark as completed
        farm_details.mark_completed()
        
        # If this is a new farm, set it as current
        if is_adding_new_farm:
            request.session['current_farm_id'] = str(farm_details.id)
        
        return JsonResponse({
            'success': True, 
            'farm_id': str(farm_details.id),
            'completion_date': farm_details.completion_date.isoformat(),
            'is_new_farm': is_adding_new_farm
        })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def set_farm_view(request):
    """Switch between farms (placeholder for future multi-farm support)"""
    try:
        data = json.loads(request.body)
        farm_id = data.get('farm_id')
        
        # For now, just return success since we have one farm per user
        try:
            farm_details = request.user.farm_details
            return JsonResponse({'success': True, 'farm_name': farm_details.farm_name})
        except FarmDetails.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Farm not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def reverse_geocode_view(request):
    """Server-side reverse geocoding to avoid CORS issues"""
    try:
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        
        if not lat or not lng:
            return JsonResponse({'error': 'Missing coordinates'}, status=400)
        
        # Use Nominatim API from server side
        import requests
        
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            'format': 'json',
            'lat': lat,
            'lon': lng,
            'zoom': 18,
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'SmartFarm/1.0 (smartfarm@example.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get('display_name', f"{lat}, {lng}")
            return JsonResponse({
                'success': True,
                'address': address,
                'data': data
            })
        else:
            # Return coordinates as fallback
            return JsonResponse({
                'success': False,
                'address': f"{lat}, {lng}",
                'error': f'HTTP {response.status_code}'
            })
            
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'address': f"{lat}, {lng}",
            'error': 'Network error'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'address': f"{lat}, {lng}",
            'error': str(e)
        })

@login_required
def export_farm_csv(request, farm_id):
    """Export farm details as CSV"""
    try:
        farm = FarmDetails.objects.get(id=farm_id, user=request.user)
        
        # Create the HttpResponse object with the appropriate CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{farm.farm_name}_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Create a CSV writer
        writer = csv.writer(response)
        
        # Write header row
        header = [
            'Farm Name',
            'Farm Type', 
            'Farm Size Category',
            'Primary Crop',
            'Farming Years',
            'Region',
            'Division',
            'Subdivision', 
            'Village/Town',
            'GPS Coordinates',
            'Soil Type',
            'Soil Fertility',
            'pH Level',
            'Soil Test Done',
            'Last Soil Test Date',
            'Water Source',
            'Irrigation Method',
            'Water Availability',
            'Irrigation Equipment',
            'Available Equipment',
            'Equipment Details',
            'Labor Source',
            'Labor Count',
            'Experience Level',
            'Farming Methods',
            'Fertilizer Usage',
            'Pesticide Usage',
            'Organic Farming',
            'Selected Maize Variety',
            'Farming Goals',
            'Main Challenges',
            'Expected Yield',
            'Market Access',
            'Additional Notes',
            'Phone Number',
            'Created Date',
            'Completion Date',
            'Profile Completion %'
        ]
        writer.writerow(header)
        
        # Write data row
        data_row = [
            farm.farm_name or '',
            farm.get_farm_type_display() or '',
            farm.get_farm_size_category_display() or '',
            farm.get_primary_crop_display() or '',
            farm.farming_years or '',
            farm.get_region_display() or '',
            farm.division or '',
            farm.subdivision or '',
            farm.village_town or '',
            farm.gps_coordinates or '',
            farm.get_soil_type_display() or '',
            farm.get_soil_fertility_display() or '',
            farm.ph_level or '',
            'Yes' if farm.soil_test_done else 'No',
            farm.last_soil_test_date.strftime('%Y-%m-%d') if farm.last_soil_test_date else '',
            farm.get_water_source_display() or '',
            farm.get_irrigation_method_display() or '',
            farm.water_availability or '',
            farm.irrigation_equipment or '',
            ', '.join(farm.get_equipment_display()) if farm.available_equipment else '',
            farm.equipment_details or '',
            farm.labor_source or '',
            farm.labor_count or '',
            farm.get_experience_level_display() or '',
            farm.farming_methods or '',
            'Yes' if farm.fertilizer_usage else 'No',
            'Yes' if farm.pesticide_usage else 'No',
            'Yes' if farm.organic_farming else 'No',
            farm.selected_maize_variety.name if farm.selected_maize_variety else '',
            farm.farming_goals or '',
            farm.main_challenges or '',
            farm.expected_yield or '',
            farm.market_access or '',
            farm.additional_notes or '',
            farm.phone_number or '',
            farm.created_at.strftime('%Y-%m-%d %H:%M:%S') if farm.created_at else '',
            farm.completion_date.strftime('%Y-%m-%d %H:%M:%S') if farm.completion_date else '',
            f"{farm.completion_percentage()}%" if hasattr(farm, 'completion_percentage') else '0%'
        ]
        writer.writerow(data_row)
        
        return response
        
    except FarmDetails.DoesNotExist:
        messages.error(request, 'Farm not found')
        return redirect('farm_list')
    except Exception as e:
        messages.error(request, f'Error exporting farm data: {str(e)}')
        return redirect('farm_detail', farm_id=farm_id)
