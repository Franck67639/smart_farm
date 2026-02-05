"""
URL configuration for smart_farm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from . import views
from . import views_geocoding

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    
    # Non-internationalized URLs (admin, static, etc.)
]

# Internationalized URL patterns
urlpatterns += i18n_patterns(
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Landing Page
    path('', views.landing_view, name='landing'),
    
    # Main Application
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Farm Management
    path('farms/', views.farm_list_view, name='farm_list'),
    path('farm/<uuid:farm_id>/', views.farm_detail_view, name='farm_detail'),
    path('farm/switch/<uuid:farm_id>/', views.switch_farm, name='switch_farm'),
    path('farm/add/', views.add_new_farm, name='add_new_farm'),
    path('farm/delete/<uuid:farm_id>/', views.delete_farm, name='delete_farm'),
    path('farm/export/<uuid:farm_id>/csv/', views.export_farm_csv, name='export_farm_csv'),
    
    # Geocoding Services
    path('api/geocode/reverse/', views_geocoding.reverse_geocode, name='reverse_geocode'),
    path('api/geocode/address/', views_geocoding.geocode_address, name='geocode_address'),
    
    # Weather Services
    path('weather/', include('weather.urls')),
    
    # Onboarding Flow
    path('onboarding/', views.onboarding_step_view, name='onboarding'),
    path('onboarding/complete/', views.complete_onboarding_view, name='onboarding_complete'),
    
    # API Endpoints for HTMX
    path('weather/partial/', views.weather_partial_view, name='weather_partial'),
    path('onboarding/save-location/', views.save_onboarding_step_view, name='save_onboarding_step'),
    path('onboarding/save-step/', views.save_onboarding_step_view, name='save_onboarding_step'),
    path('api/set-farm/', views.set_farm_view, name='set_farm'),
)

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
