import requests
import logging
from django.conf import settings
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class GeocodingService:
    """Service for geocoding and reverse geocoding operations"""
    
    def __init__(self):
        self.nominatim_base_url = "https://nominatim.openstreetmap.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SmartFarm Cameroon/1.0 (geocoding@smartfarm.cm)'
        })
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[Dict]:
        """
        Convert coordinates to address information
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            Dictionary with address components or None if failed
        """
        try:
            url = f"{self.nominatim_base_url}/reverse"
            params = {
                'lat': lat,
                'lon': lng,
                'format': 'json',
                'addressdetails': 1,
                'countrycodes': 'cm',  # Limit to Cameroon
                'zoom': 13
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('error'):
                logger.warning(f"Geocoding error: {data['error']}")
                return None
            
            # Extract relevant address components
            address = data.get('address', {})
            address_components = {
                'display_name': data.get('display_name', ''),
                'village_town': self._extract_village_town(address),
                'division': self._extract_division(address),
                'subdivision': self._extract_subdivision(address),
                'region': self._extract_region(address),
                'country': address.get('country', ''),
                'raw_address': address
            }
            
            logger.info(f"Successfully reverse geocoded coordinates {lat}, {lng}")
            return address_components
            
        except requests.RequestException as e:
            logger.error(f"Network error during reverse geocoding: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during reverse geocoding: {e}")
            return None
    
    def _extract_village_town(self, address: Dict) -> str:
        """Extract village or town name from address components"""
        # Priority order for settlement names
        for key in ['village', 'town', 'city', 'municipality', 'suburb']:
            if address.get(key):
                return address[key]
        return ''
    
    def _extract_division(self, address: Dict) -> str:
        """Extract division/department name from address components"""
        # Priority order for administrative divisions
        for key in ['county', 'department', 'district']:
            if address.get(key):
                return address[key]
        return ''
    
    def _extract_region(self, address: Dict) -> str:
        """Extract region/state name from address components"""
        # Priority order for regions
        for key in ['state', 'region', 'province']:
            if address.get(key):
                region = address[key].lower()
                # Map common variations to form values
                region_mapping = {
                    'northwest': 'northwest',
                    'southwest': 'southwest', 
                    'west': 'west',
                    'littoral': 'littoral',
                    'centre': 'center',  # Note: OSM uses 'centre'
                    'center': 'center',
                    'east': 'east',
                    'adamawa': 'adamawa',
                    'far north': 'far_north',
                    'north': 'north',
                    'south': 'south'
                }
                return region_mapping.get(region, region)
        
        # If no explicit region, try to infer from division/county
        division = address.get('county', '').lower()
        if division:
            # Cameroon division to region mapping
            division_to_region = {
                # Northwest
                'mezam': 'northwest',
                'ngo-ketunjia': 'northwest',
                'momo': 'northwest',
                'bui': 'northwest',
                'donga-mantung': 'northwest',
                'menchum': 'northwest',
                'boyo': 'northwest',
                'fako': 'southwest',  # Actually Southwest
                'meme': 'southwest',
                'manyu': 'southwest',
                'lebialem': 'southwest',
                'ndian': 'southwest',
                'kupu-muanenguba': 'southwest',
                
                # West
                'menoua': 'west',
                'haut-nkam': 'west',
                'mifi': 'west',
                'ndé': 'west',
                'bamboutos': 'west',
                
                # Littoral
                'wouri': 'littoral',
                'sanaga-maritime': 'littoral',
                'moungo': 'littoral',
                'nyong-et-kéllé': 'littoral',
                'nyong-et-so\'o': 'littoral',
                
                # Center
                'mfoundi': 'center',
                'lefki': 'center',
                'haut-nyong': 'center',
                'nyong-et-mfoumou': 'center',
                'mbam-et-inoubou': 'center',
                'mbam-et-kim': 'center',
                
                # East
                'boumba-et-ngoko': 'east',
                'haut-nyong': 'east',
                'kadey': 'east',
                'lom-et-djerem': 'east',
                
                # Adamawa
                'djérem': 'adamawa',
                'faro-et-déo': 'adamawa',
                'maya-maya': 'adamawa',
                'mbéré': 'adamawa',
                'vina': 'adamawa',
                
                # North
                'bénoué': 'north',
                'faro': 'north',
                'maya-maya': 'north',  # Also in Adamawa
                'tcholliré': 'north',
                'touboro': 'north',
                
                # Far North
                'diamaré': 'far_north',
                'logone-et-chania': 'far_north',
                'maya-sava': 'far_north',
                'maya-danay': 'far_north',
                'sokolo': 'far_north',
                
                # South
                'mvilla': 'south',
                'njyan-et-mfoumou': 'south',
                'ocean': 'south',
                'vallée-du-ntem': 'south',
            }
            
            return division_to_region.get(division, '')
        
        return ''
    
    def _extract_subdivision(self, address: Dict) -> str:
        """Extract subdivision/district name from address components"""
        # Priority order for subdivisions
        for key in ['city_district', 'suburb', 'municipality', 'district']:
            if address.get(key):
                return address[key]
        # Fallback to city if no subdivision found
        if address.get('city'):
            return address['city']
        return ''
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to coordinates
        
        Args:
            address: Address string
            
        Returns:
            Tuple of (latitude, longitude) or None if failed
        """
        try:
            url = f"{self.nominatim_base_url}/search"
            params = {
                'q': f"{address}, Cameroon",
                'format': 'json',
                'countrycodes': 'cm',
                'limit': 1,
                'addressdetails': 1
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.warning(f"No results found for address: {address}")
                return None
            
            result = data[0]
            lat = float(result['lat'])
            lng = float(result['lon'])
            
            logger.info(f"Successfully geocoded address '{address}' to {lat}, {lng}")
            return (lat, lng)
            
        except requests.RequestException as e:
            logger.error(f"Network error during geocoding: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during geocoding: {e}")
            return None

# Singleton instance
geocoding_service = GeocodingService()
