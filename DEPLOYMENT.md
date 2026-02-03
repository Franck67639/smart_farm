# SmartFarm Production Deployment Guide

## Static Files Configuration

The 404 errors for hero images indicate that static files are not being served properly in production. Follow these steps:

### 1. Run Collect Static Files
```bash
# Clear and collect all static files
python manage.py collectstatic --noinput --clear
```

### 2. Web Server Configuration

#### For Apache:
Add this to your Apache configuration:
```apache
Alias /static /path/to/your/project/staticfiles
<Directory /path/to/your/project/staticfiles>
    Require all granted
</Directory>

Alias /media /path/to/your/project/media
<Directory /path/to/your/project/media>
    Require all granted
</Directory>
```

#### For Nginx:
Add this to your Nginx configuration:
```nginx
location /static/ {
    alias /path/to/your/project/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location /media/ {
    alias /path/to/your/project/media/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### 3. Environment Variables
Set these environment variables in production:
```bash
export DJANGO_SECRET_KEY='your-secure-secret-key-here'
export DEBUG=False
export ALLOWED_HOSTS='yourdomain.com,www.yourdomain.com'
```

### 4. Production Settings
Use the production settings file:
```bash
python manage.py runserver --settings=smart_farm.settings_production
```

Or update your WSGI configuration:
```python
# wsgi.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_farm.settings_production')
```

### 5. Verify Static Files
Check that files exist:
```bash
ls -la staticfiles/hero_images/
# Should show:
# hero0.avif
# hero1.webp
# hero2.webp
# hero3.png
```

### 6. Common Issues & Solutions

#### Issue: Static files return 404
**Solution**: Ensure your web server is configured to serve files from STATIC_ROOT

#### Issue: Permissions denied
**Solution**: Set proper permissions:
```bash
chmod -R 755 staticfiles/
```

#### Issue: CSS/JS not loading
**Solution**: Run collectstatic again and check web server logs

### 7. Production Checklist
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Set secure SECRET_KEY
- [ ] Run collectstatic
- [ ] Configure web server for static files
- [ ] Set proper file permissions
- [ ] Test all static assets load correctly

### 8. Hero Images Specific Fix
The hero images should be accessible at:
- `/static/hero_images/hero0.avif`
- `/static/hero_images/hero1.webp`
- `/static/hero_images/hero2.webp`
- `/static/hero_images/hero3.png`

Test these URLs directly in your browser to verify they load.

### 9. CDN Alternative (Optional)
For better performance, consider using a CDN:
```python
# settings.py
STATIC_URL = 'https://your-cdn.com/static/'
```

## Troubleshooting

### Check Django Settings
```python
python manage.py shell
>>> from django.conf import settings
>>> print(settings.STATIC_URL)
>>> print(settings.STATIC_ROOT)
```

### Check Web Server Logs
Look for errors related to static file serving in your web server logs.

### Verify Template Tags
Ensure templates use `{% static %}` tags correctly:
```html
<img src="{% static 'hero_images/hero0.avif' %}" alt="Hero Image">
```

Following these steps should resolve the 404 errors for your hero images in production.
