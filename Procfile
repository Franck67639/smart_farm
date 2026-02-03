web: gunicorn smart_farm.wsgi:application
release: python manage.py collectstatic --noinput && python manage.py migrate
