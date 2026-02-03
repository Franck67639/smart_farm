from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
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
        email = request.POST.get('username')  # form field name stays the same but we treat it as email
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
                username=email,  # Django still expects username parameter
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
    
    return redirect('dashboard')

@login_required
def onboarding_step_view(request):
    """Handle onboarding steps"""
    # Get or create farm details with defaults for required fields
    farm_details, created = FarmDetails.objects.get_or_create(
        user=request.user,
        defaults={
            'farm_name': f"{request.user.full_name or request.user.email}'s Farm",
            'farm_type': 'smallholder',
            'farm_size_category': '1_to_5',
            'primary_crop': 'maize',
            'farming_years': 1,  # Required field with default
            'region': 'center',  # Required field with default
            'division': '',
            'subdivision': '',
            'village_town': '',
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
    
    # Get maize varieties for step 1 (or any step where you want to show them)
    maize_varieties = MaizeVariety.objects.filter(is_active=True)
    
    context = {
        'total_steps': 7,
        'progress_percentage': farm_details.completion_percentage(),
        'farm_details': farm_details,
        'maize_varieties': maize_varieties,
        'current_time': datetime.now().strftime('%I:%M %p'),
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
        
        # Get or create farm details
        farm_details, created = FarmDetails.objects.get_or_create(user=request.user)
        
        # Update farm details based on step
        if step == 1:  # Basic farm information
            farm_details.farm_name = data.get('farmName')
            farm_details.farm_type = data.get('farmType')
            farm_details.farm_size_category = data.get('farmSizeCategory')
            farm_details.primary_crop = data.get('primaryCrop')
            
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
            farm_details.region = data.get('region')
            farm_details.division = data.get('division')
            farm_details.subdivision = data.get('subdivision')
            farm_details.village_town = data.get('villageTown')
            farm_details.gps_coordinates = data.get('gpsCoordinates')
            
        elif step == 3:  # Soil information
            farm_details.soil_type = data.get('soilType')
            farm_details.soil_fertility = data.get('soilFertility')
            farm_details.ph_level = data.get('soilPh')
            farm_details.soil_test_done = data.get('soilTestDone', False)
            
        elif step == 4:  # Water and irrigation
            farm_details.water_source = data.get('waterSource')
            farm_details.irrigation_method = data.get('irrigationMethod')
            farm_details.water_availability = data.get('waterAvailability')
            farm_details.irrigation_equipment = data.get('irrigationEquipment', '')
            
        elif step == 5:  # Equipment and resources
            farm_details.available_equipment = data.get('availableEquipment', [])
            farm_details.equipment_details = data.get('equipmentDetails', '')
            farm_details.labor_source = data.get('laborSource')
            
            # Convert labor_count to integer with default
            labor_count = data.get('laborCount', 1)
            try:
                farm_details.labor_count = int(labor_count) if labor_count else 1
            except (ValueError, TypeError):
                farm_details.labor_count = 1
            
        elif step == 6:  # Farming practices
            farm_details.experience_level = data.get('experienceLevel')
            farm_details.farming_methods = data.get('farmingMethods')
            farm_details.fertilizer_usage = data.get('fertilizerUsage', True)
            farm_details.pesticide_usage = data.get('pesticideUsage', True)
            farm_details.organic_farming = data.get('organicFarming', False)
            
        elif step == 7:  # Goals and challenges
            farm_details.farming_goals = data.get('farmingGoals')
            farm_details.main_challenges = data.get('mainChallenges')
            farm_details.expected_yield = data.get('expectedYield')
            farm_details.market_access = data.get('marketAccess')
            
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
            # Create new farm
            farm_details = FarmDetails.objects.create(user=request.user)
            
            # Clear the session flag
            del request.session['adding_new_farm']
        else:
            # Update existing farm that was created during onboarding
            farm_details = FarmDetails.objects.filter(user=request.user).first()
            if not farm_details:
                farm_details = FarmDetails.objects.create(user=request.user)
        
        # Update all fields from session data
        onboarding_data = request.session.get('onboarding_data', {})
        if onboarding_data:
            # Basic farm information
            farm_details.farm_name = onboarding_data.get('farmName', farm_details.farm_name)
            farm_details.farm_type = onboarding_data.get('farmType', farm_details.farm_type)
            farm_details.farm_size_category = onboarding_data.get('farmSizeCategory', farm_details.farm_size_category)
            farm_details.primary_crop = onboarding_data.get('primaryCrop', farm_details.primary_crop)
            
            # Handle farming_years conversion
            farming_years = onboarding_data.get('farmingYears', 1)
            try:
                farm_details.farming_years = int(farming_years) if farming_years else 1
            except (ValueError, TypeError):
                farm_details.farming_years = 1
            
            # Location information
            farm_details.region = onboarding_data.get('region', farm_details.region)
            farm_details.division = onboarding_data.get('division', farm_details.division)
            farm_details.subdivision = onboarding_data.get('subdivision', farm_details.subdivision)
            farm_details.village_town = onboarding_data.get('villageTown', farm_details.village_town)
            
            # Handle GPS coordinates
            gps_coords = onboarding_data.get('gpsCoordinates', {})
            if gps_coords and gps_coords.get('lat') and gps_coords.get('lng'):
                farm_details.gps_coordinates = f"{gps_coords['lat']}, {gps_coords['lng']}"
            
            # Soil information
            farm_details.soil_type = onboarding_data.get('soilType', farm_details.soil_type)
            farm_details.soil_fertility = onboarding_data.get('soilFertility', farm_details.soil_fertility)
            farm_details.ph_level = onboarding_data.get('soilPh', farm_details.ph_level)
            farm_details.soil_test_done = onboarding_data.get('soilTestDone', False)
            
            # Water and irrigation
            farm_details.water_source = onboarding_data.get('waterSource', farm_details.water_source)
            farm_details.irrigation_method = onboarding_data.get('irrigationMethod', farm_details.irrigation_method)
            farm_details.water_availability = onboarding_data.get('waterAvailability', farm_details.water_availability)
            farm_details.irrigation_equipment = onboarding_data.get('irrigationEquipment', '')
            
            # Equipment and resources
            farm_details.available_equipment = onboarding_data.get('availableEquipment', [])
            farm_details.equipment_details = onboarding_data.get('equipmentDetails', '')
            farm_details.labor_source = onboarding_data.get('laborSource', farm_details.labor_source)
            
            # Handle labor_count conversion
            labor_count = onboarding_data.get('laborCount', 1)
            try:
                farm_details.labor_count = int(labor_count) if labor_count else 1
            except (ValueError, TypeError):
                farm_details.labor_count = 1
            
            # Farming practices
            farm_details.experience_level = onboarding_data.get('experienceLevel', farm_details.experience_level)
            farm_details.farming_methods = onboarding_data.get('farmingMethods', farm_details.farming_methods)
            farm_details.fertilizer_usage = onboarding_data.get('fertilizerUsage', True)
            farm_details.pesticide_usage = onboarding_data.get('pesticideUsage', True)
            farm_details.organic_farming = onboarding_data.get('organicFarming', False)
            
            # Goals and challenges
            farm_details.farming_goals = onboarding_data.get('farmingGoals', '')
            farm_details.main_challenges = onboarding_data.get('mainChallenges', '')
            farm_details.expected_yield = onboarding_data.get('expectedYield', '')
            farm_details.market_access = onboarding_data.get('marketAccess', '')
            
            # Maize variety
            selected_variety = onboarding_data.get('selectedMaizeVariety')
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
