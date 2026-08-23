web: python manage.py collectstatic --noinput && python manage.py migrate && gunicorn mainproj.wsgi:application --bind 0.0.0.0:${PORT:-8000}
