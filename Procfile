web: gunicorn smart_farm.wsgi:application
release: python manage.py collectstatic --noinput --verbosity 2 && python manage.py migrate --verbosity 2
