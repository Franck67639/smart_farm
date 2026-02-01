from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from smart_farm.services import geocoding_service
import json

@csrf_exempt
@require_GET
def reverse_geocode(request):
    """
    API endpoint for reverse geocoding
    Takes lat/lng parameters and returns address information
    """
    try:
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        
        if not lat or not lng:
            return JsonResponse({
                'success': False,
                'error': 'Missing lat or lng parameters'
            }, status=400)
        
        # Convert to float
        lat = float(lat)
        lng = float(lng)
        
        # Validate Cameroon bounds (approximately)
        if not (2.0 <= lat <= 13.0 and 8.0 <= lng <= 16.0):
            return JsonResponse({
                'success': False,
                'error': 'Coordinates outside Cameroon bounds'
            }, status=400)
        
        # Perform reverse geocoding
        result = geocoding_service.reverse_geocode(lat, lng)
        
        if result:
            response_data = {
                'success': True,
                'data': {
                    'village_town': result['village_town'],
                    'division': result['division'],
                    'subdivision': result['subdivision'],
                    'region': result['region'],
                    'display_name': result['display_name'],
                    'country': result['country']
                }
            }
            
            return JsonResponse(response_data)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Unable to geocode coordinates'
            }, status=404)
            
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid coordinate format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

@csrf_exempt
@require_GET
def geocode_address(request):
    """
    API endpoint for geocoding addresses
    Takes address parameter and returns coordinates
    """
    try:
        address = request.GET.get('address')
        
        if not address:
            return JsonResponse({
                'success': False,
                'error': 'Missing address parameter'
            }, status=400)
        
        # Perform geocoding
        result = geocoding_service.geocode_address(address)
        
        if result:
            lat, lng = result
            return JsonResponse({
                'success': True,
                'data': {
                    'lat': lat,
                    'lng': lng
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Unable to geocode address'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)
