#!/usr/bin/env python
"""
Debug script to check static file configuration
Run this in Render console to debug static file issues
"""

import os
import django
from django.conf import settings
from django.contrib.staticfiles.finders import find

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_farm.settings_render')
django.setup()

print("=== Static Files Debug ===")
print(f"STATIC_URL: {settings.STATIC_URL}")
print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
print(f"STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
print(f"STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")

print("\n=== Checking Hero Images ===")
hero_images = [
    'hero_images/hero0.avif',
    'hero_images/hero1.webp', 
    'hero_images/hero2.webp',
    'hero_images/hero3.png'
]

for image_path in hero_images:
    found_path = find(image_path)
    print(f"{image_path}: {'✓ FOUND' if found_path else '✗ NOT FOUND'}")
    if found_path:
        print(f"  -> {found_path}")

print(f"\n=== STATIC_ROOT Contents ===")
if os.path.exists(settings.STATIC_ROOT):
    for root, dirs, files in os.walk(settings.STATIC_ROOT):
        level = root.replace(settings.STATIC_ROOT, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
else:
    print("STATIC_ROOT does not exist!")

print("\n=== WhiteNoise Configuration ===")
print(f"WHITENOISE_USE_FINDERS: {getattr(settings, 'WHITENOISE_USE_FINDERS', 'Not set')}")
